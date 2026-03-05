"""
レース予想ロジック
機械学習モデルを使用してレース予想を生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from models.baseline import BaselineModel


class RacePredictor:
    """レース予想クラス"""

    def __init__(self, model_path: str):
        """
        Args:
            model_path: 学習済みモデルのパス
        """
        self.model = BaselineModel.load(model_path)

    def predict(self, race_data: Dict) -> Dict:
        """
        レース予想を実行

        Args:
            race_data: レース情報・出走馬情報

        Returns:
            予想結果（勝率・役割・買い目）
        """
        # 入力データをDataFrameに変換
        horses_df = self._prepare_input_data(race_data)

        # 予測実行
        win_probabilities = self.model.predict_proba(horses_df)[:, 1]

        # 予測結果をソート（勝率順）
        horses_df['win_probability'] = win_probabilities
        horses_df = horses_df.sort_values('win_probability', ascending=False).reset_index(drop=True)

        # 役割・印を割り当て
        predictions = self._assign_roles(horses_df)

        # 買い目生成
        betting_lines = self._generate_betting_lines(predictions)

        return {
            'predictions': predictions,
            'betting_lines': betting_lines
        }

    def _prepare_input_data(self, race_data: Dict) -> pd.DataFrame:
        """入力データを特徴量DataFrameに変換"""
        rows = []

        for horse in race_data['horses']:
            row = {
                # レース情報
                'distance': race_data['distance'],
                'surface_encoded': 1 if race_data['surface'] == '芝' else 0,
                'weather_encoded': self._encode_weather(race_data.get('weather', '晴')),
                'track_condition_encoded': self._encode_track_condition(
                    race_data.get('track_condition', '良')
                ),
                'horses_count': len(race_data['horses']),

                # 馬情報
                'number': horse['number'],
                'popularity': horse.get('popularity', 0),

                # 過去成績（ダミーデータ: 実際は履歴DBから取得）
                'past_races_count': 0,
                'past_win_rate': 0.0,
                'past_place_rate': 0.0,
                'past_avg_rank': 0.0,
                'last_race_rank': 0,
                'days_since_last_race': 0,

                # 騎手・調教師（ダミーデータ）
                'jockey_win_rate': 0.0,
                'jockey_place_rate': 0.0,
                'trainer_win_rate': 0.0,
                'trainer_place_rate': 0.0,

                # 適性（ダミーデータ）
                'distance_win_rate': 0.0,
                'surface_win_rate': 0.0,
                'venue_win_rate': 0.0,

                # メタ情報（予測には使わない）
                'name': horse['name']
            }

            rows.append(row)

        df = pd.DataFrame(rows)

        # モデルの特徴量カラムに合わせる
        for col in self.model.feature_cols:
            if col not in df.columns:
                df[col] = 0

        # 順序を揃える
        df = df[self.model.feature_cols + ['number', 'name']]

        return df

    def _encode_weather(self, weather: str) -> int:
        """天候エンコーディング"""
        weather_map = {'晴': 0, '曇': 1, '雨': 2, '小雨': 2, '雪': 3, '小雪': 3}
        return weather_map.get(weather, 0)

    def _encode_track_condition(self, condition: str) -> int:
        """馬場状態エンコーディング"""
        condition_map = {'良': 0, '稍重': 1, '重': 2, '不良': 3}
        return condition_map.get(condition, 0)

    def _assign_roles(self, df: pd.DataFrame) -> List[Dict]:
        """役割・印を割り当て"""
        predictions = []

        for rank, (idx, row) in enumerate(df.iterrows(), start=1):
            # 役割割り当て
            if rank == 1:
                role = '本命'
                mark = '◎'
            elif rank == 2:
                role = '対抗'
                mark = '○'
            elif rank == 3:
                role = '単穴'
                mark = '▲'
            elif rank <= 5:
                role = '連下'
                mark = '△'
            else:
                role = '抑え'
                mark = '-'

            predictions.append({
                'number': int(row['number']),
                'name': row['name'],
                'win_probability': float(row['win_probability']),
                'rank': rank,
                'role': role,
                'mark': mark
            })

        return predictions

    def _generate_betting_lines(self, predictions: List[Dict]) -> Dict[str, List[str]]:
        """買い目生成（馬単）"""
        # 上位5頭
        top5 = [p['number'] for p in predictions[:5]]

        # 本命・対抗
        honmei = top5[0]
        taikou = top5[1] if len(top5) > 1 else None

        # 相手（3-5位）
        aite = top5[2:5]

        betting_lines = {
            'umatan': []
        }

        # 本命軸
        if aite:
            aite_str = '.'.join(map(str, aite))
            betting_lines['umatan'].append(f"{honmei}-{aite_str}")

        # 対抗軸
        if taikou and aite:
            aite_str = '.'.join(map(str, aite))
            betting_lines['umatan'].append(f"{taikou}-{aite_str}")

        return betting_lines


if __name__ == '__main__':
    print("レース予想ロジックモジュール")
    print("使用方法:")
    print("  from src.api.predictor import RacePredictor")
    print("  predictor = RacePredictor(model_path='models/random_forest_model.pkl')")
    print("  result = predictor.predict(race_data)")
