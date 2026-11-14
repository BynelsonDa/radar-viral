"""Explorador de temas científicos recientes con señales observables.

Los resultados son una muestra de YouTube Search, no un censo ni volumen de
busquedas. El ritmo es un promedio desde la publicacion.
"""
import argparse
import json
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from channel_lab import request_api, duration_seconds, keywords

DEFAULT_TOPICS = [
    "fenomenos cientificos actualidad",
    "espacio astronomia descubrimientos",
    "oceanos clima ciencia",
    "que pasaria si ciencia",
    "curiosidades experimentos ciencia",
]


def discover(topic, days=14, limit=15, now=None):
    now = now or datetime.now(timezone.utc)
    after = (now - timedelta(days=days)).isoformat().replace("+00:00", "Z")
    search = request_api("search", {
        "part": "id,snippet", "type": "video", "q": topic,
        "publishedAfter": after, "order": "date", "maxResults": min(50, limit),
        "relevanceLanguage": "es",
    })
    ids = list(dict.fromkeys(x.get("id", {}).get("videoId") for x in search.get("items", [])))
    ids = [i for i in ids if i]
    if not ids:
        return {"topic": topic, "sample_count": 0, "videos": [], "median_views_per_day": None}
    detail = request_api("videos", {"part": "snippet,contentDetails,statistics", "id": ",".join(ids)})
    rows = []
    for item in detail.get("items", []):
        duration = duration_seconds(item.get("contentDetails", {}).get("duration"))
        if duration is None or duration > 180:
            continue  # candidatos a Shorts, no Shorts confirmados
        snippet = item.get("snippet", {})
        published = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
        days_live = max((now - published).total_seconds() / 86400, 1 / 24)
        views = int(item.get("statistics", {}).get("viewCount", 0))
        rows.append({
            "id": item["id"], "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "views": views, "views_per_day": round(views / days_live, 1),
            "age_days": round(days_live, 2),
            "duration_seconds": duration,
            "url": f"https://www.youtube.com/watch?v={item['id']}",
        })
    values = sorted(r["views_per_day"] for r in rows)
    median = (values[(len(values) - 1) // 2] + values[len(values) // 2]) / 2 if values else None
    rows.sort(key=lambda row: row["views_per_day"], reverse=True)
    for row in rows:
        row["relative_pace"] = round(row["views_per_day"] / median, 2) if median and median > 0 else None
    return {
        "topic": topic, "sample_count": len(rows),
        "median_views_per_day": median,
        "title_keywords": keywords([row["title"] for row in rows]),
        "videos": rows,
        "limitations": "Muestra limitada; no mide retencion ni demanda de busqueda. Vistas/dia no predice rendimiento.",
    }


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--topics", default=";".join(DEFAULT_TOPICS))
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()
    topics = [s.strip() for s in args.topics.split(";") if s.strip()][:5]
    if not topics:
        parser.error("Debes indicar por lo menos un tema.")
    days = max(1, min(90, args.days))
    limit = max(1, min(50, args.limit))
    data = {"generated_at": datetime.now(timezone.utc).isoformat(),
            "topics": [discover(t, days=days, limit=limit) for t in topics],
            "note": "YouTube search cuesta cuota: 100 unidades por consulta y puede no ser exhaustiva."}
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
