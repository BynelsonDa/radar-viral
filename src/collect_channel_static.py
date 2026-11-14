"""Fetch public @Neutrinitoo stats, uploads and selected public comments.

Outputs public-only data. No OAuth credentials or private analytics.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from collect_static import youtube, seconds

HANDLE = os.getenv("YOUTUBE_CHANNEL_HANDLE", "@Neutrinitoo")


def collect_channel():
    channels = youtube("channels", part="snippet,statistics,contentDetails", forHandle=HANDLE).get("items", [])
    if not channels:
        raise RuntimeError("No se encontro el canal de YouTube solicitado.")
    channel = channels[0]
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    while len(ids) < 100:
        params = {"part": "contentDetails", "playlistId": playlist,
                  "maxResults": min(50, 100 - len(ids))}
        if page:
            params["pageToken"] = page
        result = youtube("playlistItems", **params)
        ids.extend(x["contentDetails"]["videoId"] for x in result.get("items", [])
                   if x.get("contentDetails", {}).get("videoId"))
        page = result.get("nextPageToken")
        if not page:
            break

    videos = []
    for start in range(0, len(ids), 50):
        result = youtube("videos", part="snippet,statistics,contentDetails",
                         id=",".join(ids[start:start+50]))
        for video in result.get("items", []):
            stats, snippet = video.get("statistics", {}), video.get("snippet", {})
            duration = seconds(video.get("contentDetails", {}).get("duration"))
            videos.append({
                "id": video["id"], "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt"),
                "duration_seconds": duration,
                "short_candidate": duration is not None and duration <= 180,
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats["likeCount"]) if "likeCount" in stats else None,
                "comments": int(stats["commentCount"]) if "commentCount" in stats else None
            })
    videos.sort(key=lambda x: x.get("published_at") or "", reverse=True)

    # CommentThreads is public, but comment authors and text may be shown on the
    # public static site. Only keep the text necessary for creator suggestions.
    # The private admin UI can show these after login; public build omits comments.
    stats = channel.get("statistics", {})
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "channel": {
            "id": channel["id"], "title": channel["snippet"].get("title", ""),
            "handle": HANDLE,
            "subscribers": int(stats["subscriberCount"]) if "subscriberCount" in stats else None,
            "views": int(stats.get("viewCount", 0)),
            "video_count": int(stats.get("videoCount", 0))
        },
        "videos": videos,
        "notes": "Estadisticas publicas; candidatos a Shorts por duracion, sin confirmar formato."
    }


def main(path=Path("data/channel.json")):
    result = collect_channel()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     delete=False) as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        pending = Path(output.name)
    pending.replace(path)
    print(f"Actualizado {HANDLE}: {len(result['videos'])} videos")


if __name__ == "__main__":
    main()
