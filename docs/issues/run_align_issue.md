🔧 主控模組：模組整合執行流程控制
### 📌 任務說明：
- 整合各模組成流程式架構
- 控制 YAML metadata 輸入、呼叫模組執行
- 儲存 log、錯誤回報、輸出總結報表
### 📂 相關檔案：
- modules/run_align.py
- metadata/run_align.yaml
- logs/main.log
### ✅ 驗收條件：
- 可以設定單模組或全模組執行
- LOG 訊息包含每模組結果摘要
- 提供失敗回報與 retry 機制
🧩 關聯模組：M01~M09 全部  
🗂 任務編號：#10
