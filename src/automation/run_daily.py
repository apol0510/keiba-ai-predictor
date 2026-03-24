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
from src.automation.publish_state import (
    already_uploaded,
    mark_uploaded,
    mark_article_published,
    mark_video_generated,
    get_upload_info
)


async def main():
    """
    毎日の自動化フロー（部分成功対応）
    1. AI予想生成 + 記事生成
    2. 動画生成
    3. YouTube投稿
    4. X投稿（RSS経由 - dlvr.it）

    各工程は独立して成功/失敗を記録
    """

    print("=" * 60)
    print("🤖 競馬AI予想 毎日自動化スクリプト")
    print("=" * 60)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 一意キー生成（日付 + 対象 + モード）
    today_str = datetime.now().strftime('%Y-%m-%d')
    target_track = os.getenv('TARGET_TRACK', 'nankan')  # nankan, ooi, kawasaki等
    run_mode = os.getenv('RUN_MODE', 'prod')  # prod, test
    publish_key = f"{today_str}-{target_track}-{run_mode}"

    # 既に投稿済みかチェック
    if already_uploaded(publish_key):
        existing_info = get_upload_info(publish_key)
        print(f"⚠️  このキーはすでに投稿済みです: {publish_key}")
        print(f"  YouTube URL: {existing_info.get('youtube_url')}")
        print(f"  投稿日時: {existing_info.get('uploaded_at')}")
        print("\n処理をスキップします。")
        return 0

    print(f"📌 投稿キー: {publish_key}\n")

    # ===========================
    # 1. AI予想生成 + 記事コンテンツ生成
    # ===========================
    print("📊 Step 1: AI予想 + 記事コンテンツ生成")
    print("-" * 60)
    print(f"  対象トラック: {target_track}")

    article = None
    article_path = None
    try:
        prediction_system = DailyPredictionAutomation(
            api_base_url=os.getenv('API_BASE_URL', 'https://keiba-ai-predictor.onrender.com')
        )

        # 記事コンテンツ生成（フォールバック付き）
        article = await prediction_system.generate_article_content(top_n=3)

        if not article['success']:
            if article.get('skip', False):
                # データなし → 正常スキップ（exit 0）
                print(f"\n📭 {article['message']}")
                print("📌 本日の自動投稿はスキップします")
                print(f"\n{'=' * 60}")
                print("⏭️  最終判断: スキップ正常終了（レースデータなし）")
                print(f"{'=' * 60}")
                return 0
            else:
                # 本当の異常（JSON破損、必須フィールド欠落など）
                print(f"❌ エラー: {article['message']}")
                return 1

        print(f"✅ 記事コンテンツ生成完了")
        print(f"  タイトル: {article['title']}")
        print(f"  レース数: {len(article['predictions'])}")
        print(f"  競馬場: {article['track']}")
        if article.get('is_fallback'):
            print(f"  ⚠️  フォールバックデータ使用: {article['adopted_date']}")
        print()

        # ローカル保存
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)

        article_path = output_dir / f"article_{article['date']}.md"
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(article['content'])

        print(f"✅ ローカル保存: {article_path}")

        # TODO: CMS公開処理（未実装）
        # publish_to_cms(article)
        # verify_rss_update(article['url'])

        mark_article_published(publish_key, str(article_path))
        print()

    except Exception as e:
        print(f"❌ 記事生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # ===========================
    # 2. 動画生成
    # ===========================
    print("🎬 Step 2: 予想動画生成")
    print("-" * 60)

    video_path = None
    try:
        video_gen = PredictionVideoGenerator()
        video_path = video_gen.generate_video(
            article,
            output_path=str(output_dir / f"prediction_{article['date']}.mp4")
        )

        print(f"✅ 動画生成完了: {video_path}")
        mark_video_generated(publish_key, video_path)
        print()

    except Exception as e:
        print(f"❌ 動画生成エラー: {e}")
        print("記事公開は成功しています。動画は手動で生成可能です。")
        import traceback
        traceback.print_exc()
        return 1

    # ===========================
    # 3. YouTube投稿
    # ===========================
    print("📺 Step 3: YouTube投稿")
    print("-" * 60)

    youtube_url = None
    try:
        # YouTube token チェック
        token_file = os.getenv('YOUTUBE_TOKEN_PATH', 'credentials/youtube_token.json')

        if not os.path.exists(token_file):
            print(f"⚠️  YouTube トークンが見つかりません: {token_file}")
            print("  初回認証をローカルで実行してください:")
            print("  python src/automation/init_youtube_auth.py")
            print(f"\n  動画ファイル: {video_path}")
            print("  手動でアップロードも可能です\n")
            return 1

        uploader = YouTubeUploader(token_file=token_file)

        youtube_url = uploader.upload_video(
            video_path=video_path,
            title=f"【AI競馬予想】{article['date']} {article['track']}競馬 注目レース",
            description=article['summary'],
            tags=['競馬', 'AI予想', article['track'], '南関東競馬', '地方競馬', '機械学習'],
            privacy_status=os.getenv('YOUTUBE_PRIVACY', 'private')  # 本番前はprivate
        )

        if youtube_url:
            print(f"✅ YouTube投稿完了: {youtube_url}")
            mark_uploaded(publish_key, youtube_url)
            print()
        else:
            print("❌ YouTube投稿失敗（URLが返されませんでした）\n")
            return 1

    except Exception as e:
        print(f"❌ YouTube投稿エラー: {e}")
        print("記事と動画は生成済みです。手動アップロードも可能です。")
        import traceback
        traceback.print_exc()
        return 1

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
    print(f"📺 YouTube: {youtube_url}")
    print(f"🔗 サイト: https://keiba-ai-predictor.onrender.com")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  処理が中断されました")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
