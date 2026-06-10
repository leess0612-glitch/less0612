import json
import requests
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / 'config.json'


def _load_api_key():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)['holiday_api_key']


def is_holiday(check_date: date = None) -> bool:
    if check_date is None:
        check_date = date.today()

    # 주말
    if check_date.weekday() >= 5:
        return True

    # 공휴일 API
    api_key = _load_api_key()
    url = 'https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo'
    params = {
        'ServiceKey': api_key,
        'solYear': check_date.year,
        'solMonth': f'{check_date.month:02d}',
        'numOfRows': 50,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        root = ET.fromstring(resp.content)
        for item in root.findall('.//item'):
            locdate = item.findtext('locdate')
            if locdate == check_date.strftime('%Y%m%d'):
                name = item.findtext('dateName', '')
                print(f"  오늘은 공휴일({name}) - 게시 생략")
                return True
    except Exception as e:
        print(f"  공휴일 API 오류: {e} - 공휴일 아닌 것으로 처리")

    return False
