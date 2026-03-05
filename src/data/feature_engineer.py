"""
特徴量エンジニアリングモジュール
過去成績などの高度な特徴量を生成
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List


class FeatureEngineer:
    """特徴量生成クラス"""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self, filename: str) -> pd.DataFrame:
        """前処理済みデータ読み込み"""
        filepath = self.input_dir / filename
        print(f"データ読み込み: {filepath}")
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        print(f"読み込み完了: {len(df)}行")
        return df

    def create_horse_past_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """馬の過去成績特徴量を生成"""
        print("馬の過去成績特徴量を生成中...")

        # 日付でソート
        df = df.sort_values('date').reset_index(drop=True)

        # 各馬の過去成績を計算
        features = []

        for name in df['name'].unique():
            horse_df = df[df['name'] == name].copy()

            for idx, row in horse_df.iterrows():
                # このレースより前のデータ
                past_races = horse_df[horse_df['date'] < row['date']]

                if len(past_races) == 0:
                    # 新馬の場合
                    feat = {
                        'past_races_count': 0,
                        'past_win_rate': 0.0,
                        'past_place_rate': 0.0,
                        'past_avg_rank': 0.0,
                        'last_race_rank': 0,
                        'days_since_last_race': 0
                    }
                else:
                    # 過去成績集計
                    wins = (past_races['rank'] == 1).sum()
                    places = (past_races['rank'] <= 3).sum()
                    total = len(past_races)

                    # 最終レースからの日数
                    last_race_date = past_races['date'].max()
                    days_since = (row['date'] - last_race_date).days

                    feat = {
                        'past_races_count': total,
                        'past_win_rate': wins / total if total > 0 else 0.0,
                        'past_place_rate': places / total if total > 0 else 0.0,
                        'past_avg_rank': past_races['rank'].mean(),
                        'last_race_rank': past_races.iloc[-1]['rank'],
                        'days_since_last_race': days_since
                    }

                features.append({
                    'index': idx,
                    **feat
                })

        # 特徴量をDataFrameに結合
        features_df = pd.DataFrame(features)
        df = df.merge(features_df, left_index=True, right_on='index', how='left')
        df = df.drop(columns=['index'])

        return df

    def create_jockey_trainer_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """騎手・調教師の統計特徴量を生成"""
        print("騎手・調教師の統計特徴量を生成中...")

        df = df.sort_values('date').reset_index(drop=True)

        # 騎手の勝率
        jockey_features = []
        for jockey in df['jockey'].unique():
            jockey_df = df[df['jockey'] == jockey]

            for idx, row in jockey_df.iterrows():
                past_races = jockey_df[jockey_df['date'] < row['date']]

                if len(past_races) == 0:
                    feat = {'jockey_win_rate': 0.0, 'jockey_place_rate': 0.0}
                else:
                    wins = (past_races['rank'] == 1).sum()
                    places = (past_races['rank'] <= 3).sum()
                    total = len(past_races)

                    feat = {
                        'jockey_win_rate': wins / total if total > 0 else 0.0,
                        'jockey_place_rate': places / total if total > 0 else 0.0
                    }

                jockey_features.append({'index': idx, **feat})

        jockey_features_df = pd.DataFrame(jockey_features)
        df = df.merge(jockey_features_df, left_index=True, right_on='index', how='left')
        df = df.drop(columns=['index'])

        # 調教師の勝率（同様のロジック）
        trainer_features = []
        for trainer in df['trainer'].unique():
            trainer_df = df[df['trainer'] == trainer]

            for idx, row in trainer_df.iterrows():
                past_races = trainer_df[trainer_df['date'] < row['date']]

                if len(past_races) == 0:
                    feat = {'trainer_win_rate': 0.0, 'trainer_place_rate': 0.0}
                else:
                    wins = (past_races['rank'] == 1).sum()
                    places = (past_races['rank'] <= 3).sum()
                    total = len(past_races)

                    feat = {
                        'trainer_win_rate': wins / total if total > 0 else 0.0,
                        'trainer_place_rate': places / total if total > 0 else 0.0
                    }

                trainer_features.append({'index': idx, **feat})

        trainer_features_df = pd.DataFrame(trainer_features)
        df = df.merge(trainer_features_df, left_index=True, right_on='index', how='left')
        df = df.drop(columns=['index'])

        return df

    def create_distance_surface_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """距離・馬場適性特徴量を生成"""
        print("距離・馬場適性特徴量を生成中...")

        df = df.sort_values('date').reset_index(drop=True)
        features = []

        for name in df['name'].unique():
            horse_df = df[df['name'] == name].copy()

            for idx, row in horse_df.iterrows():
                past_races = horse_df[horse_df['date'] < row['date']]

                if len(past_races) == 0:
                    feat = {
                        'distance_win_rate': 0.0,
                        'surface_win_rate': 0.0,
                        'venue_win_rate': 0.0
                    }
                else:
                    # 同距離の成績
                    same_distance = past_races[past_races['distance'] == row['distance']]
                    distance_wins = (same_distance['rank'] == 1).sum()
                    distance_total = len(same_distance)

                    # 同馬場の成績
                    same_surface = past_races[past_races['surface'] == row['surface']]
                    surface_wins = (same_surface['rank'] == 1).sum()
                    surface_total = len(same_surface)

                    # 同競馬場の成績
                    same_venue = past_races[past_races['venue'] == row['venue']]
                    venue_wins = (same_venue['rank'] == 1).sum()
                    venue_total = len(same_venue)

                    feat = {
                        'distance_win_rate': distance_wins / distance_total if distance_total > 0 else 0.0,
                        'surface_win_rate': surface_wins / surface_total if surface_total > 0 else 0.0,
                        'venue_win_rate': venue_wins / venue_total if venue_total > 0 else 0.0
                    }

                features.append({'index': idx, **feat})

        features_df = pd.DataFrame(features)
        df = df.merge(features_df, left_index=True, right_on='index', how='left')
        df = df.drop(columns=['index'])

        return df

    def save_data(self, df: pd.DataFrame, filename: str):
        """特徴量データを保存"""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"保存完了: {output_path}")

    def run(self, input_filename: str = 'all_results_processed.csv'):
        """特徴量生成を実行"""
        # データ読み込み
        df = self.load_data(input_filename)

        print(f"\n=== 特徴量生成開始 ===")
        print(f"元データ: {len(df)}行 × {len(df.columns)}列")

        # 馬の過去成績
        df = self.create_horse_past_performance(df)
        print(f"馬の過去成績追加後: {len(df.columns)}列")

        # 騎手・調教師の統計
        df = self.create_jockey_trainer_stats(df)
        print(f"騎手・調教師統計追加後: {len(df.columns)}列")

        # 距離・馬場適性
        df = self.create_distance_surface_stats(df)
        print(f"距離・馬場適性追加後: {len(df.columns)}列")

        # 保存
        output_filename = input_filename.replace('_processed.csv', '_features.csv')
        self.save_data(df, output_filename)

        print(f"\n=== 特徴量生成完了 ===")
        print(f"出力ファイル: {output_filename}")
        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")
        print(f"\n生成した特徴量:")
        new_cols = [
            'past_races_count', 'past_win_rate', 'past_place_rate',
            'past_avg_rank', 'last_race_rank', 'days_since_last_race',
            'jockey_win_rate', 'jockey_place_rate',
            'trainer_win_rate', 'trainer_place_rate',
            'distance_win_rate', 'surface_win_rate', 'venue_win_rate'
        ]
        for col in new_cols:
            if col in df.columns:
                print(f"  - {col}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='特徴量エンジニアリング')
    parser.add_argument(
        '--input',
        default='data/processed',
        help='入力ディレクトリ'
    )
    parser.add_argument(
        '--output',
        default='data/features',
        help='出力ディレクトリ'
    )
    parser.add_argument(
        '--file',
        default='all_results_processed.csv',
        help='入力ファイル名'
    )

    args = parser.parse_args()

    engineer = FeatureEngineer(
        input_dir=args.input,
        output_dir=args.output
    )

    engineer.run(input_filename=args.file)
