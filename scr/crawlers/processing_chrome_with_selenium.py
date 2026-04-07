import subprocess

def run_chrome_debug():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = r"C:\selenium_profile"

    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}"
    ]

    try:
        process = subprocess.Popen(cmd)
        print("[INFO] Chrome launched successfully.")
        print(f"[INFO] PID: {process.pid}")
    except FileNotFoundError:
        print("[ERROR] Chrome executable not found.")
    except Exception as e:
        print(f"[ERROR] Failed to launch Chrome: {e}")


if __name__ == "__main__":
    run_chrome_debug()