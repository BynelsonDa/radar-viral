"""Collect public statistics for short-video candidates from YouTube Data API v3."""
import os
import re
from datetime import datetime, timedelta, timezone
from database import connect
import requests
from dotenv import load_dotenv

load_dotenv()
BASE = "https://www.googleapis.com/youtube/v3"

def duration_seconds(value):
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value or "")
    if not match:
        return None
    hours, minutes, seconds = (int(x or 0) for x in match.groups())
    return hours * 3600 + minutes * 60 + seconds

def youtube(endpoint, **params):
    key = os.environ["YOUTUBE_API_KEY"]
    try:
        response = requests.get(f"{BASE}/{endpoint}", params={**params, "key": key}, timeout=30)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        # Requests exceptions include the URL and its API key. Never propagate them.
        raise RuntimeError('YouTube no respondió correctamente; verifica clave, red y cuota.') from None

def run():
    terms = [t.strip() for t in os.environ.get("SEARCH_TERMS", "curiosidades").split(";") if t.strip()]
    limit = max(0, int(os.environ.get("MAX_SEARCHES_PER_RUN", "7")))
    page_size = min(50, max(1, int(os.environ.get("MAX_RESULTS_PER_SEARCH", "25"))))
    age_days = max(1, int(os.environ.get("MAX_VIDEO_AGE_DAYS", "60")))
    since = (datetime.now(timezone.utc) - timedelta(days=age_days)).isoformat().replace("+00:00", "Z")
    ids = set()
    for term in terms[:limit]:
        result = youtube("search", part="snippet", type="video", q=term,
                         videoDuration="short", order="viewCount", maxResults=page_size,
                         publishedAfter=since)
        ids.update(x["id"]["videoId"] for x in result.get("items", []) if x.get("id", {}).get("videoId"))
    return save_videos(ids)


def refresh_existing(limit=500):
    conn = connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT video_id FROM videos ORDER BY last_seen_at ASC,video_id LIMIT %s', (limit,))
            ids = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()
    return save_videos(ids)


def save_videos(ids):
    ids = sorted(ids)
    conn = connect()
    saved = 0
    try:
        cursor = conn.cursor()
        for offset in range(0, len(ids), 50):
            batch = ids[offset:offset + 50]
            items = youtube("videos", part="snippet,contentDetails,statistics", id=",".join(batch)).get("items", [])
            for item in items:
                seconds = duration_seconds(item.get("contentDetails", {}).get("duration"))
                if seconds is None or seconds > 180:
                    continue
                snippet, stats = item["snippet"], item.get("statistics", {})
                published = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")).replace(tzinfo=None)
                views = int(stats.get("viewCount", 0))
                likes = int(stats["likeCount"]) if "likeCount" in stats else None
                comments = int(stats["commentCount"]) if "commentCount" in stats else None
                cursor.execute("""INSERT INTO videos
                    (video_id,title,channel_title,published_at,duration_seconds,view_count,like_count,comment_count)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title),channel_title=VALUES(channel_title),
                    published_at=VALUES(published_at),duration_seconds=VALUES(duration_seconds),
                    view_count=VALUES(view_count),like_count=VALUES(like_count),
                    comment_count=VALUES(comment_count),last_seen_at=CURRENT_TIMESTAMP""",
                    (item["id"], snippet.get("title", ""), snippet.get("channelTitle"),
                     published, seconds, views, likes, comments))
                cursor.execute("""INSERT INTO snapshots (video_id,view_count,like_count,comment_count)
                    VALUES (%s,%s,%s,%s)""", (item["id"], views, likes, comments))
                saved += 1
            conn.commit()
    finally:
        conn.close()
    print(f"Guardados {saved} candidatos a Shorts. La duración no confirma el formato Shorts.", flush=True)
    return saved

if __name__ == "__main__":
    run()
