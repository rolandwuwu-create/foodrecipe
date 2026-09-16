# 電學小知識 × Grok Imagine

Cursor 4.6 不會生片。這條 pipeline 接 **Grok Imagine**，給電腦端「電學小知識」短片用：

- 靜幀：`grok-imagine-image-2.0`
- 影片：`grok-imagine-video-1.5`（圖生影片）

預設**不搜圖庫**。每一鏡鎖定「這個概念、這張電路圖」。搜 `electricity` / `閃電` / `電力` 會拿到雷暴和電塔，那就是素材會錯的原因。

## 設定

```bash
export XAI_API_KEY=xai-...
```

## 用法

```bash
# 內建課
python3 -m tools.tutorial_video list
python3 -m tools.tutorial_video plan --lesson ohms-law
python3 -m tools.tutorial_video render --lesson ohms-law

# 新的一則小知識
python3 -m tools.tutorial_video plan \
  --topic "短路為什麼會跳閘" \
  --hook "電流抄近路的時候，保護裝置在做什麼。" \
  --steps "什麼是短路|電流為什麼暴衝|斷路器怎麼斷開"
```

沒有金鑰時可先看分鏡，或 `--placeholders` 檢查接片。

輸出：`out/tutorial_video/<id>/tutorial.mp4`，以及每一鏡的 still / clip。

內建課在 `data/lessons.json`，直接加一則即可。
