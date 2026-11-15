"""Auditoría pública de un Short específico y comparación con @Neutrinitoo.

Uso:
  python src/analyze_short.py --video-id=-XyEojvQhkQ
  python src/analyze_short.py --video-id=-XyEojvQhkQ --output data/short-audit.json

Requiere YOUTUBE_API_KEY. Nunca imprime ni almacena la clave.
"""
import argparse
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from collect_channel_static import collect_channel
from collect_static import youtube, seconds


def age_days(iso_date, now):
    if not iso_date:
        return None
    published = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return max((now - published).total_seconds() / 86400, 1 / 24)


def summarize(video, now):
    snippet = video.get("snippet", {})
    stats = video.get("statistics", {})
    duration = seconds(video.get("contentDetails", {}).get("duration"))
    views = int(stats.get("viewCount", 0))
    likes = int(stats["likeCount"]) if "likeCount" in stats else None
    comments = int(stats["commentCount"]) if "commentCount" in stats else None
    days = age_days(snippet.get("publishedAt"), now)
    return {
        "id": video["id"], "title": snippet.get("title", ""),
        "published_at": snippet.get("publishedAt"),
        "duration_seconds": duration,
        "short_candidate": duration is not None and duration <= 180,
        "views": views, "likes": likes, "comments": comments,
        "likes_per_1000_views": round(likes * 1000 / views, 2) if views and likes is not None else None,
        "comments_per_1000_views": round(comments * 1000 / views, 2) if views and comments is not None else None,
        "views_per_day": round(views / days, 2) if days else None,
        "url": f"https://www.youtube.com/shorts/{video['id']}",
        "channel_id": snippet.get("channelId")
    }


def audit(video_id="-XyEojvQhkQ"):
    now = datetime.now(timezone.utc)
    result = youtube("videos", part="snippet,statistics,contentDetails", id=video_id)
    items = result.get("items", [])
    if not items:
        raise RuntimeError("El video no esta disponible mediante la API publica.")
    target = summarize(items[0], now)
    channel = collect_channel()
    if target["channel_id"] != channel["channel"]["id"]:
        raise RuntimeError("El video indicado no pertenece al canal @Neutrinitoo configurado.")

    # Se comparan candidatos de duración <= 180 s; la API no marca un Short
    # de manera inequívoca. No mezclar métricas de videos largos.
    peers = [v for v in channel["videos"]
             if v["id"] != video_id and v.get("short_candidate")]
    peer_views = [v["views"] for v in peers]
    peer_rates = []
    for v in peers:
        days = age_days(v.get("published_at"), now)
        if days:
            peer_rates.append(v["views"] / days)

    median_views = statistics.median(peer_views) if peer_views else None
    median_rate = statistics.median(peer_rates) if peer_rates else None
    observations = []
    if median_views is not None:
        relation = "por encima" if target["views"] > median_views else (
            "por debajo" if target["views"] < median_views else "igual")
        observations.append(f"Sus vistas estan {relation} de la mediana de los otros candidatos a Shorts.")
    if target["views"] < 1000:
        observations.append("El video aun no alcanza las 1.000 vistas publicas en esta captura.")
    else:
        observations.append("El video ha alcanzado al menos 1.000 vistas publicas en esta captura.")
    observations.append("La velocidad vistas/dia es un promedio desde la publicacion, no crecimiento reciente.")
    observations.append("Estas cifras no demuestran la causa de la distribucion: falta retencion, impresiones y visualizaciones elegidas frente a deslizadas.")
    return {
        "generated_at": now.isoformat(),
        "channel": channel["channel"],
        "target": target,
        "comparison": {
            "other_short_candidates": len(peers),
            "median_peer_views": median_views,
            "median_peer_views_per_day": round(median_rate, 2) if median_rate is not None else None,
            "target_percentile_by_views": round(
                100 * sum(v <= target["views"] for v in peer_views) / len(peer_views), 1
            ) if peer_views else None,
        },
        "observations": observations,
        "limitations": [
            "La duracion <= 180 segundos aproxima la categoria Shorts, sin certificarla.",
            "Solo se comparan los ultimos 100 uploads publicos recuperados.",
            "Las vistas publicas no son la metrica de visualizaciones con interaccion.",
            "YouTube Data API v3 no ofrece la curva de retencion ni el porcentaje que deslizo.",
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video-id", default="-XyEojvQhkQ")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.video_id)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Informe guardado en {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
