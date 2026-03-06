"""
3階層動画自動生成スクリプト
予想データから Shorts + 通常 + 長編動画を生成
"""

import os
import json
from pathlib import Path
from youtube_format_generator import YouTubeFormatGenerator


def load_prediction_data(data_path: str = 'output/prediction_data.json') -> dict:
    """
    予想データを読み込み

    Args:
        data_path: 予想データのパス

    Returns:
        予想データ
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"予想データが見つかりません: {data_path}")

    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """メイン処理"""
    print("=" * 70)
    print("🎬 3階層動画生成開始")
    print("=" * 70)

    # 環境変数から設定取得
    tts_engine = os.environ.get('TTS_ENGINE', 'gtts')
    use_ai_bg = os.environ.get('USE_AI_BACKGROUNDS', 'false').lower() == 'true'
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    bgm_path = os.environ.get('BGM_PATH')  # オプション

    print(f"🎙️  TTS Engine: {tts_engine}")
    print(f"🎨 AI Backgrounds: {use_ai_bg}")

    # 予想データ読み込み
    try:
        prediction_data = load_prediction_data()
        print(f"✅ 予想データ読み込み成功")
        print(f"   競馬場: {prediction_data['track']}")
        print(f"   日付: {prediction_data['date']}")
        print(f"   レース数: {len(prediction_data['predictions'])}")
    except Exception as e:
        print(f"❌ 予想データ読み込み失敗: {e}")
        exit(1)

    # 動画生成
    try:
        generator = YouTubeFormatGenerator(
            tts_engine=tts_engine,
            use_ai_backgrounds=use_ai_bg,
            openai_api_key=openai_api_key
        )

        # 3階層動画 + メタデータ + サムネイル生成
        results = generator.generate_all_formats(
            prediction_data,
            bgm_path=bgm_path if bgm_path and os.path.exists(bgm_path) else None,
            generate_metadata=True
        )

        print("\n" + "=" * 70)
        print("✅ 3階層動画生成完了！")
        print("=" * 70)

        # 生成結果サマリー
        print("\n📹 生成された動画:")
        for video_type, path in results['videos'].items():
            print(f"  {video_type}: {path}")

        print("\n🖼️  生成されたサムネイル:")
        for video_type, path in results['thumbnails'].items():
            print(f"  {video_type}: {path}")

        print("\n📊 メタデータ:")
        for video_type in ['shorts', 'youtube', 'full']:
            metadata = results['metadata'][video_type]
            print(f"\n【{video_type.upper()}】")
            print(f"  タイトル: {metadata['title']}")
            print(f"  タグ数: {len(metadata['tags'])}")

        # 結果をJSONに保存（GitHub Actionsアーティファクト用）
        result_summary = {
            'success': True,
            'track': prediction_data['track'],
            'date': prediction_data['date'],
            'race_count': len(prediction_data['predictions']),
            'videos': results['videos'],
            'thumbnails': results['thumbnails'],
            'metadata_file': 'output/metadata_*.json'
        }

        summary_path = 'output/generation_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(result_summary, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 生成サマリー保存: {summary_path}")

    except Exception as e:
        print(f"\n❌ 動画生成失敗: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
