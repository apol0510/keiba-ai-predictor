"""
VOICEVOX TTS統合モジュール
自然な日本語音声合成を実現
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional
import os

# VOICEVOX client
try:
    from vvclient import Client
    VOICEVOX_AVAILABLE = True
except ImportError:
    VOICEVOX_AVAILABLE = False


class VoicevoxTTS:
    """VOICEVOX TTS生成クラス"""

    def __init__(self, base_url: str = "http://localhost:50021", speaker: int = 1):
        """
        Args:
            base_url: VOICEVOXエンジンのURL
            speaker: 話者ID (1: ずんだもん（ノーマル）)
        """
        self.base_url = base_url
        self.speaker = speaker
        self.available = VOICEVOX_AVAILABLE

        if not self.available:
            print("⚠️  voicevox-clientがインストールされていません")
            print("   pip install voicevox-client")

    async def _generate_async(self, text: str) -> Optional[str]:
        """
        非同期で音声を生成（内部メソッド）

        Args:
            text: 読み上げテキスト

        Returns:
            生成された音声ファイルのパス
        """
        try:
            async with Client(base_uri=self.base_url) as client:
                # AudioQuery生成
                audio_query = await client.create_audio_query(
                    text=text,
                    speaker=self.speaker
                )

                # 音声合成
                audio_bytes = await audio_query.synthesis(speaker=self.speaker)

                # 一時ファイルに保存
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_file.write(audio_bytes)
                temp_file.close()

                print(f"✅ VOICEVOX音声生成: {len(text)}文字 → {temp_file.name}")
                return temp_file.name

        except Exception as e:
            print(f"⚠️  VOICEVOX音声生成エラー: {e}")
            return None

    def generate(self, text: str) -> Optional[str]:
        """
        同期インターフェースで音声を生成

        Args:
            text: 読み上げテキスト

        Returns:
            生成された音声ファイルのパス（WAV形式）

        Raises:
            RuntimeError: VOICEVOX音声生成に失敗した場合
        """
        if not self.available:
            raise RuntimeError("voicevox-client is not installed")

        try:
            # asyncio イベントループを取得または作成
            try:
                loop = asyncio.get_running_loop()
                # すでに実行中のループがある場合
                future = asyncio.ensure_future(self._generate_async(text))
                result = loop.run_until_complete(future)
            except RuntimeError:
                # ループが実行されていない場合
                result = asyncio.run(self._generate_async(text))

            if result is None:
                raise RuntimeError(f"VOICEVOX audio generation failed for text: {text[:50]}...")

            return result

        except Exception as e:
            raise RuntimeError(f"VOICEVOX generation error: {e}") from e


# テスト実行
if __name__ == '__main__':
    print("🎙️  VOICEVOX TTS テスト\n")

    # VOICEVOXインスタンス作成
    voicevox = VoicevoxTTS(speaker=1)  # ずんだもん（ノーマル）

    if not voicevox.available:
        print("❌ voicevox-clientがインストールされていません")
        exit(1)

    # テストケース
    test_cases = [
        "競馬",
        "川崎2レース",
        "デルニエエリオント",
        "本命は、4番、デルニエエリオントです。",
        "2レース、サラ4歳以上です。本命は、4番、ジーティーラピッド。対抗は、9番、イノ。単穴は、6番、キタサンブリリアンです。"
    ]

    output_dir = Path("output_test/audio_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, text in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] テキスト: {text}")

        audio_path = voicevox.generate(text)

        if audio_path:
            # 出力ディレクトリにコピー
            import shutil
            dest_path = output_dir / f"test_{i:02d}.wav"
            shutil.copy(audio_path, dest_path)
            print(f"✅ 保存: {dest_path}")

            # 一時ファイルを削除
            try:
                os.unlink(audio_path)
            except:
                pass
        else:
            print(f"❌ 生成失敗")

    print(f"\n✅ テスト完了: {output_dir}")
