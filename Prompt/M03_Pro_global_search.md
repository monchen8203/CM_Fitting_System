請根據模組 M03（global_search），使用 scipy.optimize.differential_evolution 幫我產生一個初步最佳化模組，輸入為頻率對齊後插值資料與 Netlist 模板，目標為將共模/差模阻抗誤差最小化。Ngspice 使用 subprocess 呼叫 CLI 模式。

需符合以下條件：
- Python 3.9 / Ngspice CLI 44.2
- 支援多參數調整、自訂上下限
- 執行中可記錄 log 與當前 best solution
- 輸出最終參數與模擬誤差圖（CM / NM）

Log 儲存至 logs/global_search.log
