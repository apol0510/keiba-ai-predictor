"""
投稿状態管理（二重投稿防止）

注意: この実装は暫定方式です。
長期本番運用では、以下への移行を推奨します:
- CMS側での記事ID管理
- Airtable / Supabase等の外部DB
- GitHub Artifactsやクラウドストレージ

現在の automation_state.json は開発・テスト用途向けです。
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict


STATE_FILE = Path("automation_state.json")


def load_state() -> Dict:
    """状態ファイルを読み込む"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("⚠️  状態ファイルが破損しています。新規作成します。")
            return {}
    return {}


def save_state(state: Dict):
    """状態ファイルを保存"""
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def already_uploaded(key: str) -> bool:
    """
    すでに投稿済みかチェック

    Args:
        key: 一意キー（例: "2026-03-05-main"）

    Returns:
        True: 投稿済み, False: 未投稿
    """
    state = load_state()
    return key in state and state[key].get("youtube_url") is not None


def mark_uploaded(key: str, youtube_url: str):
    """
    投稿済みとしてマーク

    Args:
        key: 一意キー
        youtube_url: YouTubeの動画URL
    """
    state = load_state()
    state[key] = {
        "youtube_url": youtube_url,
        "uploaded_at": datetime.now().isoformat()
    }
    save_state(state)
    print(f"✅ 投稿状態を保存: {key}")


def get_upload_info(key: str) -> Optional[Dict]:
    """
    投稿情報を取得

    Args:
        key: 一意キー

    Returns:
        投稿情報（なければNone）
    """
    state = load_state()
    return state.get(key)


def mark_article_published(key: str, article_url: str):
    """
    記事公開済みとしてマーク

    Args:
        key: 一意キー
        article_url: 記事URL
    """
    state = load_state()
    if key not in state:
        state[key] = {}
    state[key]["article_url"] = article_url
    state[key]["article_published_at"] = datetime.now().isoformat()
    save_state(state)


def mark_video_generated(key: str, video_path: str):
    """
    動画生成済みとしてマーク

    Args:
        key: 一意キー
        video_path: 動画ファイルパス
    """
    state = load_state()
    if key not in state:
        state[key] = {}
    state[key]["video_path"] = video_path
    state[key]["video_generated_at"] = datetime.now().isoformat()
    save_state(state)


# テスト実行
if __name__ == "__main__":
    test_key = f"{datetime.now().strftime('%Y-%m-%d')}-test"

    print(f"テストキー: {test_key}")
    print(f"投稿済み？ {already_uploaded(test_key)}")

    mark_uploaded(test_key, "https://youtube.com/watch?v=TEST123")
    print(f"投稿済み？ {already_uploaded(test_key)}")

    info = get_upload_info(test_key)
    print(f"投稿情報: {info}")
