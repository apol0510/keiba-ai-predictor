"""
毎日の自動化実行スクリプト
GitHub Actionsから呼び出される統合スクリプト
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.automation.daily_prediction import DailyPredictionAutomation
from src.automation.video_generator import PredictionVideoGenerator
from src.automation.youtube_uploader import YouTubeUploader


async def main():
    """
    毎日の自動化フロー
    1. AI予想生成
    2. 記事生成（Markdown）
    3. 動画生成
    4. YouTube投稿
    5. （X投稿はdlvr.itが自動実行）
    """

    print("=" * 60)
    print("🤖 競馬AI予想 毎日自動化スクリプト")
    print("=" * 60)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # ===========================
    # 1. AI予想生成 + 記事生成
    # ===========================
    print("📊 Step 1: AI予想生成")
    print("-" * 60)

    prediction_system = DailyPredictionAutomation(
        api_base_url=os.getenv('API_BASE_URL', 'https://keiba-ai-predictor.onrender.com')
    )

    article = await prediction_system.generate_daily_article(top_n=3)

    if not article['success']:
        print(f"❌ エラー: {article['message']}")
        print("本日のレースデータが見つかりません。処理を終了します。")
        return

    print(f"✅ 記事生成完了")
    print(f"  タイトル: {article['title']}")
    print(f"  レース数: {len(article['predictions'])}")
    print(f"  競馬場: {article['track']}\n")

    # 記事をファイルに保存（CMS連携用）
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    article_path = output_dir / f"article_{article['date']}.md"
    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(article['content'])

    print(f"✅ 記事保存: {article_path}\n")

    # ===========================
    # 2. 動画生成
    # ===========================
    print("🎬 Step 2: 予想動画生成")
    print("-" * 60)

    video_gen = PredictionVideoGenerator()
    video_path = video_gen.generate_video(
        article,
        output_path=str(output_dir / f"prediction_{article['date']}.mp4")
    )

    print(f"✅ 動画生成完了: {video_path}\n")

    # ===========================
    # 3. YouTube投稿
    # ===========================
    print("📺 Step 3: YouTube投稿")
    print("-" * 60)

    # YouTube認証情報チェック
    youtube_creds = os.getenv('YOUTUBE_CREDENTIALS_PATH', 'credentials/youtube_credentials.json')

    if not os.path.exists(youtube_creds):
        print(f"⚠️  YouTube認証情報が見つかりません: {youtube_creds}")
        print("  動画ファイルは生成されましたが、YouTube投稿はスキップします。")
        print(f"  手動でアップロードしてください: {video_path}\n")
    else:
        try:
            uploader = YouTubeUploader(credentials_file=youtube_creds)

            youtube_url = uploader.upload_video(
                video_path=video_path,
                title=f"【AI競馬予想】{article['date']} {article['track']}競馬 注目レース",
                description=article['summary'],
                tags=['競馬', 'AI予想', article['track'], '南関東競馬', '地方競馬', '機械学習']
            )

            if youtube_url:
                print(f"✅ YouTube投稿完了: {youtube_url}\n")
            else:
                print("❌ YouTube投稿失敗\n")

        except Exception as e:
            print(f"❌ YouTube投稿エラー: {e}\n")

    # ===========================
    # 4. X投稿（RSS連携）
    # ===========================
    print("🐦 Step 4: X（Twitter）投稿")
    print("-" * 60)
    print("✅ dlvr.it が RSS を検知して自動投稿します")
    print("  （記事がCMSに公開されると自動的に投稿されます）\n")

    # ===========================
    # 完了サマリー
    # ===========================
    print("=" * 60)
    print("✅ 自動化フロー完了")
    print("=" * 60)
    print(f"📄 記事: {article_path}")
    print(f"🎬 動画: {video_path}")
    print(f"🔗 サイト: https://keiba-ai-predictor.onrender.com")
    print("=" * 60)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  処理が中断されました")
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        raise
