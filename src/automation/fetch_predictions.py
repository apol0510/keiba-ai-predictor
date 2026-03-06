"""
予想データ取得スクリプト
API から本日の予想データを取得
"""

import httpx
import os
import json
from datetime import datetime
from typing import Dict, List, Optional


def fetch_track_predictions(api_base_url: str, track: str) -> Optional[Dict]:
    """
    指定競馬場の予想データを取得

    Args:
        api_base_url: APIベースURL
        track: 競馬場名 (例: kawasaki, nankan, ooi)

    Returns:
        予想データ、または取得失敗時はNone
    """
    try:
        # 本日の日付
        today = datetime.now().strftime('%Y-%m-%d')

        # API URL構築
        url = f"{api_base_url}/api/predictions/{track}?date={today}"

        print(f"📡 予想データ取得中: {url}")

        # データ取得
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()

            data = response.json()

            if not data or 'predictions' not in data:
                print(f"⚠️  予想データが見つかりません: {track}")
                return None

            print(f"✅ 予想データ取得成功: {track}")
            print(f"   レース数: {len(data['predictions'])}")

            return data

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP エラー: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"❌ 予想データ取得失敗: {e}")
        return None


def convert_to_video_format(api_data: Dict) -> Dict:
    """
    API レスポンスを動画生成用フォーマットに変換

    Args:
        api_data: API から取得した予想データ

    Returns:
        動画生成用データ
    """
    # 日付フォーマット変換
    date_str = api_data.get('date', datetime.now().strftime('%Y年%m月%d日'))
    try:
        # ISO 形式から日本語形式へ
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        formatted_date = date_obj.strftime('%Y年%m月%d日')
    except Exception:
        formatted_date = date_str

    # 競馬場名マッピング
    track_mapping = {
        'kawasaki': '川崎',
        'nankan': '南関',
        'ooi': '大井',
        'funabashi': '船橋',
        'urawa': '浦和'
    }

    track_name = track_mapping.get(
        api_data.get('track', '').lower(),
        api_data.get('track', '競馬')
    )

    # 予想データ変換
    video_data = {
        'track': track_name,
        'date': formatted_date,
        'predictions': []
    }

    for pred in api_data.get('predictions', []):
        race_data = {
            'race': {
                'raceInfo': {
                    'raceNumber': pred.get('race_number', '1R'),
                    'raceName': pred.get('race_name', 'レース'),
                    'distance': str(pred.get('distance', '1400')),
                    'surface': pred.get('surface', 'ダート'),
                    'startTime': pred.get('start_time', '15:00')
                }
            },
            'prediction': {
                'predictions': []
            }
        }

        # 馬の予想データ
        for horse in pred.get('horses', [])[:10]:  # 最大10頭
            race_data['prediction']['predictions'].append({
                'number': horse.get('number', 1),
                'name': horse.get('name', '馬名'),
                'win_probability': horse.get('win_probability', 0.0)
            })

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
    api_base_url = os.environ.get('API_BASE_URL', 'https://keiba-ai-predictor.onrender.com')
    target_track = os.environ.get('TARGET_TRACK', 'kawasaki')

    print("=" * 70)
    print("📊 予想データ取得開始")
    print("=" * 70)
    print(f"API URL: {api_base_url}")
    print(f"対象競馬場: {target_track}")

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
