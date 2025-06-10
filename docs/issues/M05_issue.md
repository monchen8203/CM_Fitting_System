🔧 M05 模組：Ngspice CLI 模擬器介接
### 📌 任務說明：
- 使用 subprocess 控制 ngspice.exe
- 接收 netlist，執行模擬，擷取 AC 阻抗
- 處理標準輸出與錯誤、Log 儲存
### 📂 相關檔案：
- modules/M05_ngspice_runner.py
- metadata/M05_ngspice_runner.yaml
- logs/M05.log
### ✅ 驗收條件：
- 正確解析結果檔案
- 支援頻率掃描 / 修改 netlist
- 可回傳 Z_cm, Z_dm 結果
🧩 關聯模組：所有模擬型模組  
🗂 任務編號：#5
