# check_latex.py
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sys

print("--- 開始執行 LaTeX 環境測試 ---")

# 步驟 1: 設定 Matplotlib 使用 LaTeX 來渲染文字
# 如果這一步就出錯，通常代表 Matplotlib 的快取有問題
try:
    matplotlib.rcParams['text.usetex'] = True
    matplotlib.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
    print("[步驟 1/3] Matplotlib 設定使用 LaTeX... 成功")
except Exception as e:
    print(f"[步驟 1/3] Matplotlib 設定使用 LaTeX... 失敗")
    print(f"錯誤訊息: {e}")
    sys.exit(1)

# 步驟 2: 建立一個包含數學公式的簡單圖表
try:
    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    x = np.linspace(0, 2 * np.pi, 200)
    y = np.sin(x)
    ax.plot(x, y, label=r'$y = \sin(x)$') # LaTeX 格式的標籤

    # 使用 LaTeX 格式的標題和軸標籤
    ax.set_title(r'LaTeX Font Test: $\int_0^\infty e^{-x} dx = 1$')
    ax.set_xlabel(r'x-axis ($\alpha$)')
    ax.set_ylabel(r'y-axis ($\beta$)')
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    print("[步驟 2/3] 建立測試圖表... 成功")
except Exception as e:
    print(f"[步驟 2/3] 建立測試圖表... 失敗")
    print(f"錯誤訊息: {e}")
    sys.exit(1)

# 步驟 3: 嘗試將圖表儲存為 PNG 檔案
# 這一步是關鍵，它會實際呼叫您系統中的 LaTeX 引擎
try:
    output_filename = 'latex_test.png'
    fig.savefig(output_filename)
    print(f"[步驟 3/3] 儲存圖檔至 '{output_filename}'... 成功")
    print("\n測試成功！您的 Python 環境可以正確呼叫 LaTeX。")
    print(f"請檢查專案根目錄下是否產生了 '{output_filename}' 圖片。")

except RuntimeError as e:
    print(f"[步驟 3/3] 儲存圖檔... 失敗")
    print("\n測試失敗！看起來您的 Python 環境無法找到或執行 LaTeX。")
    print("這通常是 MiKTeX 安裝不完整，或其路徑未被加入到系統環境變數中所導致。")
    print(f"收到的原始錯誤訊息: {e}")

except Exception as e:
    print(f"[步驟 3/3] 儲存圖檔時發生未知錯誤... 失敗")
    print(f"錯誤訊息: {e}")
