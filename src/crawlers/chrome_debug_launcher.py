import subprocess
from config.settings import CHROME_PATH, USER_DATA_DIR, DEBUG_PORT

def run_chrome_debug():
    USER_DATA_DIR.mkdir(exist_ok=True)

    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}"
    ]

    try:
        process = subprocess.Popen(cmd)
        print("[INFO] Chrome launched successfully.")
        print(f"[INFO] PID: {process.pid}")
    except FileNotFoundError:
        print("[ERROR] Chrome executable not found.")
    except Exception as e:
        print(f"[ERROR] Failed to launch Chrome: {e}")

def main():
    run_chrome_debug()

if __name__ == "__main__":
    main()