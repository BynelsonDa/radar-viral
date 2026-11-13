"""Build a free static dashboard; no secrets, database or dependencies required."""
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def build(output):
    web=ROOT/'src/web'
    output.mkdir(parents=True,exist_ok=True)
    html=(web/'index.html').read_text().replace('href="/"','href="./"')
    html=html.replace('href="/style.css"','href="./style.css"')
    html=html.replace('<script src="/ideas.js" defer></script>','<script src="./ideas.js" defer></script>')
    html=html.replace('<script src="/app.js" defer></script>', '<script>window.RADAR_LIVE_FILE="./data/live.json";</script><script src="./offline.js" defer></script><script src="./app.js" defer></script>')
    (output/'index.html').write_text(html)
    for filename in ['style.css','app.js','offline.js','ideas.js']:
        shutil.copyfile(web/filename,output/filename)
    (output/'data').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'data/live.json',output/'data/live.json')
    print('Sitio estático generado; no incluye credenciales.')


if __name__=='__main__':
    build(ROOT/'public')
