"""Canal Neutrinitoo: auditoria publica y borradores de respuestas.

Solo consulta datos con API key. Publicar respuestas requiere OAuth y un comando
explicito; nunca se publican sugerencias automaticamente.
"""
import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE = "https://www.googleapis.com/youtube/v3"
HANDLE = "@Neutrinitoo"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def request_api(endpoint, params, token=None, session=None):
    session = session or requests
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    payload = dict(params)
    if not token:
        key = os.getenv("YOUTUBE_API_KEY")
        if not key:
            raise RuntimeError("Configura YOUTUBE_API_KEY en .env")
        payload["key"] = key
    try:
        response = session.get(f"{BASE}/{endpoint}", params=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        # No se incluyen URLs ni tokens, porque podrian exponer credenciales.
        raise RuntimeError(f"Fallo la consulta de YouTube ({type(exc).__name__}). Revisa cuota y permisos.") from None


def channel_details(handle=HANDLE):
    data = request_api("channels", {"part": "snippet,statistics,contentDetails", "forHandle": handle})
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"No se encontro el canal {handle}")
    return items[0]


def channel_videos(channel, max_videos=100):
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], None
    while len(ids) < max_videos:
        params = {"part": "contentDetails", "playlistId": playlist,
                  "maxResults": min(50, max_videos - len(ids))}
        if page:
            params["pageToken"] = page
        data = request_api("playlistItems", params)
        ids.extend(x["contentDetails"]["videoId"] for x in data.get("items", [])
                   if x.get("contentDetails", {}).get("videoId"))
        page = data.get("nextPageToken")
        if not page:
            break
    videos = []
    for offset in range(0, len(ids), 50):
        data = request_api("videos", {"part": "snippet,statistics,contentDetails",
                                      "id": ",".join(ids[offset:offset + 50])})
        videos.extend(data.get("items", []))
    return videos


def duration_seconds(value):
    m = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value or "")
    if not m:
        return None
    d, h, minute, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + minute * 60 + s


def video_rows(videos):
    rows = []
    for v in videos:
        sn = v.get("snippet", {})
        st = v.get("statistics", {})
        secs = duration_seconds(v.get("contentDetails", {}).get("duration"))
        views = int(st.get("viewCount", 0))
        likes = int(st["likeCount"]) if "likeCount" in st else None
        comments = int(st["commentCount"]) if "commentCount" in st else None
        rows.append({
            "id": v["id"], "title": sn.get("title", ""), "published_at": sn.get("publishedAt"),
            "duration_seconds": secs, "short_candidate": secs is not None and secs <= 180,
            "views": views, "likes": likes, "comments": comments,
            "likes_per_1000_views": round(likes * 1000 / views, 2) if views and likes is not None else None,
            "url": f"https://www.youtube.com/watch?v={v['id']}",
        })
    return sorted(rows, key=lambda r: r["views"], reverse=True)


def public_audit(handle=HANDLE, max_videos=100):
    channel = channel_details(handle)
    rows = video_rows(channel_videos(channel, max_videos))
    stats = channel.get("statistics", {})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel": {"id": channel["id"], "title": channel["snippet"]["title"],
                    "handle_requested": handle, "subscribers": stats.get("subscriberCount"),
                    "total_views": stats.get("viewCount"), "video_count": stats.get("videoCount")},
        "videos": rows,
        "notes": ["La duracion <=180 s solo identifica candidatos, no confirma Shorts.",
                  "La API publica no expone retencion ni vistas del feed de Shorts.",
                  "Las estadisticas son una captura, no tendencias temporales sin historico."],
    }


def recent_comments(video_id, limit=50):
    comments, page = [], None
    while len(comments) < limit:
        params = {"part": "snippet", "videoId": video_id,
                  "maxResults": min(100, limit - len(comments)), "order": "time",
                  "textFormat": "plainText"}
        if page:
            params["pageToken"] = page
        data = request_api("commentThreads", params)
        for item in data.get("items", []):
            top = item["snippet"]["topLevelComment"]
            sn = top["snippet"]
            comments.append({"id": top["id"], "video_id": video_id,
                             "author": sn.get("authorDisplayName", ""),
                             "text": sn.get("textDisplay", ""), "like_count": sn.get("likeCount", 0),
                             "published_at": sn.get("publishedAt")})
        page = data.get("nextPageToken")
        if not page:
            break
    return comments[:limit]


STOPWORDS = {"para", "porque", "como", "pero", "esto", "este", "esta", "sobre", "desde",
             "todo", "todos", "tiene", "video", "short", "shorts", "ciencia",
             "entonces", "seria", "puede", "hacer", "cual", "cuando", "donde"}


def keywords(titles, n=10):
    words = Counter()
    for title in titles:
        normalized = title.lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
        words.update(w for w in re.findall(r"[a-z]{4,}", normalized)
                     if w not in STOPWORDS)
    return [{"term": word, "mentions": count} for word, count in words.most_common(n)]


def suggest_reply(text, video_title="", trends=()):
    """Borrador determinista: no inventa hechos cientificos ni hace spam."""
    message = text.strip()
    low = message.lower()
    if any(x in low for x in ["idiota", "estupido", "imbecil", "mierda"]):
        return {"category": "moderation", "suggestion": None,
                "reason": "Revisar manualmente; evitar amplificar ataques."}
    if "?" in message or "¿" in message:
        return {"category": "question",
                "suggestion": "¡Buena pregunta! La voy a investigar con fuentes confiables para responderla bien. 🔬",
                "reason": "No afirmar respuestas cientificas sin verificarlas."}
    if any(x in low for x in ["falso", "mentira", "incorrecto", "error"]):
        return {"category": "correction",
                "suggestion": "Gracias por señalarlo. ¿Qué parte te parece incorrecta? Voy a contrastarla con fuentes. 🔎",
                "reason": "Invitar a una correccion verificable."}
    if any(x in low for x in ["parte 2", "otro video", "mas videos", "más videos"]):
        return {"category": "idea",
                "suggestion": "¡Gracias por la idea! ¿Qué pregunta te gustaría que investigáramos en el siguiente Short? 🌎",
                "reason": "Recoger ideas sin prometer publicaciones."}
    return {"category": "general",
            "suggestion": "¡Gracias por ver el video! 🙌 ¿Qué otra curiosidad científica te gustaría explorar?",
            "reason": "Invitar a una conversacion genuina."}


def oauth_credentials():
    """OAuth instalado, exclusivamente local. Nunca guardar token en Git."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        raise RuntimeError("Instala requirements-channel.txt para OAuth.") from None
    token_file = Path(os.getenv("YOUTUBE_OAUTH_TOKEN_FILE", ".youtube-token.json"))
    client_file = os.getenv("YOUTUBE_OAUTH_CLIENT_FILE", "client_secret.json")
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not Path(client_file).is_file():
            raise RuntimeError("Falta el archivo local de cliente OAuth.")
        creds = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES).run_local_server(port=0)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    try:
        token_file.chmod(0o600)
    except OSError:
        pass
    return creds


def publish_reply(comment_id, message):
    """Solo invocable desde CLI con --confirm-publish."""
    if not comment_id or not message.strip():
        raise ValueError("Se requiere comentario y respuesta no vacia.")
    creds = oauth_credentials()
    # Se confirma que el usuario OAuth corresponde al canal configurado.
    identity = request_api("channels", {"part": "id", "mine": "true"}, token=creds.token)
    owner_id = channel_details(os.getenv("YOUTUBE_CHANNEL_HANDLE", HANDLE))["id"]
    if owner_id not in [x["id"] for x in identity.get("items", [])]:
        raise RuntimeError("La cuenta autorizada no controla el canal configurado.")
    try:
        response = requests.post(
            f"{BASE}/comments", params={"part": "snippet"},
            headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
            json={"snippet": {"parentId": comment_id, "textOriginal": message}},
            timeout=30)
        response.raise_for_status()
        return response.json().get("id")
    except requests.RequestException:
        raise RuntimeError("No fue posible publicar la respuesta; revisa permisos y cuota.") from None


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Auditoria y respuestas sugeridas para Neutrinitoo")
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("audit")
    a.add_argument("--handle", default=os.getenv("YOUTUBE_CHANNEL_HANDLE", HANDLE))
    a.add_argument("--limit", type=int, default=100)
    c = sub.add_parser("comments")
    c.add_argument("--video-id", required=True)
    c.add_argument("--limit", type=int, default=50)
    p = sub.add_parser("publish")
    p.add_argument("--comment-id", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--confirm-publish", action="store_true", required=True)
    args = parser.parse_args()
    if args.command == "audit":
        result = public_audit(args.handle, min(500, max(1, args.limit)))
        result["title_keywords"] = keywords([r["title"] for r in result["videos"]])
    elif args.command == "comments":
        comments = recent_comments(args.video_id, min(100, max(1, args.limit)))
        result = {"comments": [{**c, "draft": suggest_reply(c["text"])} for c in comments],
                  "warning": "Son sugerencias. Ninguna respuesta fue publicada."}
    else:
        if not args.confirm_publish:
            parser.error("Publicar requiere --confirm-publish.")
        result = {"published_comment_id": publish_reply(args.comment_id, args.text)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
