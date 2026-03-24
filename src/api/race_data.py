"""
レースデータ取得モジュール
keiba-data-sharedから予想データを読み込む（外部API経由）
"""

import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import httpx


class RaceDataFetcher:
    """keiba-data-sharedからレースデータを取得（Netlify経由）"""

    def __init__(self, base_url: str = "https://keiba-data-shared.netlify.app/nankan/predictions"):
        self.base_url = base_url

    def get_available_dates(self, days: int = 7) -> List[str]:
        """利用可能な日付リストを取得（今日から過去days日分を探索）"""
        dates = []
        today = datetime.now()

        for i in range(days + 1):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            year, month = date.year, date.strftime('%m')

            # 外部APIからファイル存在確認
            url = f"{self.base_url}/{year}/{month}/{date_str}.json"

            try:
                response = httpx.get(url, timeout=5.0)
                if response.status_code == 200:
                    dates.append(date_str)
            except Exception:
                pass

        return dates

    def get_races_by_date(self, date: str) -> Optional[Dict]:
        """指定日付のレース一覧を取得"""
        try:
            # 外部APIからデータ取得
            year, month = date.split('-')[0], date.split('-')[1]
            url = f"{self.base_url}/{year}/{month}/{date}.json"

            response = httpx.get(url, timeout=10.0)

            if response.status_code != 200:
                return None

            data = response.json()
            return data

        except Exception as e:
            print(f"Error loading race data: {e}")
            return None

    def get_race_detail(self, date: str, race_number: int) -> Optional[Dict]:
        """指定レースの詳細情報を取得"""
        races_data = self.get_races_by_date(date)

        if not races_data or 'races' not in races_data:
            return None

        for race in races_data['races']:
            race_num = race.get('raceInfo', {}).get('raceNumber', '')
            # "1R" -> 1 に変換
            race_num_int = int(race_num.replace('R', ''))

            if race_num_int == race_number:
                return race

        return None
