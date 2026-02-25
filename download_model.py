import os
import urllib.request

url   = 'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx'
dest  = os.path.join(os.path.expanduser('~'), '.u2net', 'u2netp.onnx')

os.makedirs(os.path.dirname(dest), exist_ok=True)

if os.path.exists(dest):
    print(f'이미 존재함: {dest}')
else:
    print(f'다운로드 시작: {url}')
    print('잠시 기다려주세요...')

    def progress(count, block, total):
        pct = min(100, int(count * block / total * 100))
        print(f'\r진행: {pct}%', end='', flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print(f'\n완료: {dest}')

input('\n아무 키나 누르면 닫힙니다...')
