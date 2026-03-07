"""
YouTube最適化AI競馬予想動画生成
通常動画（90秒）+ Shorts（30秒）同時生成
"""

from moviepy.editor import (
    ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip, CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
import os
from pathlib import Path
from video_generator import PredictionVideoGenerator
from youtube_metadata_generator import YouTubeMetadataGenerator
import json


class YouTubeFormatGenerator(PredictionVideoGenerator):
    """YouTube最適化動画生成（通常 + Shorts）"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Shorts用の縦型サイズ
        self.shorts_width = 1080
        self.shorts_height = 1920

    def create_hook_slide(self, track: str, race_count: int) -> ImageClip:
        """
        フック（3秒）- 最初の3秒で視聴者を掴む

        Args:
            track: 競馬場名
            race_count: レース数
        """
        # AI背景
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'opening')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            # 暗めのオーバーレイで文字を目立たせる
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 150))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = self.create_gradient_background(
                self.colors['primary'],
                self.colors['secondary'],
                direction='vertical'
            )

        draw = ImageDraw.Draw(img)

        # フォント
        title_font = self.find_japanese_font(150, weight='bold')
        subtitle_font = self.find_japanese_font(90, weight='bold')

        # メインタイトル
        title_text = "本日の注目レース"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 350),
            title_text,
            fill=self.hex_to_rgb('#FFD700'),  # ゴールド
            font=title_font
        )

        # サブタイトル
        subtitle = f"{track}競馬 AI予想{race_count}レース"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(
            ((self.width - subtitle_width) // 2, 550),
            subtitle,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        return ImageClip(np.array(img)).set_duration(3)

    def create_attention_slide(self, track: str, date_str: str) -> ImageClip:
        """
        今日の注目（5秒）
        """
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'race')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 130))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = self.create_gradient_background('#1a1a2e', '#16213e', direction='vertical')

        draw = ImageDraw.Draw(img)

        # フォント
        title_font = self.find_japanese_font(100, weight='bold')
        date_font = self.find_japanese_font(70, weight='regular')

        # タイトル
        title_text = f"{track}競馬 今日の注目"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 400),
            title_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=title_font
        )

        # 日付
        date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
        date_width = date_bbox[2] - date_bbox[0]
        draw.text(
            ((self.width - date_width) // 2, 550),
            date_str,
            fill=self.hex_to_rgb('#FFD700'),
            font=date_font
        )

        return ImageClip(np.array(img)).set_duration(5)

    def create_race_slide_optimized(self, race_info: Dict, prediction: Dict,
                                    track: str, duration: int = 15) -> ImageClip:
        """
        レーススライド（15秒）- YouTube最適化版
        """
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'race')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 200))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = self.create_gradient_background('#f5f7fa', '#c3cfe2', direction='vertical')

        draw = ImageDraw.Draw(img)

        # フォント（より大きく）
        race_font = self.find_japanese_font(100, weight='bold')
        horse_font = self.find_japanese_font(90, weight='bold')
        detail_font = self.find_japanese_font(60, weight='regular')

        # レース情報ヘッダー
        header_rect = [(0, 0), (self.width, 250)]
        draw.rectangle(header_rect, fill=self.hex_to_rgb(self.colors['primary']))

        race_title = f"{race_info['raceNumber']} {race_info['raceName']}"
        draw.text((80, 50), race_title, fill=self.hex_to_rgb(self.colors['white']), font=race_font)

        race_details = f"{race_info['distance']}m {race_info['surface']}"
        draw.text((80, 160), race_details, fill=self.hex_to_rgb(self.colors['white']), font=detail_font)

        # 予想（本命のみ大きく表示）
        predictions = sorted(
            prediction['predictions'],
            key=lambda x: x['win_probability'],
            reverse=True
        )[:3]

        y_pos = 400

        # 本命（特大表示）
        honmei = predictions[0]
        mark_font = self.find_japanese_font(120, weight='bold')
        draw.text((100, y_pos), '◎', fill=self.hex_to_rgb('#FF4444'), font=mark_font)

        horse_text = f"{honmei['number']}番 {honmei['name']}"
        draw.text((250, y_pos), horse_text, fill=self.hex_to_rgb(self.colors['black']), font=horse_font)

        prob_text = f"{honmei['win_probability']*100:.1f}%"
        draw.text((1450, y_pos), prob_text, fill=self.hex_to_rgb('#FF4444'), font=horse_font)

        y_pos += 180

        # 対抗・単穴（小さめ）
        marks = ['○', '▲']
        small_font = self.find_japanese_font(70, weight='bold')
        for idx, (mark, pred) in enumerate(zip(marks, predictions[1:3])):
            draw.text((100, y_pos), mark, fill=self.hex_to_rgb(self.colors['primary']), font=small_font)

            horse_text = f"{pred['number']}番 {pred['name']}"
            draw.text((220, y_pos), horse_text, fill=self.hex_to_rgb(self.colors['black']), font=small_font)

            prob_text = f"{pred['win_probability']*100:.1f}%"
            draw.text((1500, y_pos), prob_text, fill=self.hex_to_rgb(self.colors['primary']), font=small_font)

            y_pos += 120

        return ImageClip(np.array(img)).set_duration(duration)

    def create_cta_slide(self, track: str) -> ImageClip:
        """
        CTA（10秒）- 概要欄への誘導
        """
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'ending')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 140))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = Image.new('RGB', (self.width, self.height),
                            color=self.hex_to_rgb(self.colors['secondary']))

        draw = ImageDraw.Draw(img)

        # フォント
        title_font = self.find_japanese_font(110, weight='bold')
        subtitle_font = self.find_japanese_font(75, weight='bold')

        # CTA
        cta_text = "詳細予想は概要欄から"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=title_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
        draw.text(
            ((self.width - cta_width) // 2, 350),
            cta_text,
            fill=self.hex_to_rgb('#FFD700'),
            font=title_font
        )

        # URL
        url_text = "keiba-ai-predictor.onrender.com"
        url_bbox = draw.textbbox((0, 0), url_text, font=subtitle_font)
        url_width = url_bbox[2] - url_bbox[0]
        draw.text(
            ((self.width - url_width) // 2, 520),
            url_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        # チャンネル登録誘導
        sub_text = "👍 高評価 & チャンネル登録"
        sub_bbox = draw.textbbox((0, 0), sub_text, font=subtitle_font)
        sub_width = sub_bbox[2] - sub_bbox[0]
        draw.text(
            ((self.width - sub_width) // 2, 680),
            sub_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        return ImageClip(np.array(img)).set_duration(10)

    def generate_youtube_video(self, article_data: Dict, output_path: str = None,
                               bgm_path: str = None, top_n_races: int = 3) -> str:
        """
        YouTube最適化動画生成（70-90秒）

        構成:
        1. フック（3秒）
        2. 今日の注目（5秒）
        3. レース1（15秒）
        4. レース2（15秒）
        5. レース3（15秒）
        6. CTA（10秒）

        Args:
            article_data: 予想データ
            output_path: 出力先
            bgm_path: BGMファイル
            top_n_races: 表示するレース数（デフォルト3）
        """
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f"output/youtube_{date_str}.mp4"

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        clips = []
        narration_files = []

        # 1. フック（3秒）
        hook_clip = self.create_hook_slide(article_data['track'], top_n_races)
        # ナレーション追加（gTTS or OpenAI TTS）
        hook_text = f"本日の{article_data['track']}競馬、AIが注目する{top_n_races}レースを紹介します"
        narration_path = self.generate_narration(hook_text)
        if narration_path:
            narration_files.append(narration_path)
            narration_audio = AudioFileClip(narration_path)
            hook_clip = hook_clip.set_audio(narration_audio)
        clips.append(hook_clip)

        # 2. 今日の注目（5秒）
        attention_clip = self.create_attention_slide(article_data['track'], article_data['date'])
        # ナレーション追加（gTTS or OpenAI TTS）
        attention_text = f"今日の注目は{article_data['track']}競馬。AIが期待するレースはこちらです"
        narration_path = self.generate_narration(attention_text)
        if narration_path:
            narration_files.append(narration_path)
            narration_audio = AudioFileClip(narration_path)
            attention_clip = attention_clip.set_audio(narration_audio)
        clips.append(attention_clip)

        # 3-5. レース紹介（音声の長さに自動調整）
        for i, pred_data in enumerate(article_data['predictions'][:top_n_races]):
            race_info = pred_data['race']['raceInfo']
            prediction = pred_data['prediction']

            # ナレーション生成
            predictions = sorted(
                prediction['predictions'],
                key=lambda x: x['win_probability'],
                reverse=True
            )[:3]

            race_text = (
                f"{race_info['raceNumber']} {race_info['raceName']}。"
                f"本命は{predictions[0]['number']}番{predictions[0]['name']}。"
                f"対抗{predictions[1]['number']}番{predictions[1]['name']}、"
                f"単穴{predictions[2]['number']}番{predictions[2]['name']}です"
            )

            narration_path = self.generate_narration(race_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)

                # 音声の長さ + 0.5秒バッファでスライド時間を自動調整
                duration = narration_audio.duration + 0.5
                race_clip = self.create_race_slide_optimized(
                    race_info, prediction, article_data['track'], duration=duration
                )
                race_clip = race_clip.set_audio(narration_audio)
            else:
                # ナレーション失敗時のフォールバック
                race_clip = self.create_race_slide_optimized(
                    race_info, prediction, article_data['track'], duration=10
                )

            clips.append(race_clip)

        # 6. CTA（10秒）
        cta_clip = self.create_cta_slide(article_data['track'])
        # ナレーション追加（gTTS or OpenAI TTS）
        cta_text = "AI予想の詳細は概要欄から確認できます。チャンネル登録もよろしくお願いします"
        narration_path = self.generate_narration(cta_text)
        if narration_path:
            narration_files.append(narration_path)
            narration_audio = AudioFileClip(narration_path)
            cta_clip = cta_clip.set_audio(narration_audio)
        clips.append(cta_clip)

        # 動画結合
        final_video = concatenate_videoclips(clips, method="compose")

        # BGM追加
        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm = AudioFileClip(bgm_path)
                video_duration = final_video.duration
                if bgm.duration < video_duration:
                    loops = int(video_duration / bgm.duration) + 1
                    bgm = concatenate_videoclips([bgm] * loops)
                bgm = bgm.subclip(0, video_duration).volumex(0.25)  # BGM音量25%

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

        # クリーンアップ
        for temp_file in narration_files:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

        print(f"✅ YouTube動画生成完了: {output_path}")
        print(f"   合計時間: {final_video.duration:.1f}秒")
        return output_path

    def generate_shorts(self, article_data: Dict, race_index: int = 0,
                       output_path: str = None, bgm_path: str = None) -> str:
        """
        YouTube Shorts生成（30秒・縦型 1080x1920）

        構成:
        1. フック（3秒）
        2. レース情報（20秒）
        3. CTA（7秒）

        Args:
            article_data: 予想データ
            race_index: 使用するレースのインデックス
            output_path: 出力先
            bgm_path: BGMファイル
        """
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f"output/shorts_{date_str}.mp4"

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        # Shorts用に一時的にサイズ変更
        original_width = self.width
        original_height = self.height
        self.width = self.shorts_width
        self.height = self.shorts_height

        clips = []
        narration_files = []

        try:
            pred_data = article_data['predictions'][race_index]
            race_info = pred_data['race']['raceInfo']
            prediction = pred_data['prediction']

            # 予想トップ3を取得
            predictions = sorted(
                prediction['predictions'],
                key=lambda x: x['win_probability'],
                reverse=True
            )[:3]

            # 1. フック（インパクトある導入）- Shorts用
            hook_clip = self._create_shorts_hook(article_data['track'], race_info['raceNumber'])
            hook_text = (
                f"今日の{article_data['track']}競馬、{race_info['raceNumber']}、"
                f"{race_info['raceName']}。AIが選んだ本命は！"
            )
            narration_path = self.generate_narration(hook_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                # 音声に合わせてスライド時間を自動調整
                hook_clip = hook_clip.set_duration(narration_audio.duration + 0.3)
                hook_clip = hook_clip.set_audio(narration_audio)
            clips.append(hook_clip)

            # 2. レース情報（具体的な予想）- Shorts用
            race_clip = self._create_shorts_race_detail(race_info, prediction, article_data['track'])
            race_text = (
                f"{predictions[0]['number']}番、{predictions[0]['name']}！"
                f"勝率は{predictions[0]['win_probability']*100:.0f}パーセント。"
                f"対抗に{predictions[1]['number']}番、{predictions[1]['name']}。"
                f"穴馬は{predictions[2]['number']}番、{predictions[2]['name']}を狙います。"
            )

            narration_path = self.generate_narration(race_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                # 音声に合わせてスライド時間を自動調整
                race_clip = race_clip.set_duration(narration_audio.duration + 0.5)
                race_clip = race_clip.set_audio(narration_audio)
            clips.append(race_clip)

            # 3. CTA（自然な締めくくり）- Shorts用
            cta_clip = self._create_shorts_cta(article_data['track'])
            cta_text = "詳しい買い目は概要欄をチェック。チャンネル登録で毎日の予想をお届けします！"
            narration_path = self.generate_narration(cta_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                # 音声に合わせてスライド時間を自動調整
                cta_clip = cta_clip.set_duration(narration_audio.duration + 0.3)
                cta_clip = cta_clip.set_audio(narration_audio)
            clips.append(cta_clip)

            # 動画結合
            final_video = concatenate_videoclips(clips, method="compose")

            # BGM追加
            if bgm_path and os.path.exists(bgm_path):
                try:
                    bgm = AudioFileClip(bgm_path)
                    video_duration = final_video.duration
                    if bgm.duration < video_duration:
                        loops = int(video_duration / bgm.duration) + 1
                        bgm = concatenate_videoclips([bgm] * loops)
                    bgm = bgm.subclip(0, video_duration).volumex(0.2)  # BGM音量20%

                    if final_video.audio:
                        final_audio = CompositeAudioClip([final_video.audio, bgm])
                    else:
                        final_audio = bgm

                    final_video = final_video.set_audio(final_audio)
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

            # クリーンアップ
            for temp_file in narration_files:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

            print(f"✅ Shorts生成完了: {output_path}")
            print(f"   サイズ: {self.shorts_width}x{self.shorts_height}")
            print(f"   合計時間: {final_video.duration:.1f}秒")
            return output_path

        finally:
            # サイズを元に戻す
            self.width = original_width
            self.height = original_height

    def _create_shorts_hook(self, track: str, race_number: str) -> ImageClip:
        """Shorts用フック（3秒）"""
        img = self.create_gradient_background('#FF4444', '#CC0000', direction='vertical')
        draw = ImageDraw.Draw(img)

        title_font = self.find_japanese_font(140, weight='bold')
        subtitle_font = self.find_japanese_font(100, weight='bold')

        # タイトル
        title_text = f"{track}競馬"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 600),
            title_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=title_font
        )

        # レース番号
        race_text = f"{race_number} AI予想"
        race_bbox = draw.textbbox((0, 0), race_text, font=subtitle_font)
        race_width = race_bbox[2] - race_bbox[0]
        draw.text(
            ((self.width - race_width) // 2, 800),
            race_text,
            fill=self.hex_to_rgb('#FFD700'),
            font=subtitle_font
        )

        return ImageClip(np.array(img)).set_duration(3)

    def _create_shorts_race_detail(self, race_info: Dict, prediction: Dict, track: str) -> ImageClip:
        """Shorts用レース詳細（20秒）"""
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'race')

        if ai_bg_path:
            # 縦型にクロップ
            bg_img = Image.open(ai_bg_path)
            # 中央をクロップ
            left = (bg_img.width - self.width) // 2
            bg_img = bg_img.crop((left, 0, left + self.width, self.height))
            img = bg_img
            overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 210))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = Image.new('RGB', (self.width, self.height), color=self.hex_to_rgb('#f5f7fa'))

        draw = ImageDraw.Draw(img)

        # フォント
        race_font = self.find_japanese_font(90, weight='bold')
        horse_font = self.find_japanese_font(100, weight='bold')
        mark_font = self.find_japanese_font(140, weight='bold')

        # レース情報ヘッダー
        header_rect = [(0, 100), (self.width, 350)]
        draw.rectangle(header_rect, fill=self.hex_to_rgb(self.colors['primary']))

        race_title = race_info['raceName']
        race_bbox = draw.textbbox((0, 0), race_title, font=race_font)
        race_width = race_bbox[2] - race_bbox[0]
        draw.text(
            ((self.width - race_width) // 2, 170),
            race_title,
            fill=self.hex_to_rgb(self.colors['white']),
            font=race_font
        )

        race_detail = f"{race_info['distance']}m {race_info['surface']}"
        detail_bbox = draw.textbbox((0, 0), race_detail, font=race_font)
        detail_width = detail_bbox[2] - detail_bbox[0]
        draw.text(
            ((self.width - detail_width) // 2, 260),
            race_detail,
            fill=self.hex_to_rgb(self.colors['white']),
            font=race_font
        )

        # 予想（縦に並べる）
        predictions = sorted(
            prediction['predictions'],
            key=lambda x: x['win_probability'],
            reverse=True
        )[:3]

        y_pos = 500
        marks = ['◎', '○', '▲']
        colors = ['#FF4444', '#4444FF', '#44CC44']

        for mark, color, pred in zip(marks, colors, predictions):
            # マーク
            mark_bbox = draw.textbbox((0, 0), mark, font=mark_font)
            mark_width = mark_bbox[2] - mark_bbox[0]
            draw.text(
                ((self.width - mark_width) // 2, y_pos),
                mark,
                fill=self.hex_to_rgb(color),
                font=mark_font
            )

            # 馬名
            horse_text = f"{pred['number']}番 {pred['name']}"
            horse_bbox = draw.textbbox((0, 0), horse_text, font=horse_font)
            horse_width = horse_bbox[2] - horse_bbox[0]
            draw.text(
                ((self.width - horse_width) // 2, y_pos + 160),
                horse_text,
                fill=self.hex_to_rgb(self.colors['black']),
                font=horse_font
            )

            # 勝率
            prob_font = self.find_japanese_font(80, weight='bold')
            prob_text = f"{pred['win_probability']*100:.1f}%"
            prob_bbox = draw.textbbox((0, 0), prob_text, font=prob_font)
            prob_width = prob_bbox[2] - prob_bbox[0]
            draw.text(
                ((self.width - prob_width) // 2, y_pos + 280),
                prob_text,
                fill=self.hex_to_rgb(color),
                font=prob_font
            )

            y_pos += 400

        return ImageClip(np.array(img)).set_duration(20)

    def _create_shorts_cta(self, track: str) -> ImageClip:
        """Shorts用CTA（7秒）"""
        img = self.create_gradient_background(self.colors['secondary'], '#1a1a2e', direction='vertical')
        draw = ImageDraw.Draw(img)

        title_font = self.find_japanese_font(100, weight='bold')
        subtitle_font = self.find_japanese_font(70, weight='bold')

        # CTA
        cta_text = "📺 チャンネル登録"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=title_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
        draw.text(
            ((self.width - cta_width) // 2, 700),
            cta_text,
            fill=self.hex_to_rgb('#FFD700'),
            font=title_font
        )

        # サブ
        sub_text = "毎日のAI予想をお届け"
        sub_bbox = draw.textbbox((0, 0), sub_text, font=subtitle_font)
        sub_width = sub_bbox[2] - sub_bbox[0]
        draw.text(
            ((self.width - sub_width) // 2, 900),
            sub_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        return ImageClip(np.array(img)).set_duration(7)

    def generate_both(self, article_data: Dict, bgm_path: str = None,
                     youtube_output: str = None, shorts_output: str = None) -> tuple:
        """
        通常動画とShortsを同時生成

        Returns:
            (youtube_path, shorts_path)のタプル
        """
        print("=" * 60)
        print("🎬 YouTube最強フォーマット - 同時生成開始")
        print("=" * 60)

        # 通常動画生成
        print("\n📺 通常動画（70-90秒）生成中...")
        youtube_path = self.generate_youtube_video(
            article_data,
            output_path=youtube_output,
            bgm_path=bgm_path
        )

        # Shorts生成（一番注目のレース）
        print("\n📱 Shorts（30秒・縦型）生成中...")
        shorts_path = self.generate_shorts(
            article_data,
            race_index=0,  # 最初のレース（一番注目）
            output_path=shorts_output,
            bgm_path=bgm_path
        )

        print("\n" + "=" * 60)
        print("✅ 同時生成完了！")
        print("=" * 60)
        print(f"📺 通常動画: {youtube_path}")
        print(f"📱 Shorts: {shorts_path}")
        print("\n💡 使い方:")
        print("  1. Shortsを先に投稿（短期間で多くの再生）")
        print("  2. 概要欄に通常動画のリンクを貼る")
        print("  3. Shortsから通常動画へ流入")
        print("=" * 60)

        return youtube_path, shorts_path

    def generate_full_version(self, article_data: Dict, output_path: str = None,
                              bgm_path: str = None) -> str:
        """
        長編動画生成（全12レース・8-12分）

        構成:
        1. オープニング（10秒）
        2. 本日のポイント（30秒）
        3. 1R-12R（各20-25秒）
        4. まとめ（30秒）

        Args:
            article_data: 予想データ
            output_path: 出力先
            bgm_path: BGMファイル
        """
        if output_path is None:
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f"output/full_version_{date_str}.mp4"

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

        clips = []
        narration_files = []
        total_races = len(article_data['predictions'])

        # 1. オープニング（10秒）
        opening_clip = self._create_full_opening(article_data['track'], article_data['date'], total_races)
        if self.tts_engine == 'openai' and self.openai_client:
            opening_text = f"{article_data['date']} {article_data['track']}競馬、全{total_races}レースのAI予想をお届けします"
            narration_path = self.generate_narration(opening_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                opening_clip = opening_clip.set_audio(narration_audio)
        clips.append(opening_clip)

        # 2. 本日のポイント（30秒）
        point_clip = self._create_today_point(article_data['track'], article_data['predictions'][:3])
        if self.tts_engine == 'openai' and self.openai_client:
            point_text = "本日の特に注目すべきレースは、"
            for i, pred_data in enumerate(article_data['predictions'][:3]):
                race_num = pred_data['race']['raceInfo']['raceNumber']
                point_text += f"{race_num}、"
            point_text += "の3つです。それでは、各レースの予想を見ていきましょう。"

            narration_path = self.generate_narration(point_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                point_clip = point_clip.set_audio(narration_audio)
        clips.append(point_clip)

        # 3. 各レース（10-15秒に短縮）
        for i, pred_data in enumerate(article_data['predictions']):
            race_info = pred_data['race']['raceInfo']
            prediction = pred_data['prediction']

            # ナレーション生成（音声の長さに合わせてスライド時間を自動調整）
            if self.tts_engine == 'openai' and self.openai_client:
                predictions = sorted(
                    prediction['predictions'],
                    key=lambda x: x['win_probability'],
                    reverse=True
                )[:3]

                race_text = (
                    f"{race_info['raceNumber']} {race_info['raceName']}。"
                    f"本命は{predictions[0]['number']}番、{predictions[0]['name']}。"
                    f"対抗は{predictions[1]['number']}番、{predictions[1]['name']}。"
                    f"単穴は{predictions[2]['number']}番、{predictions[2]['name']}です。"
                )

                narration_path = self.generate_narration(race_text)
                if narration_path:
                    narration_files.append(narration_path)
                    narration_audio = AudioFileClip(narration_path)

                    # 音声の長さ + 0.5秒のバッファでスライド時間を自動調整
                    audio_duration = narration_audio.duration
                    duration = audio_duration + 0.5

                    race_clip = self.create_race_slide_optimized(
                        race_info, prediction, article_data['track'], duration=duration
                    )
                    race_clip = race_clip.set_audio(narration_audio)
                else:
                    # ナレーション生成失敗時のフォールバック
                    race_clip = self.create_race_slide_optimized(
                        race_info, prediction, article_data['track'], duration=8
                    )
            else:
                # TTSなしの場合
                race_clip = self.create_race_slide_optimized(
                    race_info, prediction, article_data['track'], duration=8
                )

            clips.append(race_clip)

        # 4. まとめ（30秒）
        summary_clip = self._create_summary(article_data['track'])
        if self.tts_engine == 'openai' and self.openai_client:
            summary_text = (
                "以上、本日の全レース予想でした。"
                "詳しい買い目やオッズ情報は概要欄のリンクからご確認ください。"
                "チャンネル登録して、明日の予想もお楽しみに"
            )
            narration_path = self.generate_narration(summary_text)
            if narration_path:
                narration_files.append(narration_path)
                narration_audio = AudioFileClip(narration_path)
                summary_clip = summary_clip.set_audio(narration_audio)
        clips.append(summary_clip)

        # 動画結合
        final_video = concatenate_videoclips(clips, method="compose")

        # BGM追加
        if bgm_path and os.path.exists(bgm_path):
            try:
                bgm = AudioFileClip(bgm_path)
                video_duration = final_video.duration
                if bgm.duration < video_duration:
                    loops = int(video_duration / bgm.duration) + 1
                    bgm = concatenate_videoclips([bgm] * loops)
                bgm = bgm.subclip(0, video_duration).volumex(0.20)  # BGM音量20%

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

        # クリーンアップ
        for temp_file in narration_files:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

        print(f"✅ 長編動画生成完了: {output_path}")
        print(f"   合計時間: {final_video.duration:.1f}秒 ({final_video.duration/60:.1f}分)")
        return output_path

    def _create_full_opening(self, track: str, date_str: str, race_count: int) -> ImageClip:
        """長編動画オープニング（10秒）"""
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'opening')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 140))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = self.create_gradient_background(
                self.colors['primary'],
                self.colors['secondary'],
                direction='vertical'
            )

        draw = ImageDraw.Draw(img)

        # フォント
        title_font = self.find_japanese_font(140, weight='bold')
        subtitle_font = self.find_japanese_font(90, weight='bold')
        date_font = self.find_japanese_font(70, weight='regular')

        # タイトル
        title_text = "全レースAI予想"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 300),
            title_text,
            fill=self.hex_to_rgb('#FFD700'),
            font=title_font
        )

        # 競馬場
        track_text = f"{track}競馬 {race_count}レース"
        track_bbox = draw.textbbox((0, 0), track_text, font=subtitle_font)
        track_width = track_bbox[2] - track_bbox[0]
        draw.text(
            ((self.width - track_width) // 2, 480),
            track_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        # 日付
        date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
        date_width = date_bbox[2] - date_bbox[0]
        draw.text(
            ((self.width - date_width) // 2, 620),
            date_str,
            fill=self.hex_to_rgb(self.colors['white']),
            font=date_font
        )

        return ImageClip(np.array(img)).set_duration(10)

    def _create_today_point(self, track: str, top_races: List[Dict]) -> ImageClip:
        """本日のポイント（30秒）"""
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'race')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 130))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = self.create_gradient_background('#1a1a2e', '#16213e', direction='vertical')

        draw = ImageDraw.Draw(img)

        # フォント
        title_font = self.find_japanese_font(100, weight='bold')
        race_font = self.find_japanese_font(80, weight='bold')

        # タイトル
        title_text = "本日の注目レース"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 300),
            title_text,
            fill=self.hex_to_rgb('#FFD700'),
            font=title_font
        )

        # 注目レース番号
        y_pos = 500
        for pred_data in top_races:
            race_num = pred_data['race']['raceInfo']['raceNumber']
            race_name = pred_data['race']['raceInfo']['raceName']

            race_text = f"⭐ {race_num} {race_name}"
            draw.text((200, y_pos), race_text, fill=self.hex_to_rgb(self.colors['white']), font=race_font)
            y_pos += 120

        return ImageClip(np.array(img)).set_duration(30)

    def _create_summary(self, track: str) -> ImageClip:
        """まとめ（30秒）"""
        ai_bg_path = None
        if self.use_ai_backgrounds:
            ai_bg_path = self.generate_ai_background(track, 'ending')

        if ai_bg_path:
            img = self.load_and_resize_background(ai_bg_path)
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 150))
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay).convert('RGB')
        else:
            img = Image.new('RGB', (self.width, self.height),
                            color=self.hex_to_rgb(self.colors['secondary']))

        draw = ImageDraw.Draw(img)

        # フォント
        title_font = self.find_japanese_font(110, weight='bold')
        subtitle_font = self.find_japanese_font(75, weight='bold')

        # タイトル
        title_text = "詳細予想は概要欄から"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 320),
            title_text,
            fill=self.hex_to_rgb('#FFD700'),
            font=title_font
        )

        # URL
        url_text = "keiba-ai-predictor.onrender.com"
        url_bbox = draw.textbbox((0, 0), url_text, font=subtitle_font)
        url_width = url_bbox[2] - url_bbox[0]
        draw.text(
            ((self.width - url_width) // 2, 490),
            url_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        # CTA
        cta_text = "👍 高評価 & チャンネル登録"
        cta_bbox = draw.textbbox((0, 0), cta_text, font=subtitle_font)
        cta_width = cta_bbox[2] - cta_bbox[0]
        draw.text(
            ((self.width - cta_width) // 2, 650),
            cta_text,
            fill=self.hex_to_rgb(self.colors['white']),
            font=subtitle_font
        )

        return ImageClip(np.array(img)).set_duration(30)

    def generate_all_formats(self, article_data: Dict, bgm_path: str = None,
                            generate_metadata: bool = True) -> dict:
        """
        全フォーマット同時生成（Shorts + 通常 + 長編 + メタデータ + サムネイル）

        Args:
            article_data: 予想データ
            bgm_path: BGMファイルパス
            generate_metadata: メタデータ・サムネイル生成するか

        Returns:
            {
                'videos': {
                    'shorts': shorts_path,
                    'youtube': youtube_path,
                    'full': full_path
                },
                'metadata': {
                    'shorts': {'title': ..., 'description': ..., 'tags': [...]},
                    'youtube': {...},
                    'full': {...}
                },
                'thumbnails': {
                    'shorts': thumb_path,
                    'youtube': thumb_path,
                    'full': thumb_path
                }
            }
        """
        print("\n" + "=" * 70)
        print("🚀 YouTube動画生成システム - 3階層同時生成")
        print("=" * 70)

        date_str = datetime.now().strftime('%Y%m%d')
        results = {
            'videos': {},
            'metadata': {},
            'thumbnails': {}
        }

        # 1. Shorts生成
        print("\n📱 [1/3] Shorts（30秒・縦型）生成中...")
        results['videos']['shorts'] = self.generate_shorts(
            article_data,
            race_index=0,
            output_path=f"output/shorts_{date_str}.mp4",
            bgm_path=bgm_path
        )

        # 2. 通常動画生成
        print("\n📺 [2/3] 通常動画（70-90秒）生成中...")
        results['videos']['youtube'] = self.generate_youtube_video(
            article_data,
            output_path=f"output/youtube_{date_str}.mp4",
            bgm_path=bgm_path
        )

        # 3. 長編動画生成
        print("\n🎬 [3/3] 長編動画（8-12分・全レース）生成中...")
        results['videos']['full'] = self.generate_full_version(
            article_data,
            output_path=f"output/full_version_{date_str}.mp4",
            bgm_path=bgm_path
        )

        # 4. メタデータ・サムネイル生成
        if generate_metadata:
            print("\n📊 [4/6] メタデータ生成中...")
            metadata_gen = YouTubeMetadataGenerator()

            # メタデータ生成（動画URL相互リンク）
            # Note: YouTubeアップロード後に実際のURLで更新する想定
            results['metadata'] = metadata_gen.generate_all_metadata(article_data)

            # メタデータをJSONファイルに保存
            metadata_path = f"output/metadata_{date_str}.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(results['metadata'], f, ensure_ascii=False, indent=2)
            print(f"✅ メタデータ保存: {metadata_path}")

            # 5. サムネイル生成
            print("\n🖼️  [5/6] サムネイル生成中...")
            for video_type in ['shorts', 'youtube', 'full']:
                thumb_path = f"output/thumbnail_{video_type}_{date_str}.png"
                results['thumbnails'][video_type] = metadata_gen.generate_thumbnail(
                    video_type,
                    article_data,
                    thumb_path,
                    font_finder=self.find_japanese_font
                )

        print("\n" + "=" * 70)
        print("✅ 3階層動画生成完了！")
        print("=" * 70)
        print(f"\n📱 Shorts:    {results['videos']['shorts']}")
        print(f"📺 通常動画:  {results['videos']['youtube']}")
        print(f"🎬 長編動画:  {results['videos']['full']}")

        if generate_metadata:
            print(f"\n📊 メタデータ:")
            for video_type in ['shorts', 'youtube', 'full']:
                print(f"\n【{video_type.upper()}】")
                print(f"タイトル: {results['metadata'][video_type]['title']}")
                print(f"サムネイル: {results['thumbnails'][video_type]}")

        print("\n💡 YouTube戦略:")
        print("  1. Shorts → 拡散・新規獲得")
        print("  2. 通常動画 → 中間層・SEO")
        print("  3. 長編動画 → コアファン・滞在時間")
        print("  4. 概要欄で相互リンク → チャンネル成長加速")
        print("=" * 70)

        return results


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
                        {'number': 4, 'name': 'テストホース', 'win_probability': 0.35},
                        {'number': 7, 'name': 'サンプル', 'win_probability': 0.25},
                        {'number': 2, 'name': 'データ', 'win_probability': 0.18}
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

    tts_engine = os.environ.get('TTS_ENGINE', 'gtts')
    use_ai_bg = os.environ.get('USE_AI_BACKGROUNDS', 'false').lower() == 'true'

    print(f"🎙️  TTS Engine: {tts_engine}")
    print(f"🎨 AI Backgrounds: {use_ai_bg}")
    print(f"🎬 YouTube最適化フォーマット（70-90秒）")

    generator = YouTubeFormatGenerator(
        tts_engine=tts_engine,
        use_ai_backgrounds=use_ai_bg
    )

    # 通常動画とShortsを同時生成
    youtube_path, shorts_path = generator.generate_both(
        sample_data,
        youtube_output="output/youtube_format.mp4",
        shorts_output="output/shorts_format.mp4"
    )
