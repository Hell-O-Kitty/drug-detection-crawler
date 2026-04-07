import subprocess
from src.config.settings import CHROME_PATH, USER_DATA_DIR, DEBUG_PORT

def run_chrome_debug():
    USER_DATA_DIR.mkdir(exist_ok=True)

    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}"
    ]

    try:
        process = subprocess.Popen(cmd)
        print("[INFO] 크롬 실행 성공.")
        print(f"[INFO] PID: {process.pid}")
    except FileNotFoundError:
        print("[ERROR] 크롬 실행 파일 찾을 수 없음.")
    except Exception as e:
        print(f"[ERROR] 크롬 실행 실패: {e}")

def main():
    run_chrome_debug()

if __name__ == "__main__":
    main()