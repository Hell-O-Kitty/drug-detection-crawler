from load_tools import *
from parse_tools import *
from save_tools import *
import csv

html_list = load_all_html_in_folder("preprocessing/saved_html")

# 특정 폴더 안에 있는 html 파일 전체 불러오기
def extract_articles_from_html():
    for load_idx, html_info in enumerate(html_list, start=1):
        print(f"[{load_idx:03d}] loading >> {html_info["file_name"]}")

        articles = split_articles(read_single_html(html_info["file_path"]))

        save_articles(html_info["file_name"], "article_result", articles)

def parse_articles_to_json():
    results = []

    for load_idx, article_html in enumerate(load_all_html_in_folder("article_result"), start=1):
        parsed = parse_tweet_article(read_single_html(article_html["file_path"]))
        if parsed:
            results.append(parsed)
    
    save_to_json(results, "tweets.json");
    
    print(f"{len(results)}개 트윗 저장")
    print()


# extract_articles_from_html()
# parse_articles_to_json()

save_json_to_csv("tweets.json", "test.csv")