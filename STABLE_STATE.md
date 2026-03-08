# 動画生成システム安定状態メモ

## 現在の成功条件 (2026-03-08)

### ✅ 動作確認済み
- **TTS**: VOICEVOX (http://localhost:50021) が正常動作
- **動画生成**: 3レース構成 + テロップ + BGM合成が成功
- **BGM処理**: `concatenate_audioclips` による音声重複なし

### 🔧 技術的な成功ポイント

#### 1. VOICEVOX統合
- `src/automation/voicevox_tts.py` でVOICEVOX APIを実装
- `TTS_ENGINE=voicevox` 環境変数で切り替え
- gTTSは開発時のフォールバックとして残すが、本番運用では使用しない

#### 2. BGMループ処理の修正
- **修正箇所**: `src/automation/video_generator.py:818`
- **修正内容**:
  ```python
  # ❌ 旧コード (音声重複発生)
  bgm = concatenate_videoclips([bgm] * loops)

  # ✅ 新コード (正常動作)
  bgm = concatenate_audioclips([AudioFileClip(bgm_path) for _ in range(loops)])
  ```
- **理由**: AudioFileClipオブジェクトには`concatenate_audioclips`を使用する必要がある

#### 3. テスト用BGM
- `create_test_bgm.py` で無音BGMを生成（テスト専用）
- 440Hzサイン波BGMは耳障りなノイズが発生するため使用禁止
- 本番では実際の音楽ファイルを使用する想定

### 📝 実装済みファイル
- `src/automation/voicevox_tts.py` - VOICEVOX TTS実装
- `src/automation/video_generator.py` - BGMループ修正済み
- `src/automation/youtube_format_generator.py` - YouTube形式対応

### 🚫 使用禁止
- gTTS (通常運用では使わない、開発時のみ)
- 440Hzサイン波のテストBGM (本番用に使わない)

### 📋 次のタスク候補（別タスクとして進める）
1. テロップの見栄え改善
   - フォントサイズ調整
   - 配色最適化
   - アニメーション効果

2. 本番BGM選定
   - 著作権フリーBGMの選定
   - BGM音量調整（現在30%）
   - レース種別ごとのBGM切り替え

3. 馬名読み辞書強化
   - 難読馬名のリスト作成
   - VOICEVOX用の読み仮名辞書
   - 自動修正機能

### ⚠️ 注意事項
- 成功状態を壊さないことを最優先
- 新機能追加前に必ずテスト
- 環境変数 `TTS_ENGINE=voicevox` を確認
- VOICEVOXサーバーが起動していることを確認 (localhost:50021)

### 🔄 動作確認コマンド
```bash
# VOICEVOX確認
curl http://localhost:50021/speakers

# テスト動画生成
TARGET_TRACK=kawasaki TTS_ENGINE=voicevox USE_AI_BACKGROUNDS=false \
  python3 src/automation/video_generator.py
```
