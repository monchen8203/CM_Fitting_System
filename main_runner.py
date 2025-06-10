# main_runner.py
# Version: 1.0.0 | 執行所有模組主程式，統一錯誤捕捉與日誌管理

import importlib
import logging
from error_logger import log_exception

# 設定 logging
logging.basicConfig(
    filename="logs/debug_session/main_runner.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

modules_to_run = [
    "M01_align_interpolate",
    "M02_sensitivity_analysis",
    "M03_global_search",
    "M04_local_optimize",
    "M05_ngspice_runner",
    "M06_model_builder",
    "M07_plot_results",
    "M08_animate_params",
    "M09_draw_netlist",
    "run_align",
    "M99_demo"
]

def run_module(mod_name):
    logging.info(f"➡️ 執行模組：{mod_name}")
    try:
        module = importlib.import_module(f"modules.{mod_name}")
        if hasattr(module, "main"):
            module.main()
        else:
            logging.warning(f"模組 {mod_name} 無 main() 函數，已跳過")
    except Exception as e:
        log_exception(mod_name, e)
        logging.error(f"❌ 執行 {mod_name} 時發生錯誤：{e}")

if __name__ == "__main__":
    for mod in modules_to_run:
        run_module(mod)
