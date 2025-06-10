# 📘 CM_Fitting_System 開發流程書

> 最後更新：2025-06-10

---

## 🎯 專案目標與模組設計

Ngspice 模擬驅動的共模濾波建模系統，具備模組化、最佳化、自動化視覺化與錯誤追蹤能力。

---

## 🔁 推薦開發順序

| 優先順序 | 模組代碼 | 模組名稱            | 功能簡述                           | 依賴模組      |
|----------|-----------|---------------------|------------------------------------|----------------|
| 1        | M01       | align_interpolate   | 頻率插值 + Decade 對齊（401 點）  | -              |
| 2        | M06       | model_builder       | 將 YAML 參數嵌入 Netlist 模板      | M01            |
| 3        | M05       | ngspice_runner      | 控制 Ngspice 執行，擷取輸出       | M06            |
| 4        | M02       | sensitivity_analysis| 模擬結果靈敏度分析                 | M05            |
| 5        | M03       | global_search       | 差分演化演算法最佳化               | M05, M01       |
| 6        | M04       | local_optimize      | SLSQP 精化                         | M03            |
| 7        | M07       | plot_results        | 繪製阻抗對比圖                     | M05, M01       |
| 8        | M08       | animate_params      | 動畫顯示參數優化歷程              | M03, M04       |
| 9        | M09       | draw_netlist        | 原理圖繪製（Schemdraw）           | M06            |
| 10       | run       | run_align           | 控制全流程                         | 所有模組       |

---

## 📌 每次開發流程（模組週期）

1. 建立分支：`git checkout -b feature/M01-align-interpolate`
2. 撰寫模組：`modules/M01_align_interpolate.py`
3. 撰寫 YAML：`metadata/M01_align_interpolate.yaml`
4. 單獨測試模組
5. 串接測試：執行 `main_runner.py`
6. 撰寫 AI-Log、更新 Git 版本
7. 整合 `/docs/project_logbook.md` 自動更新

---

## 🧰 重要工具

- `main_runner.py`：整合測試入口
- `error_logger.py`：自動錯誤記錄
- `update_ai_log.py` + `update_logbook.py`：整合說明
