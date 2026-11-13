"""Local, read-only dashboard. Run with python src/dashboard.py."""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from flask import Flask, Response, request, send_from_directory
from waitress import serve
from database import connect, initialize

import mysql.connector
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')
SORTS = {'views': 'v.view_count', 'recent': 'v.published_at', 'growth': 'growth_per_hour'}


def dashboard_data(params):
    query = params.get('q', [''])[0].strip()[:200]
    days = int(params.get('days', ['0'])[0])
    page = int(params.get('page', ['1'])[0])
    sort = params.get('sort', ['views'])[0]
    if days not in (0, 7, 30, 60) or not 1 <= page <= 10000 or sort not in SORTS:
        raise ValueError('Filtros inválidos')
    conditions, values = [], []
    if query:
        conditions.append('(LOCATE(%s,v.title)>0 OR LOCATE(%s,v.channel_title)>0)')
        values.extend([query, query])
    if days:
        conditions.append('v.published_at >= UTC_TIMESTAMP() - INTERVAL %s DAY')
        values.append(days)
    where = ' WHERE ' + ' AND '.join(conditions) if conditions else ''
    conn = connect()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute('''SELECT COUNT(*) AS total, COALESCE(SUM(v.view_count),0) AS views,
                COUNT(DISTINCT v.channel_title) AS channels, MAX(v.last_seen_at) AS updated
                FROM videos v''' + where, values)
            summary = cursor.fetchone()
            cursor.execute('''WITH ranked AS (
                SELECT video_id, view_count, collected_at,
                ROW_NUMBER() OVER (PARTITION BY video_id ORDER BY collected_at DESC,id DESC) AS rn
                FROM snapshots
            ), growth AS (
                SELECT a.video_id,
                (a.view_count-b.view_count)*3600.0 /
                NULLIF(TIMESTAMPDIFF(SECOND,b.collected_at,a.collected_at),0) AS growth_per_hour
                FROM ranked a JOIN ranked b ON a.video_id=b.video_id AND b.rn=2 WHERE a.rn=1
            ) SELECT v.*, g.growth_per_hour FROM videos v
                LEFT JOIN growth g ON v.video_id=g.video_id''' + where +
                f' ORDER BY {SORTS[sort]} DESC, v.video_id ASC LIMIT 24 OFFSET %s',
                [*values, (page-1)*24])
            videos = cursor.fetchall()
            cursor.execute('''SELECT DATE(v.published_at) AS day, COUNT(*) AS count
                FROM videos v''' + where + ''' GROUP BY DATE(v.published_at)
                ORDER BY day''', values)
            timeline = [{'day': str(row['day']), 'count': row['count']} for row in cursor.fetchall()]
            cursor.execute('''SELECT v.title, v.view_count FROM videos v''' + where +
                ' ORDER BY v.view_count DESC, v.video_id LIMIT 5', values)
            top = cursor.fetchall()
            cursor.execute('''SELECT COALESCE(v.channel_title,'Sin canal') AS name,
                COUNT(*) AS count FROM videos v''' + where +
                ' GROUP BY v.channel_title ORDER BY count DESC, name LIMIT 5', values)
            channels = cursor.fetchall()
            cursor.execute('''SELECT WEEKDAY(v.published_at) AS weekday,
                HOUR(v.published_at) DIV 4 AS slot, COUNT(*) AS count FROM videos v''' +
                (where + ' AND ' if where else ' WHERE ') +
                'v.published_at IS NOT NULL GROUP BY weekday, slot', values)
            heatmap = cursor.fetchall()
            cursor.execute('SELECT v.* FROM videos v' + where, values)
            idea_videos = cursor.fetchall()
            return {'idea_videos':idea_videos, 'summary': summary, 'videos': videos, 'page': page, 'page_size': 24,
                    'charts': {'timeline': timeline, 'top': top, 'channels': channels, 'heatmap': heatmap}}
    finally:
        conn.close()


def json_value(value):
    if isinstance(value, datetime):
        return value.isoformat() + 'Z'  # YouTube and collector timestamps are UTC.
    return float(value)


app = Flask(__name__, static_folder=None)


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Cache-Control'] = 'no-store'
    return response


def json_response(payload, status=200):
    return Response(json.dumps(payload, default=json_value, ensure_ascii=False),
                    status=status, mimetype='application/json')


@app.get('/api/videos')
def videos_api():
    try:
        return json_response(dashboard_data(parse_qs(request.query_string.decode())))
    except (ValueError, UnicodeError):
        return json_response({'error':'Filtros inválidos.'},400)
    except mysql.connector.Error:
        return json_response({'error':'No se pudo consultar MySQL. Reintenta en unos momentos.'},503)


@app.get('/api/status')
def status_api():
    try:
        conn = connect()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute('SELECT job,last_started_at,last_success_at,last_error,interval_seconds FROM collection_status ORDER BY job')
                return json_response({'jobs':cursor.fetchall()})
        finally:
            conn.close()
    except mysql.connector.Error:
        return json_response({'error':'No se pudo consultar el estado de actualización.'},503)


@app.get('/health')
def health():
    try:
        conn = connect()
        conn.close()
        return json_response({'status':'ok'})
    except mysql.connector.Error:
        return json_response({'status':'database_unavailable'},503)


@app.get('/')
@app.get('/<path:filename>')
def static_file(filename='index.html'):
    if filename not in ('index.html','app.js','style.css','ideas.js'):
        return json_response({'error':'No encontrado'},404)
    return send_from_directory(ROOT / 'web',filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=int(os.getenv('PORT','8000')))
    args=parser.parse_args()
    initialize()
    print(f'Radar Viral iniciado en el puerto {args.port}',flush=True)
    serve(app,host=args.host,port=args.port,threads=4,url_scheme='https' if os.getenv('RENDER') else 'http')
