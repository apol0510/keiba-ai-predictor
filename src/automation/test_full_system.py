"""
完全統合テスト: 動画 + メタデータ + サムネイル
"""

import os
from youtube_format_generator import YouTubeFormatGenerator

# サンプルデータ
sample_data = {
    'track': '川崎',
    'date': '2026年3月6日',
    'predictions': [
        {
            'race': {
                'raceInfo': {
                    'raceNumber': '11R',
                    'raceName': 'スパーキングNCh',
                    'distance': '2100',
                    'surface': 'ダート',
                    'startTime': '20:15'
                }
            },
            'prediction': {
                'predictions': [
                    {'number': 4, 'name': 'ジーティーラピッド', 'win_probability': 0.35},
                    {'number': 7, 'name': 'サンプルホース', 'win_probability': 0.25},
                    {'number': 2, 'name': 'テストデータ', 'win_probability': 0.18}
                ]
            }
        },
        {
            'race': {
                'raceInfo': {
                    'raceNumber': '10R',
                    'raceName': 'マーチC',
                    'distance': '1600',
                    'surface': 'ダート',
                    'startTime': '19:40'
                }
            },
            'prediction': {
                'predictions': [
                    {'number': 5, 'name': 'エグザンプル', 'win_probability': 0.32},
                    {'number': 1, 'name': 'モデル', 'win_probability': 0.28},
                    {'number': 3, 'name': 'フィクサー', 'win_probability': 0.15}
                ]
            }
        },
        {
            'race': {
                'raceInfo': {
                    'raceNumber': '9R',
                    'raceName': 'クラシックC',
                    'distance': '1500',
                    'surface': 'ダート',
                    'startTime': '19:05'
                }
            },
            'prediction': {
                'predictions': [
                    {'number': 6, 'name': 'アルゴリズム', 'win_probability': 0.40},
                    {'number': 8, 'name': 'パターン', 'win_probability': 0.22},
                    {'number': 2, 'name': 'ロジック', 'win_probability': 0.16}
                ]
            }
        }
    ]
}

# 環境設定
tts_engine = os.environ.get('TTS_ENGINE', 'gtts')
use_ai_bg = os.environ.get('USE_AI_BACKGROUNDS', 'false').lower() == 'true'

print(f"🎙️  TTS Engine: {tts_engine}")
print(f"🎨 AI Backgrounds: {use_ai_bg}")

# ジェネレーター作成
generator = YouTubeFormatGenerator(
    tts_engine=tts_engine,
    use_ai_backgrounds=use_ai_bg
)

# 完全統合テスト: 動画 + メタデータ + サムネイル
results = generator.generate_all_formats(
    sample_data,
    bgm_path=None,  # BGMなし
    generate_metadata=True  # メタデータ・サムネイル生成
)

print("\n" + "=" * 70)
print("🎉 完全統合テスト完了！")
print("=" * 70)
print("\n生成されたファイル:")
print(f"\n【動画】")
for video_type, path in results['videos'].items():
    print(f"  {video_type}: {path}")

print(f"\n【サムネイル】")
for video_type, path in results['thumbnails'].items():
    print(f"  {video_type}: {path}")

print(f"\n【メタデータ】")
print(f"  すべてのタイトル・概要欄・タグが生成されました")

print("\n" + "=" * 70)
