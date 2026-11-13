"""Export a portable HTML dashboard containing a snapshot of public video data."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from dashboard import dashboard_data, json_value, ROOT


def export_site(output):
    first = dashboard_data({})
    videos = first['videos']
    for page in range(2, (first['summary']['total']+23)//24+1):
        videos.extend(dashboard_data({'page':[str(page)]})['videos'])
    snapshot = {'exported_at':datetime.now(timezone.utc).isoformat(),'videos':videos}
    payload = json.dumps(snapshot,default=json_value,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    web = ROOT / 'web'
    html = (web / 'index.html').read_text()
    html = html.replace('<link rel="stylesheet" href="/style.css">', '<style>'+(web/'style.css').read_text()+'</style>')
    scripts = '<script>window.RADAR_SNAPSHOT='+payload+';</script>'
    for filename in ['offline.js','app.js']:
        scripts += '<script>'+ (web/filename).read_text().replace('</script','<\\/script')+'</script>'
    html = html.replace('<script src="/app.js" defer></script>','')
    html = html.replace('</body>',scripts+'</body>')
    html = html.replace('href="/"','href="#overview"')
    html = html.replace('↻ Actualizar datos','↻ Recargar vista')
    html = html.replace('<p id="status"', '<p class="note">VERSIÓN PORTÁTIL · Copia de datos del '+datetime.now(timezone.utc).strftime('%Y-%m-%d')+'. Los filtros funcionan sin conexión; este archivo no incorpora nuevos videos de YouTube.</p><p id="status"')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(html)
    print(f'Exportados {len(videos)} videos a {output}')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    export_site(parser.parse_args().output)
