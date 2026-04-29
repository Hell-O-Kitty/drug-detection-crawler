import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

url = "https://api.x.com/2/tweets/search/recent"
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

keyword = "작대기"
lang = "ko"

params = {
    "query": f"{keyword} lang:{lang} -is:retweet",
    "max_results": 10,

    # Tweet 필드
    "tweet.fields": ",".join([
        "id",
        "text",
        "author_id",
        "created_at",
        "lang",
        "source",
        "public_metrics",
        "possibly_sensitive",
        "reply_settings",
        "conversation_id",
        "in_reply_to_user_id",
        "referenced_tweets",
        "entities",
        "context_annotations",
        "attachments",
        "edit_history_tweet_ids"
    ]),

    # 확장 (연결 데이터)
    "expansions": ",".join([
        "author_id",
        "referenced_tweets.id",
        "referenced_tweets.id.author_id",
        "attachments.media_keys",
        "geo.place_id"
    ]),

    # User 필드 (작성자)
    "user.fields": ",".join([
        "id",
        "name",
        "username",
        "created_at",
        "description",
        "location",
        "profile_image_url",
        "verified",
        "public_metrics"
    ]),

    # Media 필드 (이미지/영상)
    "media.fields": ",".join([
        "media_key",
        "type",
        "url",
        "preview_image_url",
        "width",
        "height",
        "duration_ms",
        "public_metrics"
    ]),

    # Place (위치 정보)
    "place.fields": ",".join([
        "full_name",
        "id",
        "country",
        "country_code",
        "geo",
        "name",
        "place_type"
    ])
}

response = requests.get(url, headers=headers, params=params)

data = response.json()

with open("test_result.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("저장 완료 : test_result.json")
