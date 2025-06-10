🔧 M01 模組：插值與頻率對齊功能
### 📌 任務說明：
- 處理 `801CM.txt` 和 `801NM.txt` 的資料
- 使用 log spacing 的 401 點 decade 插值（1 MHz ~ 3 GHz）
- 將插值結果另存為 `.npy` / `.csv`
### 📂 相關檔案：
- modules/M01_align_interpolate.py
- metadata/M01_align_interpolate.yaml
- logs/M01.log
- figure/M01_result.png
### ✅ 驗收條件：
- 插值後資料與原始資料曲線一致
- `.npy` 輸出含頻率軸與插值阻抗值
- 有 INFO 級日誌輸出
🧩 關聯模組：M07_plot_results.py, M05_ngspice_runner.py
📌 關聯 YAML：metadata/M01_align_interpolate.yaml  
🗂 任務編號：#1
