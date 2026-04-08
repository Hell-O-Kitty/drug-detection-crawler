import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from src.config.settings import DEBUG_PORT, HTML_TAG, SOURCE_NAME, RAW_JSON_PATH
from src.storage.save_json import load_json, save_json


def connect_driver():
    options = Options()
    options.add_experimental_option(
        "debuggerAddress",
        f"127.0.0.1:{DEBUG_PORT}"
    )
    return webdriver.Chrome(options=options)


def build_raw_html_key(raw_html: str) -> str:
    return (raw_html or "").strip()


def collect_elements_to_json(driver, pause_time=2, max_scroll=30):
    existing = load_json(RAW_JSON_PATH)

    seen_raw_keys = {
        build_raw_html_key(item.get("raw_html", ""))
        for item in existing
        if item.get("raw_html")
    }

    results = existing[:]
    no_new_count = 0

    for scroll_idx in range(max_scroll):
        elements = driver.find_elements(By.CSS_SELECTOR, HTML_TAG)
        added = 0

        for el in elements:
            try:
                raw_html = el.get_attribute("outerHTML")
                raw_key = build_raw_html_key(raw_html)

                if not raw_key or raw_key in seen_raw_keys:
                    continue

                seen_raw_keys.add(raw_key)

                results.append({
                    "collected_at": datetime.now().isoformat(timespec="seconds"),
                    "source": SOURCE_NAME,
                    "raw_html": raw_html
                })

                added += 1

            except Exception as e:
                print(f"[WARN] element 처리 실패: {e}")

        save_json(results, RAW_JSON_PATH)

        print(
            f"[INFO] scroll={scroll_idx+1}, "
            f"visible={len(elements)}, "
            f"new={added}, total={len(results)}"
        )

        if added == 0:
            no_new_count += 1
        else:
            no_new_count = 0

        if no_new_count >= 3:
            print("[INFO] 종료 (새 데이터 없음)")
            break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)


def main():
    driver = connect_driver()
    collect_elements_to_json(driver)


if __name__ == "__main__":
    main()