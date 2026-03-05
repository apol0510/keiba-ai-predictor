"""
レースデータ取得モジュール
keiba-data-sharedから予想データを読み込む
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class RaceDataFetcher:
    """keiba-data-sharedからレースデータを取得"""

    def __init__(self, data_dir: str = "../keiba-data-shared/dist/nankan/predictions"):
        self.data_dir = Path(data_dir)

    def get_available_dates(self, days: int = 7) -> List[str]:
        """利用可能な日付リストを取得（今日から指定日数分）"""
        dates = []
        today = datetime.now()

        for i in range(days):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            # ファイルが存在するかチェック
            year, month = date.year, date.strftime('%m')
            file_path = self.data_dir / str(year) / month / f"{date_str}.json"

            if file_path.exists():
                dates.append(date_str)

        return dates

    def get_races_by_date(self, date: str) -> Optional[Dict]:
        """指定日付のレース一覧を取得"""
        try:
            # ファイルパス生成
            year, month = date.split('-')[0], date.split('-')[1]
            file_path = self.data_dir / year / month / f"{date}.json"

            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

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
