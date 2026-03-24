"""
レースデータ取得モジュール
keiba-data-sharedから予想データを読み込む（外部API経由）
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import httpx

# 会場コードサフィックス候補（ファイル名が YYYY-MM-DD-VENUE.json の場合）
VENUE_SUFFIXES = ['OOI', 'KAW', 'FUN', 'URA']


class RaceDataFetcher:
    """keiba-data-sharedからレースデータを取得（Netlify経由）"""

    def __init__(self, base_url: str = "https://keiba-data-shared.netlify.app/nankan/predictions"):
        self.base_url = base_url

    def _try_fetch_json(self, url: str, timeout: float = 5.0) -> Tuple[Optional[Dict], int]:
        """
        URLからJSONを安全に取得する。

        Returns:
            (data, status_code)
            - data: JSONデータ or None
            - status_code: HTTPステータスコード（例外時は0）
        """
        try:
            response = httpx.get(url, timeout=timeout)
            if response.status_code != 200:
                return None, response.status_code

            # Content-Type確認（HTMLを誤ってJSONとして扱わない）
            content_type = response.headers.get('content-type', '')
            if 'html' in content_type and 'json' not in content_type:
                print(f"  ⚠️  HTMLレスポンス検出（JSON期待）: {url}")
                return None, response.status_code

            return response.json(), response.status_code
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ⚠️  JSON解析エラー: {url} ({e})")
            return None, 0
        except httpx.TimeoutException:
            print(f"  ⚠️  タイムアウト: {url}")
            return None, 0
        except Exception as e:
            print(f"  ⚠️  取得エラー: {url} ({e})")
            return None, 0

    def _find_json_for_date(self, date_str: str, timeout: float = 5.0) -> Tuple[Optional[Dict], Optional[str]]:
        """
        指定日付のJSONファイルを探索する。
        YYYY-MM-DD.json → YYYY-MM-DD-VENUE.json の順に試行。

        Returns:
            (data, matched_url) or (None, None)
        """
        year, month = date_str.split('-')[0], date_str.split('-')[1]

        # 1. まず標準形式: YYYY-MM-DD.json
        url = f"{self.base_url}/{year}/{month}/{date_str}.json"
        data, status = self._try_fetch_json(url, timeout)
        if data:
            return data, url

        # 2. 会場サフィックス付き: YYYY-MM-DD-VENUE.json
        for venue in VENUE_SUFFIXES:
            url = f"{self.base_url}/{year}/{month}/{date_str}-{venue}.json"
            data, status = self._try_fetch_json(url, timeout)
            if data:
                return data, url

        return None, None

    def get_available_dates(self, days: int = 7) -> List[str]:
        """利用可能な日付リストを取得（今日から過去days日分を探索）"""
        dates = []
        today = datetime.now()

        print(f"📅 開催日探索開始: 基準日={today.strftime('%Y-%m-%d')}, 探索日数={days}")

        for i in range(days + 1):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            data, matched_url = self._find_json_for_date(date_str)
            if data:
                dates.append(date_str)
                print(f"  ✅ {date_str}: データあり ({matched_url})")
            else:
                print(f"  ❌ {date_str}: データなし")

        print(f"📅 探索完了: {len(dates)}件の開催日を発見 {dates}")
        return dates

    def get_races_by_date(self, date: str) -> Optional[Dict]:
        """指定日付のレース一覧を取得"""
        data, matched_url = self._find_json_for_date(date, timeout=10.0)
        if data:
            print(f"✅ レースデータ取得成功: {matched_url}")
        else:
            print(f"❌ レースデータなし: {date}")
        return data

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
