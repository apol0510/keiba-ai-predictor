"""
データ収集モジュール
keiba-data-sharedリポジトリからレース結果データを収集
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class KeibaDataCollector:
    """競馬データ収集クラス"""

    def __init__(self, data_shared_path: str, output_dir: str):
        """
        Args:
            data_shared_path: keiba-data-sharedのローカルパス
            output_dir: 出力先ディレクトリ
        """
        self.data_shared_path = Path(data_shared_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_nankan_results(self) -> pd.DataFrame:
        """南関競馬の結果データを収集"""
        print("南関競馬結果データを収集中...")

        results_dir = self.data_shared_path / "nankan" / "results"
        all_races = []

        # 年別・月別にデータを探索
        for year_dir in sorted(results_dir.glob("*")):
            if not year_dir.is_dir():
                continue

            for month_dir in sorted(year_dir.glob("*")):
                if not month_dir.is_dir():
                    continue

                # 各日付のJSONファイルを読み込み
                for json_file in sorted(month_dir.glob("*.json")):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # データ構造チェック
                        if isinstance(data, dict):
                            # 通常フォーマット
                            date = data.get('date')
                            venue = data.get('venue')
                            venue_code = data.get('venueCode')
                            races = data.get('races', [])
                        elif isinstance(data, list):
                            # リスト形式（古い形式の可能性）
                            continue
                        else:
                            continue

                        # 各レースをフラット化
                        for race in races:
                            race_data = self._flatten_race_results(
                                date=date,
                                venue=venue,
                                venue_code=venue_code,
                                race=race
                            )
                            all_races.extend(race_data)

                    except Exception as e:
                        print(f"エラー: {json_file} - {e}")
                        continue

        df = pd.DataFrame(all_races)
        print(f"収集完了: {len(df)}レース×馬データ")

        return df

    def collect_jra_results(self) -> pd.DataFrame:
        """中央競馬（JRA）の結果データを収集"""
        print("中央競馬結果データを収集中...")

        results_dir = self.data_shared_path / "jra" / "results"
        all_races = []

        # 南関と同じロジック
        for year_dir in sorted(results_dir.glob("*")):
            if not year_dir.is_dir():
                continue

            for month_dir in sorted(year_dir.glob("*")):
                if not month_dir.is_dir():
                    continue

                for json_file in sorted(month_dir.glob("*.json")):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # データ構造チェック
                        if isinstance(data, dict):
                            date = data.get('date')
                            venue = data.get('venue', '')
                            venue_code = data.get('venueCode', '')
                            races = data.get('races', [])
                        elif isinstance(data, list):
                            continue
                        else:
                            continue

                        for race in races:
                            race_data = self._flatten_race_results(
                                date=date,
                                venue=venue,
                                venue_code=venue_code,
                                race=race
                            )
                            all_races.extend(race_data)

                    except Exception as e:
                        print(f"エラー: {json_file} - {e}")
                        continue

        df = pd.DataFrame(all_races)
        print(f"収集完了: {len(df)}レース×馬データ")

        return df

    def _flatten_race_results(
        self,
        date: str,
        venue: str,
        venue_code: str,
        race: Dict
    ) -> List[Dict]:
        """レース結果をフラット化（1行=1頭）"""
        race_data = []

        race_number = race.get('raceNumber')
        race_name = race.get('raceName', '')
        distance = race.get('distance', 0)
        surface = race.get('surface', '')
        track = race.get('track', '')
        horses_count = race.get('horses', 0)
        weather = race.get('weather', '')
        track_condition = race.get('trackCondition', '')

        # 配当情報
        payouts = race.get('payouts', {})

        # 単勝配当（リスト形式の場合は最初の要素）
        tansho = payouts.get('tansho', [])
        if isinstance(tansho, list) and len(tansho) > 0:
            tansho_payout = tansho[0].get('payout', 0)
        elif isinstance(tansho, dict):
            tansho_payout = tansho.get('payout', 0)
        else:
            tansho_payout = 0

        # 馬単配当（リスト形式の場合は最初の要素）
        umatan = payouts.get('umatan', [])
        if isinstance(umatan, list) and len(umatan) > 0:
            umatan_payout = umatan[0].get('payout', 0)
        elif isinstance(umatan, dict):
            umatan_payout = umatan.get('payout', 0)
        else:
            umatan_payout = 0

        # 各着順の馬データ
        for result in race.get('results', []):
            horse_data = {
                # レース情報
                'date': date,
                'venue': venue,
                'venue_code': venue_code,
                'race_number': race_number,
                'race_name': race_name,
                'distance': distance,
                'surface': surface,
                'track': track,
                'horses_count': horses_count,
                'weather': weather,
                'track_condition': track_condition,

                # 馬情報
                'rank': result.get('rank'),
                'bracket': result.get('bracket'),
                'number': result.get('number'),
                'name': result.get('name', ''),
                'jockey': result.get('jockey', ''),
                'trainer': result.get('trainer', ''),
                'time': result.get('time', ''),
                'margin': result.get('margin', ''),
                'last_furlong': result.get('lastFurlong', ''),
                'popularity': result.get('popularity'),

                # 配当情報
                'tansho_payout': tansho_payout,
                'umatan_payout': umatan_payout,

                # 目的変数（1着なら1、それ以外0）
                'is_winner': 1 if result.get('rank') == 1 else 0
            }

            race_data.append(horse_data)

        return race_data

    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """DataFrameをCSV保存"""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"保存完了: {output_path}")

    def run(self):
        """データ収集を実行"""
        # 南関競馬
        nankan_df = self.collect_nankan_results()
        if not nankan_df.empty:
            self.save_to_csv(nankan_df, 'nankan_results.csv')

        # 中央競馬
        jra_df = self.collect_jra_results()
        if not jra_df.empty:
            self.save_to_csv(jra_df, 'jra_results.csv')

        # 統合データ
        if not nankan_df.empty or not jra_df.empty:
            combined_df = pd.concat([nankan_df, jra_df], ignore_index=True)
            self.save_to_csv(combined_df, 'all_results.csv')

            print(f"\n=== データ収集サマリー ===")
            print(f"南関競馬: {len(nankan_df)}行")
            print(f"中央競馬: {len(jra_df)}行")
            print(f"合計: {len(combined_df)}行")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='競馬データ収集')
    parser.add_argument(
        '--source',
        default='/Users/apolon/Projects/keiba-data-shared',
        help='keiba-data-sharedのパス'
    )
    parser.add_argument(
        '--output',
        default='data/raw',
        help='出力先ディレクトリ'
    )

    args = parser.parse_args()

    collector = KeibaDataCollector(
        data_shared_path=args.source,
        output_dir=args.output
    )

    collector.run()
