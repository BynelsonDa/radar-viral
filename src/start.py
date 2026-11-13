"""Wait for the database schema, then replace this process with web or worker."""
import os
import sys
import time
from database import initialize

mode = sys.argv[1] if len(sys.argv)>1 else 'web'
if mode not in ('web','worker'):
    raise SystemExit('Expected web or worker')
for attempt in range(24):
    try:
        initialize()
        break
    except Exception:
        if attempt == 23:
            raise SystemExit('MySQL no está disponible; revisa DB_* y el servicio privado.')
        print('Esperando MySQL…',flush=True)
        time.sleep(5)
args = [sys.executable, 'src/dashboard.py', '--host','0.0.0.0'] if mode=='web' else [sys.executable,'src/worker.py']
os.execv(sys.executable,args)
