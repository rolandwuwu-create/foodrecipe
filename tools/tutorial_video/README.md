# 教學影片（Grok Imagine）

Cursor 的 4.6 不會生片。這條 pipeline 接的是 **Grok Imagine**：

- 靜幀：`grok-imagine-image-2.0`
- 影片：`grok-imagine-video-1.5`（圖生影片）

預設**不搜圖庫**。每一鏡先鎖定這道菜、這一步，再生成。亂搜 `cooking` / `美食` 就是素材會錯的原因。

## 設定

```bash
export XAI_API_KEY=xai-...
```

金鑰只放環境變數，不要寫進 repo。

## 用法

```bash
# 看食譜 id
python3 -m tools.tutorial_video list

# 只出分鏡（不花 API）
python3 -m tools.tutorial_video plan --recipe tomatoegg

# 生成每一鏡並接成一支片
python3 -m tools.tutorial_video render --recipe tomatoegg

# 不是食譜、是功能教學
python3 -m tools.tutorial_video plan \
  --topic "怎麼用冰箱篩出20分鐘晚餐" \
  --steps "打開網站|勾選現有食材|看推薦|點進步驟"
```

沒有金鑰時可用色塊檢查接片：

```bash
python3 -m tools.tutorial_video render --recipe tomatoegg --placeholders
```

輸出在 `out/tutorial_video/<id>/`：

- `storyboard.json` — 分鏡、旁白、must_include
- `shots/sXX/still.jpg` + `clip.mp4`
- `tutorial.mp4`

## 素材規則

1. 一鏡一個畫面，畫面必須是這道菜的這一步。
2. 禁止泛詞搜尋：`cooking`, `kitchen`, `food`, `美食`, `料理`。
3. 若真的要用圖庫，標題／說明必須包含該鏡全部 `must_include`，且不能出現 `must_not`。對不上就改生成，不要硬塞。
