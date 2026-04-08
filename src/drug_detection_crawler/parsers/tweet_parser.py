from bs4 import BeautifulSoup


def extract_num(label: str) -> int:
    num = ""

    for ch in label:
        if ch.isdigit() or ch == ",":
            num += ch
        elif num:
            break

    return int(num.replace(",", "")) if num else 0


def make_item_key(parsed: dict) -> str:
    date = str(parsed.get("date") or "").strip()
    user_id = str(parsed.get("user_id") or "").strip().lower()

    if not date or not user_id:
        return ""

    return f"{date}|{user_id}"


def parse_tweet_html(raw_html: str) -> dict:
    soup = BeautifulSoup(raw_html, "html.parser")

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
            "video_source_url": None,
        },
    }

    user_name_box = article.select_one('[data-testid="User-Name"]')
    if user_name_box:
        for sp in user_name_box.select("span"):
            txt = sp.get_text(strip=True)

            if txt.startswith("@"):
                result["user_id"] = txt
            elif txt and txt != "·" and not result["nickname"]:
                result["nickname"] = txt

    avatar = article.select_one('[data-testid="Tweet-User-Avatar"] img')
    if avatar:
        result["profile_image_url"] = avatar.get("src")

    time_elem = article.select_one("time")
    if time_elem and time_elem.get("datetime"):
        result["date"] = time_elem["datetime"]

    text_elem = article.select_one('[data-testid="tweetText"]')
    if text_elem:
        result["text"] = text_elem.get_text(" ", strip=True)

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
                    break

    seen_image_urls = set()
    for img in article.select('[data-testid="tweetPhoto"] img'):
        src = img.get("src")
        if src and src not in seen_image_urls:
            seen_image_urls.add(src)
            result["image_urls"].append(src)

    seen_tags = set()
    for a in article.select('a[href*="/hashtag/"]'):
        tag = a.get_text(strip=True)
        if tag and tag not in seen_tags:
            seen_tags.add(tag)
            result["hashtags"].append(tag)

    video_elem = article.select_one("video")
    if video_elem:
        result["video"]["video_poster_url"] = video_elem.get("poster")

        source = video_elem.select_one("source")
        if source:
            src = source.get("src")
            if src:
                if src.startswith("blob:"):
                    result["video"]["video_blob_url"] = src
                else:
                    result["video"]["video_source_url"] = src

    return result


def parse_collected_item(item: dict) -> dict:
    raw_html = item.get("raw_html")
    if not raw_html:
        return {}

    parsed = parse_tweet_html(raw_html)
    if not parsed:
        return {}

    item_key = make_item_key(parsed)
    if not item_key:
        return {}

    return {
        "item_key": item_key,
        "collected_at": item.get("collected_at"),
        "source": item.get("source"),
        "raw_html": raw_html,
        "parsed": parsed,
    }