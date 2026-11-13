"""One quota-conscious collector worker. Run separately from the web process."""
import argparse
import os
import signal
import threading
from datetime import datetime, timezone

import collector
from database import connect, initialize

stop = threading.Event()


def run_job(name, interval, action):
    """MySQL advisory lock prevents duplicate workers and survives web restarts."""
    conn = connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT GET_LOCK(%s,0)', ('radar_viral_collection',))
            if cursor.fetchone()[0] != 1:
                return False
            cursor.execute('SELECT last_started_at FROM collection_status WHERE job=%s', (name,))
            row = cursor.fetchone()
            if row and row[0] and (datetime.now(timezone.utc).replace(tzinfo=None)-row[0]).total_seconds()<interval:
                return False
            cursor.execute('''INSERT INTO collection_status (job,last_started_at,interval_seconds)
                VALUES (%s,UTC_TIMESTAMP(),%s) ON DUPLICATE KEY UPDATE
                last_started_at=UTC_TIMESTAMP(), interval_seconds=VALUES(interval_seconds)''',(name,interval))
            conn.commit()
        try:
            action()
        except Exception:
            # Never log SDK exceptions, request URLs, passwords or API keys.
            with conn.cursor() as cursor:
                cursor.execute('UPDATE collection_status SET last_error=%s WHERE job=%s',
                    ('Falló la recolección. Revisa conexión, credenciales y cuota de YouTube.',name))
            conn.commit()
            print(f'{name}: fallo; se reintentará en el próximo intervalo.',flush=True)
            return False
        with conn.cursor() as cursor:
            cursor.execute('UPDATE collection_status SET last_success_at=UTC_TIMESTAMP(),last_error=NULL WHERE job=%s',(name,))
        conn.commit()
        return True
    finally:
        # Closing this connection releases the named lock, even after failure.
        conn.close()


def tick():
    refresh = max(300,int(os.getenv('REFRESH_INTERVAL_SECONDS','900')))
    discover = max(3600,int(os.getenv('DISCOVERY_INTERVAL_SECONDS','21600')))
    limit = min(500,max(1,int(os.getenv('REFRESH_MAX_VIDEOS','500'))))
    run_job('refresh', refresh, lambda: collector.refresh_existing(limit))
    run_job('discovery', discover, collector.run)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once',action='store_true',help='Run due jobs once and exit')
    args = parser.parse_args()
    signal.signal(signal.SIGTERM,lambda *_:stop.set())
    signal.signal(signal.SIGINT,lambda *_:stop.set())
    initialize()
    while not stop.is_set():
        try:
            tick()
        except Exception:
            print('MySQL no está disponible. Reintentando en 60 segundos.',flush=True)
            if args.once:
                raise SystemExit(1)
        if args.once:
            break
        stop.wait(60)
