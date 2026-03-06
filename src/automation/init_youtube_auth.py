"""
YouTube初回認証専用スクリプト（ローカル実行専用）
CI環境では実行しない
"""

import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    """ローカルでブラウザ認証を実行し、トークンを保存"""
    credentials_file = "credentials/youtube_credentials.json"
    token_file = "credentials/youtube_token.json"

    if not os.path.exists(credentials_file):
        raise FileNotFoundError(
            f"\n❌ 認証情報ファイルが見つかりません: {credentials_file}\n\n"
            "【セットアップ手順】\n"
            "1. Google Cloud Console でプロジェクト作成\n"
            "2. YouTube Data API v3 を有効化\n"
            "3. OAuth 2.0 クライアントID作成（デスクトップアプリ）\n"
            "4. credentials.json をダウンロード\n"
            "5. credentials/youtube_credentials.json に配置\n"
        )

    print("🔐 YouTube OAuth 2.0 認証を開始します...")
    print("ブラウザが自動的に開きます。")

    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_file,
        SCOPES
    )

    # ローカルブラウザで認証
    creds = flow.run_local_server(port=0)

    # トークンを保存
    Path("credentials").mkdir(parents=True, exist_ok=True)
    with open(token_file, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"\n✅ 認証成功！トークンを保存しました")
    print(f"保存先: {token_file}\n")
    print("次のステップ:")
    print("1. このトークンファイルを GitHub Secrets に登録")
    print("   cat credentials/youtube_token.json")
    print("2. GitHub → Settings → Secrets → YOUTUBE_TOKEN_JSON")


if __name__ == "__main__":
    main()
