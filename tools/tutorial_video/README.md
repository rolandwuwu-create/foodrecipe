# 小東老師電子學 × 成片產線

對照成品：https://youtu.be/bN9DOArGQbE  
《高頻世界裡，粗電線的心是空的｜集膚效應 5 分鐘搞懂》

這條產線出的是**成片**：腳本、國語配音、**電流／磁場動畫**、字幕、mp4。

Grok Bot 等級的銅線鏡頭是 Imagine **video**（`grok-imagine-video-1.5`），要環境變數 `XAI_API_KEY`。沒有 key 時，銅線改跑程序動畫（電流脈衝、磁場圈、集膚空洞長大），不是靜態圖+Ken Burns。

```bash
python3 -m tools.tutorial_video render --lesson proximity-effect
```

```bash
python3 -m tools.tutorial_video list
python3 -m tools.tutorial_video plan --lesson proximity-effect
python3 -m tools.tutorial_video render --lesson proximity-effect
```

會寫到 `out/tutorial_video/<lesson>/`：

- `SCRIPT.md` 完整旁白＋分鏡腳本
- `YOUTUBE.md` 標題／說明
- `captions.srt` 字幕
- `shots/sXX/vo.mp3` 每一鏡配音
- `tutorial.mp4` 成片

配音預設 `zh-TW-YunJheNeural`（台灣腔男聲）。需要網路。靜音測試加 `--no-voice`。

電影感銅線先無字生成，中文金句與字幕後製疊上。不要搜閃電。
