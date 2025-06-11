# m10_interactive_viewer.py
# -*- coding: utf-8 -*-

import sys
import os
import logging
import multiprocessing
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

# --- 路徑修正 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 全域設定 ---
PROJECT_ROOT = Path(project_root)
LOG_DIR = PROJECT_ROOT / 'logs'
FIGURE_DIR = PROJECT_ROOT / 'figure'

# --- 日誌設定 ---
def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    # 建立一個專屬的 logger
    logger = logging.getLogger('M10_Viewer')
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - (%(module)s) - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # 檔案 handler
    fh = logging.FileHandler(LOG_DIR / 'm10_interactive_viewer.log', mode='w', encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 控制台 handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger

logger = setup_logging()

# --- 內部函式，將在子程序中被執行 ---
def _show_image_in_process(image_path_str: str):
    """
    這是一個簡單的函式，其唯一任務是在一個獨立的程序中顯示一張圖片。
    """
    try:
        image_path = Path(image_path_str)
        # 讀取圖片檔案
        img = mpimg.imread(image_path)

        # 建立一個視窗來顯示圖片
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(img)
        
        # 美化顯示，隱藏座標軸
        ax.axis('off')
        
        # 設定視窗標題
        # fig.canvas.manager is not available on all backends, so we use a more robust way
        fig.suptitle(f"檢視圖片: {image_path.name}", fontsize=12)
        
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        
        # 顯示圖片，程式會在此暫停，直到使用者關閉視窗
        plt.show()

    except Exception as e:
        # 在子程序中，我們無法使用 logger，所以用 print
        print(f"[M10 子程序錯誤] 顯示圖片時發生錯誤: {e}")

# --- 主功能函式 ---
def display_image_and_wait(image_filename: str):
    """
    在一個新的獨立程序中，讀取並顯示一張圖片，並暫停主程式直到圖片視窗被關閉。

    Args:
        image_filename (str): 要顯示的圖片檔案名稱 (例如 'my_plot.png')。
    """
    image_path = FIGURE_DIR / image_filename
    logger.info(f"準備在新視窗中顯示圖片: {image_path}")

    if not image_path.is_file():
        logger.error(f"錯誤：找不到圖片檔案 '{image_path}'。")
        return

    # 建立並啟動子程序
    # 使用 'spawn' 模式在 Windows 和 macOS 上更穩定
    ctx = multiprocessing.get_context('spawn')
    p = ctx.Process(target=_show_image_in_process, args=(str(image_path),))
    p.start()
    
    # 等待子程序結束 (即等待使用者關閉圖片視窗)
    p.join()
    
    logger.info(f"圖片視窗已關閉，主程式繼續執行。")


# --- 主程式 (if __name__ == '__main__') ---
if __name__ == '__main__':
    logging.info("="*50)
    logging.info("=== 執行 M10 模組 (Interactive Viewer) 獨立測試 ===")
    logging.info("="*50)

    # 這個獨立測試假設 'M09_Generated_Schematic.png' 已經由 M09 產生
    # 如果您想讓它能完全獨立運作，需要先呼叫 M09 來產生圖片
    test_image_name = 'M09_Generated_Schematic.png'
    
    # 檢查測試圖片是否存在
    if not (FIGURE_DIR / test_image_name).exists():
        logging.warning(f"找不到測試圖片 '{test_image_name}'。")
        logging.warning("請先執行 m09_draw_netlist.py 來產生一張範例圖片，或將您想看的圖片手動放到 'figure' 資料夾。")
    else:
        # 呼叫 M10 的主功能來顯示圖片
        display_image_and_wait(test_image_name)
    
    logging.info("="*50)
    logging.info("=== M10 獨立測試執行完畢！ ===")
