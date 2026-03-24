"""
予想データ取得スクリプト
API から本日の予想データを取得
"""

import httpx
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 会場コードサフィックス候補
VENUE_SUFFIXES = ['OOI', 'KAW', 'FUN', 'URA']


def _try_fetch_json(client: httpx.Client, url: str) -> Optional[Dict]:
    """URLからJSONを安全に取得（HTMLレスポンスを除外）"""
    try:
        response = client.get(url)
        if response.status_code != 200:
            return None
        content_type = response.headers.get('content-type', '')
        if 'html' in content_type and 'json' not in content_type:
            return None
        data = response.json()
        if data and 'races' in data:
            return data
    except Exception:
        pass
    return None


def _find_json_for_date(client: httpx.Client, base_url: str, track: str, date_str: str) -> Optional[Dict]:
    """指定日付のJSONを探索（標準形式 + 会場サフィックス付き）"""
    year = date_str[:4]
    month = date_str[5:7]

    # 標準形式: YYYY-MM-DD.json
    url = f"{base_url}/{track}/predictions/{year}/{month}/{date_str}.json"
    data = _try_fetch_json(client, url)
    if data:
        print(f"  ✅ データ取得成功: {url}")
        return data

    # 会場サフィックス付き: YYYY-MM-DD-VENUE.json
    for venue in VENUE_SUFFIXES:
        url = f"{base_url}/{track}/predictions/{year}/{month}/{date_str}-{venue}.json"
        data = _try_fetch_json(client, url)
        if data:
            print(f"  ✅ データ取得成功: {url}")
            return data

    return None


def fetch_track_predictions(api_base_url: str, track: str, fallback_days: int = 7) -> Optional[Dict]:
    """
    指定競馬場の予想データを取得（フォールバック機能付き）

    Args:
        api_base_url: データベースURL (keiba-data-shared)
        track: 競馬場名 (例: kawasaki, nankan, ooi)
        fallback_days: 本日のデータがない場合、過去何日分まで遡るか

    Returns:
        予想データ、または取得失敗時はNone
    """
    with httpx.Client(timeout=30.0) as client:
        # 本日から過去N日分を試行
        for days_back in range(fallback_days + 1):
            target_date = datetime.now() - timedelta(days=days_back)
            date_str = target_date.strftime('%Y-%m-%d')

            if days_back == 0:
                print(f"📡 予想データ取得中: {date_str}")
            else:
                print(f"📡 フォールバック: {days_back}日前のデータを試行 ({date_str})")

            data = _find_json_for_date(client, api_base_url, track, date_str)
            if data:
                if days_back > 0:
                    print(f"✅ {days_back}日前の予想データを使用: {track} ({date_str})")
                else:
                    print(f"✅ 予想データ取得成功: {track}")
                print(f"   レース数: {len(data['races'])}")
                return data
            else:
                if days_back == 0:
                    print(f"⚠️  本日のデータが見つかりません")
                    print(f"   過去{fallback_days}日分のデータを検索します...")

        # すべての試行が失敗
        print(f"❌ 過去{fallback_days}日間のデータが見つかりませんでした")
        return None


def convert_to_video_format(api_data: Dict) -> Dict:
    """
    keiba-data-shared レスポンスを動画生成用フォーマットに変換

    Args:
        api_data: keiba-data-shared から取得したデータ

    Returns:
        動画生成用データ
    """
    # 日付フォーマット変換
    date_str = api_data.get('date', datetime.now().strftime('%Y年%m月%d日'))
    try:
        # ISO 形式から日本語形式へ (例: 2026-03-06 -> 2026年03月06日)
        if '-' in date_str and len(date_str) == 10:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y年%m月%d日')
        else:
            formatted_date = date_str
    except Exception:
        formatted_date = date_str

    # 競馬場名取得（keiba-data-sharedは日本語で返す）
    track_name = api_data.get('track', '競馬')

    # レースデータ変換（keiba-data-sharedはすでに正しい形式）
    video_data = {
        'track': track_name,
        'date': formatted_date,
        'predictions': []
    }

    # keiba-data-sharedの形式: data['races'] は既に正しいフォーマット
    for race in api_data.get('races', []):
        # 予想データを生成（勝率でソート）
        horses = race.get('horses', [])

        # ダミーの勝率を割り当て（実際のAI予想は別途実装）
        predictions = []
        for idx, horse in enumerate(horses[:10]):
            # 仮の勝率: 1着馬を35%、以降は減少
            win_prob = max(0.05, 0.35 - (idx * 0.03))
            predictions.append({
                'number': horse.get('number', idx + 1),
                'name': horse.get('name', '馬名'),
                'win_probability': win_prob
            })

        # 勝率でソート
        predictions = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)

        race_data = {
            'race': race,  # raceInfo を含む
            'prediction': {
                'predictions': predictions
            }
        }

        video_data['predictions'].append(race_data)

    return video_data


def save_prediction_data(data: Dict, output_path: str = 'output/prediction_data.json'):
    """
    予想データを JSON ファイルに保存

    Args:
        data: 予想データ
        output_path: 保存先パス
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 予想データ保存: {output_path}")


def main():
    """メイン処理"""
    # 環境変数から設定取得
    api_base_url = os.environ.get('API_BASE_URL', 'https://keiba-data-shared.netlify.app')
    target_track = os.environ.get('TARGET_TRACK', 'kawasaki')

    print("=" * 70)
    print("📊 予想データ取得開始")
    print("=" * 70)
    print(f"データソース: {api_base_url}")
    print(f"対象競馬場: {target_track}")
    print(f"取得日付: {datetime.now().strftime('%Y-%m-%d')}")

    # データ取得
    api_data = fetch_track_predictions(api_base_url, target_track)

    if not api_data:
        print("❌ 予想データ取得失敗")
        exit(1)

    # 動画生成用フォーマットに変換
    video_data = convert_to_video_format(api_data)

    # JSON に保存
    save_prediction_data(video_data)

    print("\n" + "=" * 70)
    print("✅ 予想データ取得完了")
    print("=" * 70)
    print(f"競馬場: {video_data['track']}")
    print(f"日付: {video_data['date']}")
    print(f"レース数: {len(video_data['predictions'])}")


if __name__ == '__main__':
    main()
