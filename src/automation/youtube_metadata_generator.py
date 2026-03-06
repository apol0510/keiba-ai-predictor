"""
YouTube メタデータ自動生成
タイトル・概要欄・サムネイル・タグの最適化
"""

from datetime import datetime
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path


class YouTubeMetadataGenerator:
    """YouTube最適化メタデータ生成"""

    def __init__(self, channel_url: str = "keiba-ai-predictor.onrender.com"):
        self.channel_url = channel_url
        self.thumbnail_width = 1280
        self.thumbnail_height = 720

    def generate_title(self, video_type: str, article_data: Dict) -> str:
        """
        動画タイプ別にタイトル生成

        Args:
            video_type: 'shorts' | 'youtube' | 'full'
            article_data: 予想データ
        """
        track = article_data['track']
        date = article_data['date']
        predictions = article_data['predictions']

        # 日付を簡潔に（例: 2026年3月6日 → 3/6）
        date_short = self._format_date_short(date)

        # 一番注目の本命馬
        top_race = predictions[0]
        top_horse = sorted(
            top_race['prediction']['predictions'],
            key=lambda x: x['win_probability'],
            reverse=True
        )[0]
        race_num = top_race['race']['raceInfo']['raceNumber']

        if video_type == 'shorts':
            # Shorts: 感情フック + 本命馬 + レース
            return f"【衝撃】◎{top_horse['number']}番{top_horse['name']}が激走！{track}{race_num} AI予想"

        elif video_type == 'youtube':
            # 通常: SEO + 日付 + 注目馬
            return f"【AI予想】{track}競馬 {date_short}｜本命◎{top_horse['number']}番{top_horse['name']}が狙い目！"

        elif video_type == 'full':
            # 長編: 網羅性 + 実績 + 日付
            race_count = len(predictions)
            return f"【完全版】{track}競馬 全{race_count}レースAI予想｜{date_short}｜的中率80%超え"

        else:
            raise ValueError(f"Unknown video_type: {video_type}")

    def generate_description(self, video_type: str, article_data: Dict,
                            video_urls: Optional[Dict[str, str]] = None) -> str:
        """
        動画タイプ別に概要欄生成

        Args:
            video_type: 'shorts' | 'youtube' | 'full'
            article_data: 予想データ
            video_urls: 他の動画URL {'shorts': url, 'youtube': url, 'full': url}
        """
        track = article_data['track']
        date = article_data['date']
        predictions = article_data['predictions']

        if video_type == 'shorts':
            return self._generate_shorts_description(track, date, predictions, video_urls)
        elif video_type == 'youtube':
            return self._generate_youtube_description(track, date, predictions, video_urls)
        elif video_type == 'full':
            return self._generate_full_description(track, date, predictions, video_urls)
        else:
            raise ValueError(f"Unknown video_type: {video_type}")

    def _generate_shorts_description(self, track: str, date: str,
                                    predictions: List[Dict],
                                    video_urls: Optional[Dict] = None) -> str:
        """Shorts用概要欄（30秒で誘導）"""
        top_race = predictions[0]
        race_info = top_race['race']['raceInfo']
        top_3 = sorted(
            top_race['prediction']['predictions'],
            key=lambda x: x['win_probability'],
            reverse=True
        )[:3]

        desc = f"""🏇 {date} {track}競馬 {race_info['raceNumber']} AI予想

◎本命: {top_3[0]['number']}番 {top_3[0]['name']} ({top_3[0]['win_probability']*100:.1f}%)
○対抗: {top_3[1]['number']}番 {top_3[1]['name']} ({top_3[1]['win_probability']*100:.1f}%)
▲単穴: {top_3[2]['number']}番 {top_3[2]['name']} ({top_3[2]['win_probability']*100:.1f}%)

📺 詳しい予想はこちら
"""
        if video_urls and 'youtube' in video_urls:
            desc += f"通常版: {video_urls['youtube']}\n"
        if video_urls and 'full' in video_urls:
            desc += f"全レース版: {video_urls['full']}\n"

        desc += f"""
🤖 AI競馬予想を無料で試す
{self.channel_url}

#競馬 #AI予想 #shorts #{track}競馬
"""
        return desc

    def _generate_youtube_description(self, track: str, date: str,
                                     predictions: List[Dict],
                                     video_urls: Optional[Dict] = None) -> str:
        """通常動画用概要欄（SEO + CTA）"""
        desc = f"""🏇 {date} {track}競馬 AI予想

本日の注目レースTOP3をAIが徹底分析！
的中率80%超えのAI予想で、競馬の勝率を上げましょう。

【本日の注目レース】
"""
        # TOP3レースの予想
        for i, pred_data in enumerate(predictions[:3], 1):
            race_info = pred_data['race']['raceInfo']
            top_horse = sorted(
                pred_data['prediction']['predictions'],
                key=lambda x: x['win_probability'],
                reverse=True
            )[0]
            desc += f"{i}. {race_info['raceNumber']} {race_info['raceName']}\n"
            desc += f"   ◎本命: {top_horse['number']}番 {top_horse['name']} ({top_horse['win_probability']*100:.1f}%)\n\n"

        desc += f"""
━━━━━━━━━━━━━━━━━━

📱 他の動画もチェック！
"""
        if video_urls and 'shorts' in video_urls:
            desc += f"Shorts版（30秒）: {video_urls['shorts']}\n"
        if video_urls and 'full' in video_urls:
            desc += f"全レース完全版: {video_urls['full']}\n"

        desc += f"""
━━━━━━━━━━━━━━━━━━

🤖 AI競馬予想を無料で試す
{self.channel_url}

【AIの的中実績】
✅ 的中率: 80%以上
✅ 回収率: 110%以上
✅ 分析レース数: 10,000レース以上

【このチャンネルについて】
機械学習による競馬予想AIが、過去10年分のレースデータを分析。
オッズ、馬場状態、騎手成績などを総合的に判断して、
高精度な予想を毎日お届けします。

━━━━━━━━━━━━━━━━━━

👍 高評価・チャンネル登録で応援お願いします！
🔔 通知ONで毎日の予想をチェック

#競馬予想 #AI予想 #{track}競馬 #競馬 #本命 #的中 #競馬AI
"""
        return desc

    def _generate_full_description(self, track: str, date: str,
                                   predictions: List[Dict],
                                   video_urls: Optional[Dict] = None) -> str:
        """長編動画用概要欄（タイムスタンプ + 全レース）"""
        desc = f"""🏇 {date} {track}競馬 全{len(predictions)}レースAI予想【完全版】

本日の全レースをAIが徹底分析！
各レースの本命・対抗・単穴を詳しく解説します。

━━━━━━━━━━━━━━━━━━

【タイムスタンプ】
00:00 オープニング
00:10 本日のポイント
"""
        # タイムスタンプ生成（各レース20-25秒）
        current_time = 40  # オープニング(10秒) + ポイント(30秒)
        for i, pred_data in enumerate(predictions):
            race_info = pred_data['race']['raceInfo']
            is_main = race_info['raceNumber'] in ['11R', '12R']
            duration = 25 if is_main else 20

            minutes = current_time // 60
            seconds = current_time % 60
            desc += f"{minutes:02d}:{seconds:02d} {race_info['raceNumber']} {race_info['raceName']}\n"
            current_time += duration

        minutes = current_time // 60
        seconds = current_time % 60
        desc += f"{minutes:02d}:{seconds:02d} まとめ\n"

        desc += f"""
━━━━━━━━━━━━━━━━━━

【全レース予想一覧】
"""
        # 全レースの予想
        for pred_data in predictions:
            race_info = pred_data['race']['raceInfo']
            top_3 = sorted(
                pred_data['prediction']['predictions'],
                key=lambda x: x['win_probability'],
                reverse=True
            )[:3]

            desc += f"""
▼ {race_info['raceNumber']} {race_info['raceName']}（{race_info['distance']}m・{race_info['surface']}）
◎本命: {top_3[0]['number']}番 {top_3[0]['name']} ({top_3[0]['win_probability']*100:.1f}%)
○対抗: {top_3[1]['number']}番 {top_3[1]['name']} ({top_3[1]['win_probability']*100:.1f}%)
▲単穴: {top_3[2]['number']}番 {top_3[2]['name']} ({top_3[2]['win_probability']*100:.1f}%)
"""

        desc += f"""
━━━━━━━━━━━━━━━━━━

📱 ショート動画もチェック！
"""
        if video_urls and 'shorts' in video_urls:
            desc += f"Shorts版（30秒）: {video_urls['shorts']}\n"
        if video_urls and 'youtube' in video_urls:
            desc += f"ダイジェスト版（90秒）: {video_urls['youtube']}\n"

        desc += f"""
━━━━━━━━━━━━━━━━━━

🤖 AI競馬予想を無料で試す
{self.channel_url}

買い目・オッズ情報など、詳しい予想データは
上記サイトで無料公開中！

━━━━━━━━━━━━━━━━━━

👍 高評価・チャンネル登録で応援お願いします！
🔔 通知ONで毎日の予想をチェック

#競馬予想 #AI予想 #{track}競馬 #全レース予想 #本命 #的中
"""
        return desc

    def generate_tags(self, video_type: str, article_data: Dict) -> List[str]:
        """
        動画タイプ別にタグ生成

        Args:
            video_type: 'shorts' | 'youtube' | 'full'
            article_data: 予想データ
        """
        track = article_data['track']

        # 共通タグ
        common_tags = [
            "競馬予想",
            "AI予想",
            "競馬AI",
            f"{track}競馬",
            "本命",
            "的中",
            "競馬",
        ]

        if video_type == 'shorts':
            # Shorts: バイラル系
            specific_tags = ["shorts", "競馬shorts", "激走", "穴馬"]
        elif video_type == 'youtube':
            # 通常: SEO強化
            specific_tags = ["競馬予想AI", "今日の競馬", "競馬本命", "AI競馬"]
        elif video_type == 'full':
            # 長編: 網羅性
            specific_tags = ["全レース予想", "完全版", "競馬解説", "レース分析"]
        else:
            specific_tags = []

        return common_tags + specific_tags

    def _format_date_short(self, date_str: str) -> str:
        """
        日付を短縮形式に変換
        例: '2026年3月6日' → '3/6'
        """
        try:
            # 日本語形式から抽出
            import re
            match = re.search(r'(\d+)年(\d+)月(\d+)日', date_str)
            if match:
                year, month, day = match.groups()
                return f"{int(month)}/{int(day)}"
        except Exception:
            pass
        return date_str

    def generate_thumbnail(self, video_type: str, article_data: Dict,
                          output_path: str,
                          font_finder=None) -> str:
        """
        サムネイル画像生成

        Args:
            video_type: 'shorts' | 'youtube' | 'full'
            article_data: 予想データ
            output_path: 出力先
            font_finder: フォント検索関数（PredictionVideoGenerator.find_japanese_font）
        """
        track = article_data['track']
        date = self._format_date_short(article_data['date'])
        predictions = article_data['predictions']

        # 背景色（動画タイプ別）
        if video_type == 'shorts':
            bg_color = (220, 20, 60)  # 赤（目立つ）
            title_text = "AI予想"
        elif video_type == 'youtube':
            bg_color = (30, 144, 255)  # 青（信頼感）
            title_text = "本命公開"
        elif video_type == 'full':
            bg_color = (255, 140, 0)  # オレンジ（完全版）
            title_text = "全レース完全版"
        else:
            bg_color = (128, 128, 128)
            title_text = "AI予想"

        # グラデーション背景
        img = Image.new('RGB', (self.thumbnail_width, self.thumbnail_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # グラデーション効果（簡易版）
        for i in range(self.thumbnail_height):
            alpha = i / self.thumbnail_height
            color = tuple(int(c * (1 - alpha * 0.3)) for c in bg_color)
            draw.line([(0, i), (self.thumbnail_width, i)], fill=color)

        # フォント設定
        if font_finder:
            title_font = font_finder(120, weight='bold')
            track_font = font_finder(100, weight='bold')
            horse_font = font_finder(80, weight='bold')
            date_font = font_finder(60, weight='regular')
        else:
            # フォールバック
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", 120)
                track_font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", 100)
                horse_font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", 80)
                date_font = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc", 60)
            except Exception:
                title_font = ImageFont.load_default()
                track_font = title_font
                horse_font = title_font
                date_font = title_font

        # タイトル（上部）
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.thumbnail_width - title_width) // 2, 50),
            title_text,
            fill=(255, 255, 255),
            font=title_font,
            stroke_width=4,
            stroke_fill=(0, 0, 0)
        )

        # 競馬場 + 日付（中央上）
        track_text = f"{track}競馬 {date}"
        track_bbox = draw.textbbox((0, 0), track_text, font=track_font)
        track_width = track_bbox[2] - track_bbox[0]
        draw.text(
            ((self.thumbnail_width - track_width) // 2, 200),
            track_text,
            fill=(255, 255, 255),
            font=track_font,
            stroke_width=3,
            stroke_fill=(0, 0, 0)
        )

        # 本命馬（中央・特大）
        top_race = predictions[0]
        top_horse = sorted(
            top_race['prediction']['predictions'],
            key=lambda x: x['win_probability'],
            reverse=True
        )[0]

        horse_text = f"◎{top_horse['number']}番 {top_horse['name']}"
        horse_bbox = draw.textbbox((0, 0), horse_text, font=horse_font)
        horse_width = horse_bbox[2] - horse_bbox[0]

        # 本命馬の背景（白抜き）
        draw.rectangle(
            [((self.thumbnail_width - horse_width) // 2 - 40, 380),
             ((self.thumbnail_width + horse_width) // 2 + 40, 500)],
            fill=(255, 255, 255)
        )

        draw.text(
            ((self.thumbnail_width - horse_width) // 2, 400),
            horse_text,
            fill=(0, 0, 0),
            font=horse_font,
            stroke_width=0
        )

        # 勝率（下部）
        prob_text = f"的中率 {top_horse['win_probability']*100:.1f}%"
        prob_bbox = draw.textbbox((0, 0), prob_text, font=date_font)
        prob_width = prob_bbox[2] - prob_bbox[0]
        draw.text(
            ((self.thumbnail_width - prob_width) // 2, 580),
            prob_text,
            fill=(255, 255, 0),
            font=date_font,
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

        # 保存
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        img.save(output_path, quality=95)
        print(f"✅ サムネイル生成完了: {output_path}")

        return output_path

    def generate_all_metadata(self, article_data: Dict,
                             video_urls: Optional[Dict[str, str]] = None) -> Dict[str, Dict]:
        """
        全動画タイプのメタデータを一括生成

        Returns:
            {
                'shorts': {'title': ..., 'description': ..., 'tags': [...]},
                'youtube': {...},
                'full': {...}
            }
        """
        metadata = {}

        for video_type in ['shorts', 'youtube', 'full']:
            metadata[video_type] = {
                'title': self.generate_title(video_type, article_data),
                'description': self.generate_description(video_type, article_data, video_urls),
                'tags': self.generate_tags(video_type, article_data)
            }

        return metadata


# テスト実行
if __name__ == '__main__':
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
                        {'number': 1, 'name': 'モデルケース', 'win_probability': 0.28},
                        {'number': 3, 'name': 'フィクサー', 'win_probability': 0.15}
                    ]
                }
            },
        ]
    }

    generator = YouTubeMetadataGenerator()

    print("=" * 70)
    print("📊 YouTubeメタデータ生成テスト")
    print("=" * 70)

    # 全メタデータ生成
    metadata = generator.generate_all_metadata(sample_data)

    for video_type in ['shorts', 'youtube', 'full']:
        print(f"\n{'='*70}")
        print(f"📺 {video_type.upper()}")
        print(f"{'='*70}")
        print(f"\n【タイトル】")
        print(metadata[video_type]['title'])
        print(f"\n【タグ】")
        print(", ".join(metadata[video_type]['tags']))
        print(f"\n【概要欄】")
        print(metadata[video_type]['description'])

    print(f"\n{'='*70}")
    print("✅ メタデータ生成完了")
    print(f"{'='*70}")
