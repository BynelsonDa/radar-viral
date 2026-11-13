"""Free-tier collection: public metrics in JSON, no database or long-running worker."""
import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE = 'https://www.googleapis.com/youtube/v3'


def youtube(endpoint, **params):
    key = os.getenv('YOUTUBE_API_KEY')
    if not key:
        raise RuntimeError('Falta el secreto YOUTUBE_API_KEY en GitHub Actions.')
    try:
        response = requests.get(f'{BASE}/{endpoint}',params={**params,'key':key},timeout=30)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException,ValueError):
        raise RuntimeError('YouTube rechazó la consulta; verifica clave, red y cuota. Se conserva la captura anterior.') from None


def seconds(value):
    match=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',value or '')
    if not match:
        return None
    h,m,s=(int(x or 0) for x in match.groups())
    return h*3600+m*60+s


def collect(previous, now=None):
    now=now or datetime.now(timezone.utc)
    stamp=now.isoformat()
    age=max(1,int(os.getenv('MAX_VIDEO_AGE_DAYS','60')))
    cutoff=now-timedelta(days=age)
    # Bound both public JSON size and hourly API use. Expire videos outside the window.
    existing={v['video_id']:v for v in previous.get('videos',[]) if datetime.fromisoformat(v['published_at'].replace('Z','+00:00'))>=cutoff}
    ids=set(existing)
    last=previous.get('last_discovery_at')
    discovery_due=not last or (now-datetime.fromisoformat(last.replace('Z','+00:00'))).total_seconds()>=21600
    if discovery_due:
        terms=[t.strip() for t in os.getenv('SEARCH_TERMS','curiosidades;inteligencia artificial;gaming').split(';') if t.strip()][:7]
        for term in terms:
            result=youtube('search',part='snippet',type='video',q=term,videoDuration='short',order='viewCount',maxResults=25,publishedAfter=cutoff.isoformat())
            ids.update(item['id']['videoId'] for item in result.get('items',[]) if item.get('id',{}).get('videoId'))
    # All tracked videos are refreshed, capped at 500; prioritize recent publications.
    ids=sorted(ids,key=lambda i:existing.get(i,{}).get('published_at',stamp),reverse=True)[:500]
    videos=[]
    for offset in range(0,len(ids),50):
        result=youtube('videos',part='snippet,contentDetails,statistics',id=','.join(ids[offset:offset+50]))
        for item in result.get('items',[]):
            duration=seconds(item.get('contentDetails',{}).get('duration'))
            if duration is None or duration>180:
                continue
            snippet,stats=item['snippet'],item.get('statistics',{})
            if datetime.fromisoformat(snippet['publishedAt'].replace('Z','+00:00'))<cutoff:
                continue
            views=int(stats.get('viewCount',0))
            old=existing.get(item['id'])
            elapsed=(now-datetime.fromisoformat(old['last_seen_at'].replace('Z','+00:00'))).total_seconds() if old else 0
            videos.append({'video_id':item['id'],'title':snippet.get('title',''),
                'channel_title':snippet.get('channelTitle'),'published_at':snippet['publishedAt'],
                'duration_seconds':duration,'view_count':views,
                'like_count':int(stats['likeCount']) if 'likeCount' in stats else None,
                'comment_count':int(stats['commentCount']) if 'commentCount' in stats else None,
                'last_seen_at':stamp,'growth_per_hour':(views-old['view_count'])*3600/elapsed if old and elapsed>0 else None})
    return {'exported_at':stamp,'last_discovery_at':stamp if discovery_due else last,'videos':sorted(videos,key=lambda v:v['video_id'])}


def main(path):
    previous=json.loads(path.read_text()) if path.exists() else {}
    try:
        data=collect(previous)
    except Exception as error:
        # Only known safe messages; never print requests URLs or credentials.
        message=str(error) if type(error) is RuntimeError else 'No se pudo actualizar la captura. Se conserva el archivo anterior.'
        raise SystemExit(message) from None
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False) as file:
        json.dump(data,file,ensure_ascii=False,indent=2)
        temp=Path(file.name)
    temp.replace(path)
    print(f'Captura actualizada: {len(data["videos"])} videos públicos.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/live.json'))
    main(parser.parse_args().output)
