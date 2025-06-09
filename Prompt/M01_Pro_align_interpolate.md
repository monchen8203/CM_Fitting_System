請根據模組代碼 M01（align_interpolate），撰寫一個 Python 模組，功能為讀取 801CM.txt 和 801NM.txt 兩組阻抗資料，進行對頻率軸（401 點 Decade 掃頻，1 MHz ~ 3 GHz）的插值處理，使其可與 ngspice 模擬結果比對。請輸出成統一格式的 DataFrame 或 .npy 檔案供後續模組使用。

參考規格：
- Python 版本：3.9.0
- 使用 numpy, pandas, scipy.interpolate
- 支援雙軸插值（頻率一致）
- 所有日誌請儲存 logs/align_interpolate.log（UTF-8 中文）
- 輸出資料結構應標示來源（CM/NM）

風格與 M05 相容（變數命名、log 訊息格式、錯誤處理）
