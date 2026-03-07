"""
予想動画自動生成
MoviePyを使用してAI予想を動画化
BGM・ナレーション・デザイン改善版
"""

from moviepy.editor import (
    ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip, CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import os
from pathlib import Path
from gtts import gTTS
import tempfile
import re
import unicodedata

# OpenAI TTS (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def sanitize_display_text(text: str) -> str:
    """
    画面表示用テキストのサニタイズ（文字化け防止）

    目的：フォント非対応文字や制御文字を除去し、
    すべてのデバイスで正しく表示されるテキストにする。

    Args:
        text: 元の表示テキスト

    Returns:
        サニタイズされたテキスト
    """
    if not text:
        return ""

    text = str(text)

    # Unicode正規化（全角・半角を統一）
    text = unicodedata.normalize("NFKC", text)

    # 文字化けの原因となる特殊文字を除去
    text = text.replace("\u25a1", " ")  # □
    text = text.replace("\u2715", " ")  # ✕
    text = text.replace("\u00d7", "×")  # ×（表示用）

    # 不可視の制御文字を除去
    text = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", text)

    # 空白の整理
    text = re.sub(r"\s+", " ", text).strip()

    return text


def create_race_narration(race_num: str, race_name: str, horses: list) -> str:
    """
    TTS専用のレースナレーションを生成

    馬名の前後に必ず区切りを入れることで、TTSの発音品質を向上させる

    Args:
        race_num: レース番号 (例: "1R")
        race_name: レース名
        horses: [{' number': int, 'name': str, 'role': '本命'|'対抗'|'単穴'}]

    Returns:
        TTS最適化されたナレーションテキスト
    """
    # レース番号を正規化
    race_num_normalized = re.sub(r'(\d{1,2})R', r'\1レース', race_num)

    # ナレーション構築
    narration_parts = [f"{race_num_normalized}、{race_name}です。"]

    for horse in horses:
        role = horse.get('role', '')
        number = horse.get('number', '')
        name = horse.get('name', '')

        # 馬名の前後に区切りを入れる
        if role == '本命':
            narration_parts.append(f"本命は、{number}番、{name}です。")
        elif role == '対抗':
            narration_parts.append(f"対抗は、{number}番、{name}。")
        elif role == '単穴':
            narration_parts.append(f"単穴は、{number}番、{name}です。")

    return "\n".join(narration_parts)


def normalize_tts_text(text: str) -> str:
    """
    TTS音声生成前のテキスト正規化（共通処理）

    目的：日本人が自然に聞ける競馬予想動画を実現するため、
    すべての読み上げテキストを統一的に正規化する。

    Args:
        text: 元のナレーションテキスト

    Returns:
        正規化されたテキスト
    """
    if not text:
        return text

    text = str(text)

    # ===== レース番号の正規化 =====
    # "1R", "2R" → "1レース", "2レース"
    text = re.sub(r'(\d{1,2})R\b', r'\1レース', text)

    # ===== 競馬記号の読み =====
    text = text.replace('◎', '本命、')
    text = text.replace('○', '対抗、')
    text = text.replace('▲', '単穴、')
    text = text.replace('△', '連下、')
    text = text.replace('×', '抑え、')

    # ===== 英字・略語の読み =====
    text = text.replace('AI', 'エーアイ')
    text = text.replace('JRA', 'ジェイアールエー')
    text = text.replace('NAR', 'エヌエーアール')
    text = text.replace('BGM', 'ビージーエム')
    text = text.replace('TTS', 'ティーティーエス')

    # ===== 競馬専門用語の読み方 =====
    text = text.replace('買い目', 'かいめ')
    text = text.replace('概要欄', 'がいようらん')
    text = text.replace('馬単', 'ばたん')
    text = text.replace('馬連', 'うまれん')
    text = text.replace('三連複', 'さんれんぷく')
    text = text.replace('三連単', 'さんれんたん')
    text = text.replace('ワイド', 'わいど')

    # ===== 読みにくい記号・句読点 =====
    text = text.replace('・', '、')
    text = text.replace('！', '')  # 感嘆符は除去
    text = text.replace('!', '')
    text = text.replace('★', '')
    text = text.replace('☆', '')
    text = text.replace('/', 'スラッシュ')

    # ===== 数字の読みやすさ改善 =====
    # "3-5-7" → "3、5、7"（オッズ表記など）
    text = re.sub(r'(\d+)-(\d+)-(\d+)', r'\1、\2、\3', text)

    # ===== 空白・改行の整理 =====
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # ===== 句読点の調整（読みやすさ向上） =====
    # 連続する句読点を整理
    text = re.sub(r'[、。]+', lambda m: m.group(0)[0], text)

    return text


class PredictionVideoGenerator:
    """予想動画を自動生成"""

    def __init__(self, width: int = 1920, height: int = 1080,
                 openai_api_key: Optional[str] = None,
                 tts_engine: str = 'gtts',
                 use_ai_backgrounds: bool = False,
                 background_cache_dir: str = 'cache/backgrounds'):
        """
        Args:
            width: 動画の幅
            height: 動画の高さ
            openai_api_key: OpenAI APIキー（OpenAI TTS/DALL-E使用時）
            tts_engine: 'gtts' or 'openai' - 使用するTTSエンジン
            use_ai_backgrounds: AI生成背景を使用するか
            background_cache_dir: 背景画像キャッシュディレクトリ
        """
        self.width = width
        self.height = height
        self.fps = 24
        self.tts_engine = tts_engine
        self.use_ai_backgrounds = use_ai_backgrounds
        self.background_cache_dir = Path(background_cache_dir)

        # キャッシュディレクトリ作成
        if use_ai_backgrounds:
            self.background_cache_dir.mkdir(parents=True, exist_ok=True)

        # OpenAI設定
        self.openai_client = None
        if (tts_engine == 'openai' or use_ai_backgrounds) and OPENAI_AVAILABLE:
            api_key = openai_api_key or os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                print("⚠️  OPENAI_API_KEYが設定されていません。")
                if tts_engine == 'openai':
                    print("   gTTSにフォールバックします。")
                    self.tts_engine = 'gtts'
                if use_ai_backgrounds:
                    print("   AI背景を無効化します。")
                    self.use_ai_backgrounds = False

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

    def generate_narration(self, text: str) -> Optional[str]:
        """
        ナレーション音声を生成（OpenAI TTS or gTTS）

        すべてのナレーションは normalize_tts_text() で正規化されます。

        Args:
            text: ナレーション内容

        Returns:
            生成された音声ファイルのパス（一時ファイル）
        """
        try:
            # ★★★ 必ずすべてのテキストを正規化 ★★★
            normalized_text = normalize_tts_text(text)

            # デバッグ: TTS入力を確認
            print(f"[TTS INPUT] Original: {repr(text)}")
            print(f"[TTS INPUT] Normalized: {repr(normalized_text)}")

            if self.tts_engine == 'openai' and self.openai_client:
                return self._generate_openai_tts(normalized_text)
            else:
                return self._generate_gtts(normalized_text)
        except Exception as e:
            print(f"⚠️  ナレーション生成エラー: {e}")
            return None

    def _generate_openai_tts(self, text: str) -> Optional[str]:
        """
        OpenAI TTSで音声生成

        Args:
            text: ナレーション内容

        Returns:
            生成された音声ファイルのパス
        """
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",  # 高品質モデル
                voice="nova",      # nova: 日本語に最適な女性の声
                input=text,
                speed=1.1          # やや速めで間を短縮
            )

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            response.stream_to_file(temp_file.name)
            print(f"✅ OpenAI TTS音声生成: {len(text)}文字")
            return temp_file.name
        except Exception as e:
            print(f"⚠️  OpenAI TTS生成エラー: {e}")
            print("   gTTSにフォールバックします...")
            return self._generate_gtts(text)

    def _generate_gtts(self, text: str) -> Optional[str]:
        """
        gTTSで音声生成（フォールバック用）

        Args:
            text: ナレーション内容

        Returns:
            生成された音声ファイルのパス
        """
        try:
            tts = gTTS(text=text, lang='ja', slow=False)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            return temp_file.name
        except Exception as e:
            print(f"⚠️  gTTS生成エラー: {e}")
            return None

    def generate_ai_background(self, track: str, scene_type: str = 'opening') -> Optional[str]:
        """
        DALL-EでAI背景画像を生成（キャッシュ機能付き）

        Args:
            track: 競馬場名（例: '川崎'）
            scene_type: 'opening', 'race', 'ending'

        Returns:
            生成された画像ファイルのパス（キャッシュ済み）
        """
        if not self.use_ai_backgrounds or not self.openai_client:
            return None

        # キャッシュファイル名
        cache_filename = f"{track}_{scene_type}.png"
        cache_path = self.background_cache_dir / cache_filename

        # キャッシュがあれば使用
        if cache_path.exists():
            print(f"✅ キャッシュ使用: {cache_filename}")
            return str(cache_path)

        # プロンプト生成
        prompts = {
            'opening': f"{track} horse racing stadium at night, dramatic lighting, cinematic, professional sports photography, high quality, atmospheric",
            'race': f"{track} horse racing track, aerial view, professional photography, cinematic lighting, high quality",
            'ending': f"horse racing stadium sunset, beautiful sky, cinematic, professional photography, high quality"
        }

        prompt = prompts.get(scene_type, prompts['opening'])

        try:
            print(f"🎨 AI背景生成中: {track} ({scene_type})...")

            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",  # 横長（動画に最適）
                quality="standard",  # "hd" or "standard"
                n=1
            )

            # 画像URLを取得
            image_url = response.data[0].url

            # 画像をダウンロード
            import requests
            img_response = requests.get(image_url)

            # キャッシュに保存
            with open(cache_path, 'wb') as f:
                f.write(img_response.content)

            print(f"✅ AI背景生成完了: {cache_filename}")
            return str(cache_path)

        except Exception as e:
            print(f"⚠️  AI背景生成エラー: {e}")
            print("   グラデーション背景にフォールバックします。")
            return None

    def load_and_resize_background(self, image_path: str) -> Image.Image:
        """
        背景画像を読み込んで動画サイズにリサイズ

        Args:
            image_path: 画像ファイルのパス

        Returns:
            リサイズされた画像
        """
        try:
            img = Image.open(image_path)
            # アスペクト比を保ちながらリサイズ
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            print(f"⚠️  画像読み込みエラー: {e}")
            return None

    def create_gradient_background(self, color1_hex: str, color2_hex: str,
                                   direction: str = 'vertical') -> Image.Image:
        """
        グラデーション背景を生成

        Args:
            color1_hex: 開始色
            color2_hex: 終了色
            direction: 'vertical' or 'horizontal'

        Returns:
            グラデーション画像
        """
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)

        color1 = self.hex_to_rgb(color1_hex)
        color2 = self.hex_to_rgb(color2_hex)

        if direction == 'vertical':
            for y in range(self.height):
                ratio = y / self.height
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        else:  # horizontal
            for x in range(self.width):
                ratio = x / self.width
                r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
                g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
                b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
                draw.line([(x, 0), (x, self.height)], fill=(r, g, b))

        return img

    def create_opening(self, track: str, date_str: str) -> ImageClip:
        """オープニング画像生成（5秒）- AI背景 or グラデーション"""
        # AI背景生成（キャッシュ利用）
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'opening')

        if ai_bg_path:
            # AI背景を使用
            img = self.load_and_resize_background(ai_bg_path)
            # 暗めのオーバーレイで文字を読みやすく
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 100))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            # グラデーション背景生成
            img = self.create_gradient_background(
                self.colors['primary'],
                self.colors['secondary'],
                direction='vertical'
            )

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

    def create_prediction_slide(self, race_info: Dict, prediction: Dict, track: str) -> ImageClip:
        """予想スライド生成（各10秒）- AI背景 or グラデーション"""
        # AI背景生成（キャッシュ利用）
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'race')

        if ai_bg_path:
            # AI背景を使用
            img = self.load_and_resize_background(ai_bg_path)
            # 明るめのオーバーレイで情報を見やすく
            overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 180))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            # 淡いグラデーション背景
            img = self.create_gradient_background('#f5f7fa', '#c3cfe2', direction='vertical')

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

    def create_ending(self, track: str = None) -> ImageClip:
        """エンディング画像生成（5秒）- AI背景 or 単色"""
        # AI背景生成（キャッシュ利用）
        ai_bg_path = None
        if self.use_ai_backgrounds and track:
            ai_bg_path = self.generate_ai_background(track, 'ending')

        if ai_bg_path:
            # AI背景を使用
            img = self.load_and_resize_background(ai_bg_path)
            # 暗めのオーバーレイ
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 120))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            # 単色背景
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

    def generate_video(self, article_data: Dict, output_path: str = None,
                       bgm_path: str = None, enable_narration: bool = True) -> str:
        """
        予想データから動画生成

        Args:
            article_data: daily_prediction.pyで生成された記事データ
            output_path: 出力先パス（省略時は自動生成）
            bgm_path: BGM音声ファイルのパス（省略時はBGMなし）
            enable_narration: ナレーション生成を有効化

        Returns:
            生成された動画ファイルのパス
        """
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f"output/prediction_{date_str}.mp4"

        # 出力ディレクトリ作成
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        clips = []
        narration_files = []  # 一時ファイルの管理用

        # オープニング
        opening_clip = self.create_opening(
            article_data['track'],
            article_data['date']
        )

        # オープニングナレーション
        if enable_narration:
            opening_text = f"{article_data['date']} {article_data['track']}競馬の予想をお届けします"
            narration_path = self.generate_narration(opening_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                opening_clip = opening_clip.set_audio(narration_audio)

        clips.append(opening_clip)

        # 各レースの予想スライド
        for pred_data in article_data['predictions']:
            race_info = pred_data['race']['raceInfo']
            prediction = pred_data['prediction']

            slide_clip = self.create_prediction_slide(race_info, prediction, article_data['track'])

            # レースナレーション
            if enable_narration:
                # 上位3頭の予想を取得
                predictions = sorted(
                    prediction['predictions'],
                    key=lambda x: x['win_probability'],
                    reverse=True
                )[:3]

                narration_text = (
                    f"{race_info['raceNumber']} {race_info['raceName']}。"
                    f"本命は{predictions[0]['number']}番{predictions[0]['name']}、"
                    f"対抗{predictions[1]['number']}番{predictions[1]['name']}、"
                    f"単穴{predictions[2]['number']}番{predictions[2]['name']}です。"
                )

                narration_path = self.generate_narration(narration_text)
                if narration_path:
                    narration_files.append(narration_path)
                    narration_audio = AudioFileClip(narration_path)
                    slide_clip = slide_clip.set_audio(narration_audio)

            clips.append(slide_clip)

        # エンディング
        ending_clip = self.create_ending(article_data['track'])

        if enable_narration:
            ending_text = "詳しい予想は、keiba-ai-predictor.onrender.comをご覧ください"
            narration_path = self.generate_narration(ending_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                ending_clip = ending_clip.set_audio(narration_audio)

        clips.append(ending_clip)

        # 動画結合
        final_video = concatenate_videoclips(clips, method="compose")

        # BGM追加
        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm = AudioFileClip(bgm_path)
                # BGMをループして動画の長さに合わせる
                video_duration = final_video.duration
                if bgm.duration < video_duration:
                    # BGMが短い場合はループ
                    loops = int(video_duration / bgm.duration) + 1
                    bgm = concatenate_videoclips([bgm] * loops)
                bgm = bgm.subclip(0, video_duration).volumex(0.3)  # 音量を30%に

                # 既存のナレーションとBGMを合成
                if final_video.audio:
                    final_audio = CompositeAudioClip([final_video.audio, bgm])
                else:
                    final_audio = bgm

                final_video = final_video.set_audio(final_audio)
                print("✅ BGMを追加しました")
            except Exception as e:
                print(f"⚠️  BGM追加エラー: {e}")

        # 動画書き出し
        final_video.write_videofile(
            output_path,
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            preset='medium'
        )

        # 一時ファイルのクリーンアップ
        for temp_file in narration_files:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

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

    # 環境変数で設定（環境変数で切り替え可能）
    tts_engine = os.environ.get('TTS_ENGINE', 'gtts')  # 'gtts' or 'openai'
    use_ai_bg = os.environ.get('USE_AI_BACKGROUNDS', 'false').lower() == 'true'

    print(f"🎙️  TTS Engine: {tts_engine}")
    print(f"🎨 AI Backgrounds: {use_ai_bg}")

    generator = PredictionVideoGenerator(
        tts_engine=tts_engine,
        use_ai_backgrounds=use_ai_bg
    )

    video_path = generator.generate_video(sample_data, "test_output.mp4")
    print(f"\n✅ 動画ファイル: {video_path}")

    # AI背景を使用した場合のキャッシュ情報
    if use_ai_bg:
        cache_dir = Path('cache/backgrounds')
        if cache_dir.exists():
            cached_files = list(cache_dir.glob('*.png'))
            print(f"📁 キャッシュされた背景画像: {len(cached_files)}枚")
            for f in cached_files:
                print(f"   - {f.name}")
