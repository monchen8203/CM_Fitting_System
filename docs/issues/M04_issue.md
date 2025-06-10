🔧 M04 模組：SLSQP 局部最佳化器
### 📌 任務說明：
- 在 global search 結果基礎上做精細擬合
- 使用 `scipy.optimize.minimize(method='SLSQP')`
- 輸出最終 loss 與參數組合
### 📂 相關檔案：
- modules/M04_local_optimize.py
- metadata/M04_local_optimize.yaml
- logs/M04.log
- figure/M04_loss_curve.png
### ✅ 驗收條件：
- 擬合 loss 降至設定閾值
- 可與原始阻抗疊圖比對
- 保存參數與適應度歷史
🧩 關聯模組：M03, M05, M07  
🗂 任務編號：#4
