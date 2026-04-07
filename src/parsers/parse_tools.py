from bs4 import BeautifulSoup
from datetime import datetime

def split_articles(html_text):
    bs = BeautifulSoup(html_text, "html.parser")
    articles = bs.find_all("article")

    print()
    print(f"extract {len(articles)} articles")
    print()

    return [str(article) for article in articles]

def parse_tweet_article(article_html: str) -> dict:
    soup = BeautifulSoup(article_html, "html.parser")
    article = soup.select_one('article[data-testid="tweet"]')
    if not article:
        return {}

    result = {
        "nickname": None,
        "user_id": None,
        "profile_image_url": None,
        "date": None,
        "text": None,
        "counts": {
            "reply": 0,
            "retweet": 0,
            "like": 0,
            "view": 0,
        },
        "image_urls": [],
        "hashtags": [],
        "video": {
            "video_blob_url": None,
            "video_poster_url": None,
            "video_source_url": None
        }
    }

    # 닉네임 / 유저ID
    user_name_box = article.select_one('[data-testid="User-Name"]')
    if user_name_box:
        for sp in user_name_box.select("span"):
            txt = sp.get_text(strip=True)
            if txt.startswith("@"):
                result["user_id"] = txt
            elif txt and txt != "·" and not result["nickname"]:
                result["nickname"] = txt

    # 프로필 이미지
    avatar = article.select_one('[data-testid="Tweet-User-Avatar"] img')
    if avatar:
        result["profile_image_url"] = avatar.get("src")

    # 업로드 날짜 (YYYY-MM-DD) - 시간도 가능할듯
    time_elem = article.select_one("time")
    if time_elem and time_elem.get("datetime"):
        result["date"] = time_elem["datetime"]

    # 글의 본문 텍스트
    text_elem = article.select_one('[data-testid="tweetText"]')
    if text_elem:
        result["text"] = text_elem.get_text(" ", strip=True)

    # reply, repost, loke, view 아이콘 숫자들
    def extract_num(label):
        num = ""
        for ch in label:
            if ch.isdigit() or ch == ",":
                num += ch
            elif num:
                break
        return int(num.replace(",", "")) if num else 0

    for btn in article.select("button[aria-label]"):
        label = btn.get("aria-label", "").lower()

        if "reply" in label:
            result["counts"]["reply"] = extract_num(label)
        elif "repost" in label or "retweet" in label:
            result["counts"]["retweet"] = extract_num(label)
        elif "like" in label:
            result["counts"]["like"] = extract_num(label)

    group = article.select_one('[role="group"][aria-label]')
    if group:
        txt = group.get("aria-label", "").lower()
        if "view" in txt:
            for part in txt.split(","):
                if "view" in part:
                    result["counts"]["view"] = extract_num(part)

    # 첨부 이미지 url
    for img in article.select('[data-testid="tweetPhoto"] img'):
        src = img.get("src")
        if src:
            result["image_urls"].append(src)

    # 해시태그 (text만)
    seen = set()
    for a in article.select('a[href*="/hashtag/"]'):
        tag = a.get_text(strip=True)
        if tag and tag not in seen:
            seen.add(tag)
            result["hashtags"].append(tag)

    # 비디오 관련 url
    video_elem = article.select_one("video")
    if video_elem:
        result["video"]["video_poster_url"] = video_elem.get("poster")

        source = video_elem.select_one("source")
        if source:
            src = source.get("src")
            if src.startswith("blob:"):
                result["video"]["video_blob_url"] = src
            else:
                result["video"]["video_source_url"] = src

    return result

