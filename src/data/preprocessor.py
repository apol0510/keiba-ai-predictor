"""
データ前処理モジュール
生データをクリーニング・変換
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


class KeibaDataPreprocessor:
    """競馬データ前処理クラス"""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self, filename: str) -> pd.DataFrame:
        """CSVデータ読み込み"""
        filepath = self.input_dir / filename
        print(f"データ読み込み: {filepath}")
        df = pd.read_csv(filepath)
        print(f"読み込み完了: {len(df)}行 × {len(df.columns)}列")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """データクリーニング"""
        print("データクリーニング中...")

        # 元の行数
        original_rows = len(df)

        # 必須カラムの欠損値削除
        required_cols = ['date', 'venue', 'race_number', 'rank', 'number']
        df = df.dropna(subset=required_cols)

        # 日付型に変換
        df['date'] = pd.to_datetime(df['date'])

        # 数値型に変換
        numeric_cols = ['distance', 'rank', 'number', 'popularity', 'horses_count']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # タイム文字列を秒数に変換（例: "2:28.0" → 148.0秒）
        if 'time' in df.columns:
            df['time_seconds'] = df['time'].apply(self._time_to_seconds)

        # 上がり3Fを数値化（例: "39.3" → 39.3）
        if 'last_furlong' in df.columns:
            df['last_furlong_seconds'] = pd.to_numeric(
                df['last_furlong'],
                errors='coerce'
            )

        # 欠損値補完
        df['weather'] = df['weather'].fillna('晴')
        df['track_condition'] = df['track_condition'].fillna('良')

        print(f"クリーニング完了: {original_rows}行 → {len(df)}行")

        return df

    def _time_to_seconds(self, time_str: str) -> Optional[float]:
        """タイム文字列を秒数に変換"""
        if pd.isna(time_str):
            return None

        try:
            parts = str(time_str).split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return None

    def add_categorical_encoding(self, df: pd.DataFrame) -> pd.DataFrame:
        """カテゴリカル変数をエンコーディング"""
        print("カテゴリカル変数エンコーディング中...")

        # 馬場種別（ダート=0, 芝=1）
        if 'surface' in df.columns:
            df['surface_encoded'] = (df['surface'] == '芝').astype(int)

        # 天候（晴=0, 曇=1, 雨=2, 雪=3）
        weather_map = {'晴': 0, '曇': 1, '雨': 2, '小雨': 2, '雪': 3, '小雪': 3}
        if 'weather' in df.columns:
            df['weather_encoded'] = df['weather'].map(weather_map).fillna(0)

        # 馬場状態（良=0, 稍重=1, 重=2, 不良=3）
        condition_map = {'良': 0, '稍重': 1, '重': 2, '不良': 3}
        if 'track_condition' in df.columns:
            df['track_condition_encoded'] = df['track_condition'].map(condition_map).fillna(0)

        # 競馬場（ワンホットエンコーディングは後で実施）
        # 騎手・調教師も後で実施

        return df

    def save_data(self, df: pd.DataFrame, filename: str):
        """前処理済みデータを保存"""
        output_path = self.output_dir / filename
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"保存完了: {output_path}")

    def run(self, input_filename: str = 'all_results.csv'):
        """前処理を実行"""
        # データ読み込み
        df = self.load_data(input_filename)

        # クリーニング
        df = self.clean_data(df)

        # エンコーディング
        df = self.add_categorical_encoding(df)

        # 保存
        output_filename = input_filename.replace('.csv', '_processed.csv')
        self.save_data(df, output_filename)

        print(f"\n=== 前処理完了 ===")
        print(f"出力ファイル: {output_filename}")
        print(f"行数: {len(df)}")
        print(f"列数: {len(df.columns)}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='データ前処理')
    parser.add_argument(
        '--input',
        default='data/raw',
        help='入力ディレクトリ'
    )
    parser.add_argument(
        '--output',
        default='data/processed',
        help='出力ディレクトリ'
    )
    parser.add_argument(
        '--file',
        default='all_results.csv',
        help='入力ファイル名'
    )

    args = parser.parse_args()

    preprocessor = KeibaDataPreprocessor(
        input_dir=args.input,
        output_dir=args.output
    )

    preprocessor.run(input_filename=args.file)
