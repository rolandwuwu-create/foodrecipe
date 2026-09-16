# 小東老師電子學 × Grok Imagine

對照成品：https://youtu.be/bN9DOArGQbE  
《高頻世界裡，粗電線的心是空的｜集膚效應 5 分鐘搞懂》

Grok Bot 強，不是因為 4.6 比較會搜「電」。那支出片是：

1. **金句當標題**（心是空的／電流只走這層）
2. **電影感銅線英雄鏡頭**先無字生成（Cursor GenerateImage 或 Grok Imagine），prompt **不准帶字**
3. **深藍解說圖**自己畫：電流密度熱圖、實心粗線剖面、金句卡
4. 中文字、徽章、字幕是後製疊上去的

Cursor 這邊本來就能生圖。銅線電影感不是 XAI Imagine API 獨佔的；缺的是「先出無字英雄圖，再疊金句」，不是不能畫銅。以前爛在亂搜閃電電塔、還把「不要寫字」寫進教學片。

## 用法

```bash
python3 -m tools.tutorial_video list
python3 -m tools.tutorial_video plan --lesson skin-effect
python3 -m tools.tutorial_video render --lesson skin-effect
```

解說圖不需要 API，內建英雄圖在 `data/heroes/`（銅管、集膚特寫、平行鄰近），會直接出 `tutorial.mp4`。要另走 Grok Imagine 動態鏡頭才需要 key：

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
