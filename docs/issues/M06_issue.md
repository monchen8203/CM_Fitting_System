🔧 M06 模組：嵌入參數並生成 SPICE 模型
### 📌 任務說明：
- 將優化參數嵌入 `Tai_CM.txt` Netlist
- 輸出帶參數版本的 netlist 檔案
- 支援 `.param` 替換與正則處理
### 📂 相關檔案：
- modules/M06_model_builder.py
- metadata/M06_model_builder.yaml
- netlist/optimized_Tai_CM.cir
### ✅ 驗收條件：
- 參數替換成功
- 可傳遞給 ngspice_runner 使用
- 儲存 YAML 版本控制摘要
🧩 關聯模組：M03, M04, M05  
🗂 任務編號：#6
