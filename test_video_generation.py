"""
テスト動画生成スクリプト
日本語フォント・MoviePy動作確認用の5秒動画を生成
"""

from moviepy.editor import ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path


def create_test_video():
    """5秒のテスト動画を生成"""

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print("🎬 テスト動画生成開始...")

    # 画像生成
    img = Image.new('RGB', (1920, 1080), color=(102, 126, 234))  # keiba-ai-predictor primary color
    draw = ImageDraw.Draw(img)

    # フォント設定
    try:
        # macOS
        font_large = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", 120)
        font_small = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 60)
        print("✅ ヒラギノフォント使用")
    except:
        try:
            # Linux (GitHub Actions)
            font_large = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 120)
            font_small = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 60)
            print("✅ Notoフォント使用")
        except:
            # フォールバック
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
            print("⚠️  デフォルトフォント使用（日本語が表示されない可能性）")

    # テキスト描画
    title = "競馬AI予想"
    subtitle = "テスト動画"
    desc = "日本語フォント確認用"

    # タイトル（中央）
    title_bbox = draw.textbbox((0, 0), title, font=font_large)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(
        ((1920 - title_width) // 2, 350),
        title,
        fill=(255, 255, 255),
        font=font_large
    )

    # サブタイトル
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(
        ((1920 - subtitle_width) // 2, 550),
        subtitle,
        fill=(255, 255, 255),
        font=font_small
    )

    # 説明
    desc_bbox = draw.textbbox((0, 0), desc, font=font_small)
    desc_width = desc_bbox[2] - desc_bbox[0]
    draw.text(
        ((1920 - desc_width) // 2, 700),
        desc,
        fill=(255, 255, 255),
        font=font_small
    )

    # 5秒の動画クリップ
    clip = ImageClip(np.array(img)).set_duration(5)

    # 動画書き出し
    output_path = output_dir / "test_video.mp4"
    clip.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio=False,
        preset='medium'
    )

    print(f"✅ テスト動画生成完了: {output_path}")
    print("\n次のステップ:")
    print("1. 動画を再生して日本語が正しく表示されるか確認")
    print("2. YouTube private投稿テスト:")
    print(f"   python -c \"from src.automation.youtube_uploader import YouTubeUploader; u=YouTubeUploader(); print(u.upload_video('{output_path}', 'テスト動画', 'これはテストです', privacy_status='private'))\"")

    return str(output_path)


if __name__ == "__main__":
    create_test_video()
