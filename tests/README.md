# 測試

```bash
pip install playwright && playwright install chromium   # 第一次
bash tests/run_all.sh
```

| 檔案 | 內容 |
|---|---|
| `core/*.js` | 從 `index.html` 抽出 SIM-CORE（`// === SIM-CORE-BEGIN ===` 到 `END`）在 node 執行 |
| `core/baseline/*.txt` | 上面各測試的標準輸出；輸出必須逐字相同。刻意修改物理或控制器、確認結果正確後才更新：`node core/xxx.js > core/baseline/xxx.txt` |
| `browser/build.py` | 產生 `test.html`：把 three.js 換成 `browser/three/three.min.js` 替身（不需要網路、不畫 3D） |
| `browser/regress.py` | 70 項回歸測試：各模式、彈出視窗、參數重設、鍵盤 / 手把解鎖、考照計時、軌跡、重飛、墜機、全螢幕、主題切換 |
| `browser/deltest.py` | 逐一刪除每個模組區塊，確認頁面仍可執行（驗證模組之間沒有硬相依） |
| `browser/origin.py` | 原站與其他網址時的頁尾顯示 |

因為使用 three.js 替身，3D 畫面本身（模型、旋翼轉動、場地）仍需手動開頁面看一眼。
