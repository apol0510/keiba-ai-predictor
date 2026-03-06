"""
予想動画自動生成
MoviePyを使用してAI予想を動画化
"""

from moviepy.editor import (
    ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
from typing import List, Dict
import os
from pathlib import Path


class PredictionVideoGenerator:
    """予想動画を自動生成"""

    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.fps = 24

        # カラースキーム（keiba-ai-predictorのブランドカラー）
        self.colors = {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'white': '#ffffff',
            'black': '#2c3e50',
            'gray': '#666666'
        }

    def hex_to_rgb(self, hex_color: str) -> tuple:
        """HEX色をRGBタプルに変換"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def find_japanese_font(self, size: int, weight: str = 'regular') -> ImageFont.FreeTypeFont:
        """
        日本語対応フォントを探索して返す

        Args:
            size: フォントサイズ
            weight: 'regular' or 'bold'

        Returns:
            ImageFont.FreeTypeFont

        Raises:
            RuntimeError: 日本語フォントが見つからない場合
        """
        # フォント候補パス（優先度順）
        if weight == 'bold':
            candidates = [
                # Linux/GitHub Actions (Noto CJK Bold)
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
                # macOS (Hiragino Bold)
                "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                # Fallback to regular
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]
        else:
            candidates = [
                # Linux/GitHub Actions (Noto CJK Regular)
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                # macOS (Hiragino Regular)
                "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]

        # フォント探索
        for font_path in candidates:
            if Path(font_path).exists():
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception as e:
                    print(f"⚠️  フォント読み込み失敗: {font_path} - {e}")
                    continue

        # すべて失敗した場合はエラー
        searched_paths = "\n  - ".join(candidates)
        raise RuntimeError(
            f"日本語対応フォントが見つかりません。\n"
            f"探索したパス:\n  - {searched_paths}\n\n"
            f"fonts-noto-cjk がインストールされているか確認してください。\n"
            f"Ubuntu/Debian: sudo apt-get install fonts-noto-cjk"
        )

    def create_opening(self, track: str, date_str: str) -> ImageClip:
        """オープニング画像生成（5秒）"""
        img = Image.new('RGB', (self.width, self.height),
                        color=self.hex_to_rgb(self.colors['primary']))
        draw = ImageDraw.Draw(img)

        # 日本語対応フォント取得
        title_font = self.find_japanese_font(120, weight='bold')
        subtitle_font = self.find_japanese_font(80, weight='regular')

        # タイトル
        title_text = "AI競馬予想"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 300),
            title_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=title_font
        )

        # サブタイトル
        subtitle = f"{date_str} {track}競馬"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(
            ((self.width - subtitle_width) // 2, 500),
            subtitle,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        # 機械学習モデル説明
        desc = "的中率33.01% 機械学習モデル"
        desc_bbox = draw.textbbox((0, 0), desc, font=subtitle_font)
        desc_width = desc_bbox[2] - desc_bbox[0]
        draw.text(
            ((self.width - desc_width) // 2, 700),
            desc,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        return ImageClip(np.array(img)).set_duration(5)

    def create_prediction_slide(self, race_info: Dict, prediction: Dict) -> ImageClip:
        """予想スライド生成（各10秒）"""
        # グラデーション背景
        img = Image.new('RGB', (self.width, self.height),
                        color=self.hex_to_rgb(self.colors['white']))
        draw = ImageDraw.Draw(img)

        # 日本語対応フォント取得
        race_font = self.find_japanese_font(80, weight='bold')
        horse_font = self.find_japanese_font(70, weight='bold')
        detail_font = self.find_japanese_font(50, weight='regular')

        # レース情報ヘッダー（背景色付き）
        header_rect = [(0, 0), (self.width, 200)]
        draw.rectangle(header_rect, fill=self.hex_to_rgb(self.colors['primary']))

        race_title = f"{race_info['raceNumber']} {race_info['raceName']}"
        draw.text((100, 50), race_title, fill=self.hex_to_rgb(self.colors['white']), font=race_font)

        race_details = f"{race_info['distance']}m {race_info['surface']} {race_info['startTime']}発走"
        draw.text((100, 140), race_details, fill=self.hex_to_rgb(self.colors['white']), font=detail_font)

        # 本命・対抗・単穴
        predictions = sorted(
            prediction['predictions'],
            key=lambda x: x['win_probability'],
            reverse=True
        )[:3]

        y_pos = 350
        marks = ['◎', '○', '▲']
        roles = ['本命', '対抗', '単穴']

        for idx, (mark, role, pred) in enumerate(zip(marks, roles, predictions)):
            # マーク
            draw.text((100, y_pos), mark, fill=self.hex_to_rgb(self.colors['primary']), font=horse_font)

            # 馬情報
            horse_text = f"{pred['number']}番 {pred['name']}"
            draw.text((200, y_pos), horse_text, fill=self.hex_to_rgb(self.colors['black']), font=horse_font)

            # 勝率
            prob_text = f"{pred['win_probability']*100:.1f}%"
            draw.text((1400, y_pos), prob_text, fill=self.hex_to_rgb(self.colors['primary']), font=horse_font)

            y_pos += 150

        # フッター
        footer_text = "詳しくは keiba-ai-predictor.onrender.com"
        draw.text((100, 950), footer_text, fill=self.hex_to_rgb(self.colors['gray']), font=detail_font)

        return ImageClip(np.array(img)).set_duration(10)

    def create_ending(self) -> ImageClip:
        """エンディング画像生成（5秒）"""
        img = Image.new('RGB', (self.width, self.height),
                        color=self.hex_to_rgb(self.colors['secondary']))
        draw = ImageDraw.Draw(img)

        # 日本語対応フォント取得
        title_font = self.find_japanese_font(100, weight='bold')
        url_font = self.find_japanese_font(70, weight='bold')

        # CTA
        cta_text = "無料で予想を試す"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=title_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
        draw.text(
            ((self.width - cta_width) // 2, 350),
            cta_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=title_font
        )

        # URL
        url_text = "keiba-ai-predictor.onrender.com"
        url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
        url_width = url_bbox[2] - url_bbox[0]
        draw.text(
            ((self.width - url_width) // 2, 550),
            url_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=url_font
        )

        return ImageClip(np.array(img)).set_duration(5)

    def generate_video(self, article_data: Dict, output_path: str = None) -> str:
        """
        予想データから動画生成

        Args:
            article_data: daily_prediction.pyで生成された記事データ
            output_path: 出力先パス（省略時は自動生成）

        Returns:
            生成された動画ファイルのパス
        """
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f"output/prediction_{date_str}.mp4"

        # 出力ディレクトリ作成
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        clips = []

        # オープニング
        clips.append(self.create_opening(
            article_data['track'],
            article_data['date']
        ))

        # 各レースの予想スライド
        for pred_data in article_data['predictions']:
            race_info = pred_data['race']['raceInfo']
            prediction = pred_data['prediction']

            clips.append(self.create_prediction_slide(race_info, prediction))

        # エンディング
        clips.append(self.create_ending())

        # 動画結合
        final_video = concatenate_videoclips(clips, method="compose")

        # 動画書き出し
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio=False,
            preset='medium'
        )

        print(f"✅ 動画生成完了: {output_path}")
        return output_path


# テスト実行
if __name__ == '__main__':
    # サンプルデータ
    sample_data = {
        'track': '川崎',
        'date': '2026年3月5日',
        'predictions': [
            {
                'race': {
                    'raceInfo': {
                        'raceNumber': '1R',
                        'raceName': 'サラ4歳以上',
                        'distance': '1400',
                        'surface': 'ダート',
                        'startTime': '15:00'
                    }
                },
                'prediction': {
                    'predictions': [
                        {'number': 4, 'name': 'ジーティーラピッド', 'win_probability': 0.35},
                        {'number': 9, 'name': 'イノ', 'win_probability': 0.25},
                        {'number': 6, 'name': 'キタサンブリリアン', 'win_probability': 0.15}
                    ]
                }
            }
        ]
    }

    generator = PredictionVideoGenerator()
    video_path = generator.generate_video(sample_data, "test_output.mp4")
    print(f"動画ファイル: {video_path}")
