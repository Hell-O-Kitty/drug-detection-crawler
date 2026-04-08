import time
import hashlib
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from drug_detection_crawler.crawlers.chrome_debug_launcher import run_chrome_debug
from drug_detection_crawler.config.settings import DEBUG_PORT, HTML_TAG, SOURCE_NAME, RAW_JSON_PATH, PARSED_JSON_PATH
from drug_detection_crawlerrc.storage.save_json import load_json, save_json


def connect_driver():
    options = Options()
    options.add_experimental_option(
        "debuggerAddress",
        f"127.0.0.1:{DEBUG_PORT}"
    )
    return webdriver.Chrome(options=options)


def build_item_key(raw_html: str) -> str:
    normalized = " ".join(raw_html.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def collect_elements_to_json(driver, pause_time=2, max_scroll=30, stop_when_no_new=3):
    seen_keys = set({})

    results = []
    no_new_count = 0

    for scroll_idx in range(max_scroll):
        elements = driver.find_elements(By.CSS_SELECTOR, HTML_TAG)
        added = 0

        for el in elements:
            try:
                raw_html = el.get_attribute("outerHTML")
                item_key = build_item_key(raw_html)

                if item_key in seen_keys:
                    continue

                seen_keys.add(item_key)

                results.append({
                    "item_key": item_key,
                    "collected_at": datetime.now().isoformat(timespec="seconds"),
                    "source": SOURCE_NAME,
                    "raw_html": raw_html
                })
                added += 1

            except Exception as e:
                print(f"[WARN] element 처리 실패: {e}")

        save_json(results, RAW_JSON_PATH)

        print(
            f"[INFO] scroll={scroll_idx + 1}, "
            f"visible={len(elements)}, "
            f"new={added}, "
            f"total={len(results)}"
        )

        if added == 0:
            no_new_count += 1
        else:
            no_new_count = 0

        if no_new_count >= stop_when_no_new:
            print("[INFO] 새 데이터가 없어 크롤링을 종료합니다.")
            break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)

    return results


def main():
    print("[INFO] Chrome 디버그 모드 실행")
    run_chrome_debug()
    command = "y"

    while command = "y":
        print()
        print("[INFO] 브라우저에서 원하는 페이지를 직접 열어주세요.")
        print("[INFO] 로그인/검색/페이지 이동까지 끝낸 뒤 Enter를 누르면 크롤링을 시작합니다.")
        input(">>> 준비가 끝났으면 Enter: ")

        print()
        print("[INFO] Selenium이 디버그 크롬에 연결합니다.")
        driver = connect_driver()

        print("[INFO] 현재 페이지 URL")
        print(driver.current_url)

        print()
        print("[INFO] 크롤링 시작")
        collect_elements_to_json(driver)

        print()
        print(f"[DONE] 저장 완료: {RAW_JSON_PATH}")

        print("[INFO] 크롤링을 계속하시겠습니까?")
        command = lower(input(">>> [y/n]: "))
    
    print("[INFO] 크롤링을 종료합니다.")
    

if __name__ == "__main__":
    main()