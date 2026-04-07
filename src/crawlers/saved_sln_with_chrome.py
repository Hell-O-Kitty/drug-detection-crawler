from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

driver = webdriver.Chrome(options=options)

html = driver.page_source

with open("preprocessing/saved_html/saved_page_15.html", "w", encoding="utf-8") as f:
    f.write(html)

print("저장 완료")