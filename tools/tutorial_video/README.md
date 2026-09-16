# 小東老師電子學 × Grok Imagine

對照成品：https://youtu.be/bN9DOArGQbE  
《高頻世界裡，粗電線的心是空的｜集膚效應 5 分鐘搞懂》

Grok Bot 強，不是因為 4.6 比較會搜「電」。那支出片是：

1. **金句當標題**（心是空的／電流只走這層）
2. **Imagine 只生英雄鏡頭**（粗銅線剖面、電流只走表皮）——prompt **不准帶字**
3. **深藍解說圖**自己畫：電流密度熱圖、實心粗線剖面、金句卡
4. 中文字、徽章、字幕是後製疊上去的

Cursor 之前爛在：沒 Imagine、亂搜閃電電塔、還把「不要寫字」寫進教學片（教學片最需要大字金句）。

## 用法

```bash
python3 -m tools.tutorial_video list
python3 -m tools.tutorial_video plan --lesson skin-effect
python3 -m tools.tutorial_video render --lesson skin-effect
```

解說圖不需要 API，會直接出 `tutorial.mp4`。要補 Grok Bot 那種銅線英雄鏡頭：

```bash
export XAI_API_KEY=xai-...
python3 -m tools.tutorial_video render --lesson skin-effect --imagine
```

新題目沿用同一套文法（現場問題 → 機制圖 → 金句 → 取捨）：

```bash
python3 -m tools.tutorial_video plan \
  --topic "集膚效應" \
  --jinju "高頻世界裡，粗電線的心是空的。" \
  --steps "低頻整根都在跑|高頻被趕到表皮|不是再粗一號就好"
```
