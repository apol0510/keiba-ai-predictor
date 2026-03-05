"""
モデル学習スクリプト
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
import sys

# src/ を import パスに追加
sys.path.append(str(Path(__file__).parent.parent))

from models.baseline import BaselineModel
from utils.metrics import calculate_race_metrics


def load_data(data_path: str) -> pd.DataFrame:
    """特徴量データ読み込み"""
    print(f"データ読み込み: {data_path}")
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"読み込み完了: {len(df)}行")
    return df


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.1
) -> tuple:
    """データ分割（訓練/検証/テスト）"""
    print("\nデータ分割中...")

    # 日付順にソート
    df = df.sort_values('date').reset_index(drop=True)

    # 時系列分割（未来のデータで評価）
    total_rows = len(df)
    test_rows = int(total_rows * test_size)
    val_rows = int(total_rows * val_size)
    train_rows = total_rows - test_rows - val_rows

    train_df = df.iloc[:train_rows].copy()
    val_df = df.iloc[train_rows:train_rows+val_rows].copy()
    test_df = df.iloc[train_rows+val_rows:].copy()

    print(f"訓練データ: {len(train_df)}行 ({train_df['date'].min()} 〜 {train_df['date'].max()})")
    print(f"検証データ: {len(val_df)}行 ({val_df['date'].min()} 〜 {val_df['date'].max()})")
    print(f"テストデータ: {len(test_df)}行 ({test_df['date'].min()} 〜 {test_df['date'].max()})")

    return train_df, val_df, test_df


def train_model(
    model_type: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    output_dir: str
):
    """モデル学習"""
    print(f"\n=== {model_type.upper()} モデル学習 ===")

    # モデル初期化
    model = BaselineModel(model_type=model_type)

    # データ準備
    X_train, y_train = model.prepare_data(train_df)
    X_val, y_val = model.prepare_data(val_df)

    # 学習
    model.train(X_train, y_train, normalize=True)

    # 検証データで評価
    print("\n検証データで評価...")
    val_proba = model.predict_proba(X_val)[:, 1]  # 1着確率
    val_df_copy = val_df.copy()
    val_df_copy['predicted_proba'] = val_proba

    # レース別に予測
    race_metrics = calculate_race_metrics(val_df_copy)

    print(f"\n=== 検証データ評価結果 ===")
    print(f"的中率（本命）: {race_metrics['honmei_hit_rate']*100:.2f}%")
    print(f"的中率（TOP3）: {race_metrics['top3_hit_rate']*100:.2f}%")
    print(f"平均予測確率（1着馬）: {race_metrics['avg_winner_proba']:.3f}")
    print(f"平均予測確率（敗北馬）: {race_metrics['avg_loser_proba']:.3f}")

    # 特徴量重要度
    importance_df = model.get_feature_importance()
    if importance_df is not None:
        print(f"\n=== 特徴量重要度 TOP10 ===")
        print(importance_df.head(10).to_string(index=False))

    # モデル保存
    output_path = Path(output_dir) / f"{model_type}_model.pkl"
    model.save(output_path)

    return model


def main():
    import argparse

    parser = argparse.ArgumentParser(description='モデル学習')
    parser.add_argument(
        '--data',
        default='data/features/all_results_features.csv',
        help='特徴量データパス'
    )
    parser.add_argument(
        '--model',
        default='random_forest',
        choices=['logistic', 'random_forest', 'xgboost', 'lightgbm'],
        help='モデルタイプ'
    )
    parser.add_argument(
        '--output',
        default='models',
        help='モデル保存ディレクトリ'
    )

    args = parser.parse_args()

    # データ読み込み
    df = load_data(args.data)

    # データ分割
    train_df, val_df, test_df = split_data(df)

    # モデル学習
    model = train_model(
        model_type=args.model,
        train_df=train_df,
        val_df=val_df,
        output_dir=args.output
    )

    # テストデータ保存（評価用）
    test_output_path = Path(args.output) / 'test_data.csv'
    test_df.to_csv(test_output_path, index=False, encoding='utf-8-sig')
    print(f"\nテストデータ保存: {test_output_path}")

    print("\n=== 学習完了 ===")


if __name__ == '__main__':
    main()
