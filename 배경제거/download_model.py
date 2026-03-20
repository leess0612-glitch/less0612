import os
import urllib.request

models = [
    ('u2net.onnx',  'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx',  '176MB - 고성능'),
    ('u2netp.onnx', 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx', '4.7MB - 경량'),
]

dest_dir = os.path.join(os.path.expanduser('~'), '.u2net')
os.makedirs(dest_dir, exist_ok=True)

for fname, url, desc in models:
    dest = os.path.join(dest_dir, fname)
    if os.path.exists(dest):
        print(f'[이미 있음] {fname} ({desc})')
        continue

    print(f'\n[다운로드] {fname} ({desc})')
    print(f'URL: {url}')

    def progress(count, block, total):
        pct = min(100, int(count * block / total * 100))
        done = int(pct / 2)
        bar = '#' * done + '-' * (50 - done)
        print(f'\r[{bar}] {pct}%', end='', flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print(f'\n완료: {dest}')

print('\n--- 모든 모델 준비 완료 ---')
input('\n아무 키나 누르면 닫힙니다...')
