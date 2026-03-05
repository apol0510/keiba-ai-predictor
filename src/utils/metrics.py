"""
評価指標モジュール
的中率・回収率などの競馬特有の評価指標を計算
"""

import pandas as pd
import numpy as np
from typing import Dict


def calculate_race_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    レース単位の評価指標を計算

    Args:
        df: 予測結果を含むDataFrame
            - 'predicted_proba': 予測確率
            - 'rank': 実際の着順
            - 'date', 'venue', 'race_number': レース識別

    Returns:
        評価指標の辞書
    """
    metrics = {}

    # レースごとにグループ化
    races = df.groupby(['date', 'venue', 'race_number'])

    total_races = len(races)
    honmei_hit = 0  # 本命（予測確率最高）的中数
    top3_hit = 0    # TOP3に1着が入った数

    all_winner_proba = []
    all_loser_proba = []

    for (date, venue, race_num), race_df in races:
        # 予測確率が最も高い馬（本命）
        honmei_idx = race_df['predicted_proba'].idxmax()
        honmei_rank = race_df.loc[honmei_idx, 'rank']

        if honmei_rank == 1:
            honmei_hit += 1

        # TOP3予測
        top3_idx = race_df.nlargest(3, 'predicted_proba').index
        top3_ranks = race_df.loc[top3_idx, 'rank'].values

        if 1 in top3_ranks:
            top3_hit += 1

        # 1着馬の予測確率
        winner_df = race_df[race_df['rank'] == 1]
        if len(winner_df) > 0:
            all_winner_proba.append(winner_df['predicted_proba'].values[0])

        # 敗北馬の予測確率
        loser_df = race_df[race_df['rank'] != 1]
        if len(loser_df) > 0:
            all_loser_proba.extend(loser_df['predicted_proba'].values)

    # 的中率
    metrics['honmei_hit_rate'] = honmei_hit / total_races if total_races > 0 else 0
    metrics['top3_hit_rate'] = top3_hit / total_races if total_races > 0 else 0

    # 平均予測確率
    metrics['avg_winner_proba'] = np.mean(all_winner_proba) if all_winner_proba else 0
    metrics['avg_loser_proba'] = np.mean(all_loser_proba) if all_loser_proba else 0

    # 確率の分離度（高いほど良い）
    metrics['proba_separation'] = (
        metrics['avg_winner_proba'] - metrics['avg_loser_proba']
    )

    return metrics


def calculate_recovery_rate(
    df: pd.DataFrame,
    bet_strategy: str = 'honmei'
) -> Dict[str, float]:
    """
    回収率を計算

    Args:
        df: 予測結果 + 配当情報を含むDataFrame
        bet_strategy: 'honmei' (本命単勝) or 'umatan' (馬単)

    Returns:
        回収率の辞書
    """
    races = df.groupby(['date', 'venue', 'race_number'])

    total_bet = 0
    total_payout = 0

    for (date, venue, race_num), race_df in races:
        # 本命（予測確率最高）
        honmei_idx = race_df['predicted_proba'].idxmax()
        honmei_row = race_df.loc[honmei_idx]

        if bet_strategy == 'honmei':
            # 単勝100円
            total_bet += 100

            # 的中判定
            if honmei_row['rank'] == 1:
                # 配当取得
                payout = honmei_row.get('tansho_payout', 0)
                total_payout += payout

    recovery_rate = (total_payout / total_bet * 100) if total_bet > 0 else 0

    return {
        'total_bet': total_bet,
        'total_payout': total_payout,
        'recovery_rate': recovery_rate
    }


if __name__ == '__main__':
    print("評価指標モジュール")
    print("使用方法:")
    print("  from src.utils.metrics import calculate_race_metrics")
    print("  metrics = calculate_race_metrics(df)")
    print("  print(metrics['honmei_hit_rate'])")
