# CM_Fitting_System 功能追蹤矩陣

| 模組編號 | 模組名稱              | 功能說明                                                   | 輸入依賴                     | 輸出提供                         | 實作狀態 | YAML Metadata                                |
|----------|-----------------------|------------------------------------------------------------|------------------------------|----------------------------------|----------|-----------------------------------------------|
| M01      | align_interpolate     | 匹配資料與等間距內插                                       | `data/*.txt`                 | 對齊後資料（中間輸出）           | ⬜ Todo  | `metadata/M01_align_interpolate.yaml`         |
| M02      | sensitivity_analysis  | 參數靈敏度分析與初步範圍判定                               | M01 輸出, 初始網表            | 敏感度報告, 初始參數建議         |  ⬜ Todo  | `metadata/M02_sensitivity_analysis.yaml`      |
| M03      | global_search         | 全域參數搜尋（粗略）                                       | M01 輸出, 模型範圍            | 最佳參數群, 分數表               | ⬜ Todo  | `metadata/M03_global_search.yaml`             |
| M04      | local_optimize        | 局部參數最佳化（微調）                                     | M03 輸出, Ngspice 模型        | 精確參數                         | ⬜ Todo  | `metadata/M04_local_optimize.yaml`            |
| M05      | ngspice_runner        | 自動產生/執行 Netlist 並取得模擬結果                       | 模型與參數, netlist 描述      | 頻率響應資料                     | ⬜ Todo | `metadata/M05_ngspice_runner.yaml`            |
| M06      | model_builder         | 根據參數建立 SPICE 子電路                                  | M04 輸出, 模板 Netlist        | 完整模型 Netlist 檔              |  ⬜ Todo  | `metadata/M06_model_builder.yaml`             |
| M07      | plot_results          | 畫出模擬 vs 實測圖表                                       | M01 輸出, M05 輸出            | 圖表 PDF/PNG                     |  ⬜ Todo  | `metadata/M07_plot_results.yaml`              |
| M08      | animate_params        | 參數變化動畫（增減趨勢）                                   | M02/M03 輸出                  | GIF/MP4                          | ⬜ Todo  | `metadata/M08_animate_params.yaml`            |
| M09      | draw_netlist          | schemdraw 畫出 Netlist 對應電路圖                           | 模型結構資訊                  | SVG/PNG 電路圖                   |  ⬜ Todo  | `metadata/M09_draw_netlist.yaml`              |
| Runner   | run_align.py          | 主控流程（初步資料對齊）                                   | `data/*.txt`                 | 中繼檔案                         |  ⬜ Todo  | `metadata/run_align.yaml`                     |

---

🟢 ✅ Ready：已完成  
🟡 Draft：部分完成或原型中  
⬜ Todo：尚未開始

