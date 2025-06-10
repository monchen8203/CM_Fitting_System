# M99_demo.py | 用於測試 main_runner 的錯誤紀錄功能

def main():
    print("這是一個測試錯誤模組，將觸發除以零錯誤")
    x = 1 / 0

if __name__ == "__main__":
    from error_logger import log_exception
    try:
        main()
    except Exception as e:
        log_exception("M99_demo", e)
