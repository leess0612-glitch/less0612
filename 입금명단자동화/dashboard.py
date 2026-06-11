import json
import subprocess
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / 'config.json'
LOG_PATH = BASE_DIR / 'run_log.json'
COOKIE_PATH = BASE_DIR / 'naver_cookies.json'
PYTHON = sys.executable
TASK_NAME = '입금명단자동화'

_running_proc = None


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=4)


def get_scheduler_info():
    try:
        ps = f'''
$task = Get-ScheduledTask -TaskName "{TASK_NAME}" -ErrorAction Stop
$info = Get-ScheduledTaskInfo -TaskName "{TASK_NAME}"
$next = if ($info.NextRunTime) {{ $info.NextRunTime.ToString("yyyy-MM-dd HH:mm") }} else {{ "" }}
$last = if ($info.LastRunTime -and $info.LastRunTime.Year -gt 2000) {{ $info.LastRunTime.ToString("yyyy-MM-dd HH:mm") }} else {{ "" }}
Write-Output "$($task.State)|$next|$last"
'''
        r = subprocess.run(
            ['powershell', '-NonInteractive', '-Command', ps],
            capture_output=True, encoding='utf-8', errors='replace', timeout=10
        )
        line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''
        parts = line.split('|')
        state = parts[0].strip() if len(parts) > 0 else 'Unknown'
        next_run = parts[1].strip() if len(parts) > 1 else '-'
        last_run = parts[2].strip() if len(parts) > 2 else '-'
        enabled = state in ('Ready', 'Running')
        return {'enabled': enabled, 'state': state, 'next_run': next_run or '-', 'last_run': last_run or '-'}
    except Exception as e:
        return {'enabled': False, 'state': 'Error', 'next_run': '-', 'last_run': '-', 'error': str(e)}


def get_cookie_info():
    if not COOKIE_PATH.exists():
        return {'valid': False, 'label': '쿠키 없음 — 로그인 필요', 'modified': None}
    mtime = datetime.fromtimestamp(COOKIE_PATH.stat().st_mtime)
    age = (datetime.now() - mtime).days
    valid = age <= 25
    label = f'{age}일 전 갱신' + ('' if valid else ' — 만료 가능')
    return {'valid': valid, 'label': label, 'modified': mtime.strftime('%Y-%m-%d %H:%M')}


# ── 라우트 ───────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'dashboard.html')


@app.route('/api/status')
def api_status():
    logs = []
    if LOG_PATH.exists():
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    return jsonify({
        'scheduler': get_scheduler_info(),
        'cookie': get_cookie_info(),
        'last_run': logs[-1] if logs else None,
        'total_runs': len(logs),
        'pending_posts': sum(1 for e in logs if e.get('image_file') and not e.get('cafe_posted')),
    })


@app.route('/api/logs')
def api_logs():
    if not LOG_PATH.exists():
        return jsonify([])
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


@app.route('/api/config', methods=['GET'])
def api_config_get():
    return jsonify(load_config())


@app.route('/api/config', methods=['POST'])
def api_config_save():
    data = request.json
    cfg = load_config()
    changed_hour = False
    for key in ('post_hour', 'backup_min', 'backup_max', 'target_date'):
        if key not in data:
            continue
        val = data[key]
        if key == 'target_date':
            val = (val or '').strip() or None
        else:
            try:
                val = int(val)
            except (TypeError, ValueError):
                continue
        if key == 'post_hour' and cfg.get(key) != val:
            changed_hour = True
        cfg[key] = val
    save_config(cfg)
    if changed_hour:
        h = int(cfg['post_hour'])
        ps = (
            f'$t=New-ScheduledTaskTrigger -Daily -At "{h:02d}:00";'
            f'Set-ScheduledTask -TaskName "{TASK_NAME}" -Trigger $t'
        )
        subprocess.run(['powershell', '-NonInteractive', '-Command', ps], capture_output=True, timeout=10)
    return jsonify({'ok': True})


@app.route('/api/scheduler/toggle', methods=['POST'])
def api_scheduler_toggle():
    info = get_scheduler_info()
    action = '/disable' if info['enabled'] else '/enable'
    subprocess.run(['schtasks', '/change', '/tn', TASK_NAME, action], capture_output=True)
    return jsonify({'enabled': not info['enabled']})


@app.route('/api/scheduler/skip-today', methods=['POST'])
def api_skip_today():
    cfg = load_config()
    h = int(cfg.get('post_hour', 20))
    tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    ps = (
        f'$t=New-ScheduledTaskTrigger -Daily -At "{h:02d}:00";'
        f'$t.StartBoundary="{tomorrow}T{h:02d}:00:00";'
        f'Set-ScheduledTask -TaskName "{TASK_NAME}" -Trigger $t'
    )
    subprocess.run(['powershell', '-NonInteractive', '-Command', ps], capture_output=True, timeout=10)
    return jsonify({'ok': True})


@app.route('/api/run', methods=['POST'])
def api_run():
    global _running_proc
    if _running_proc and _running_proc.poll() is None:
        return jsonify({'ok': False, 'msg': '이미 실행 중입니다.'})
    _running_proc = subprocess.Popen(
        [PYTHON, str(BASE_DIR / 'main.py')],
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    return jsonify({'ok': True, 'pid': _running_proc.pid})


@app.route('/api/run/status')
def api_run_status():
    global _running_proc
    if _running_proc is None:
        return jsonify({'running': False})
    if _running_proc.poll() is None:
        return jsonify({'running': True, 'pid': _running_proc.pid})
    return jsonify({'running': False, 'returncode': _running_proc.returncode})


@app.route('/api/refresh-login', methods=['POST'])
def api_refresh_login():
    subprocess.Popen(
        [PYTHON, str(BASE_DIR / 'main.py'), '--refresh-login'],
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    return jsonify({'ok': True})


@app.route('/api/post-pending', methods=['POST'])
def api_post_pending():
    global _running_proc
    if _running_proc and _running_proc.poll() is None:
        return jsonify({'ok': False, 'msg': '이미 실행 중입니다.'})
    _running_proc = subprocess.Popen(
        [PYTHON, str(BASE_DIR / 'main.py'), '--post'],
        cwd=str(BASE_DIR),
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    return jsonify({'ok': True, 'pid': _running_proc.pid})


if __name__ == '__main__':
    def _open():
        import time
        time.sleep(1.2)
        webbrowser.open('http://localhost:5000')

    threading.Thread(target=_open, daemon=True).start()
    print('대시보드 시작: http://localhost:5000')
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
