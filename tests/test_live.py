import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import collector
from dashboard import app
from database import connect, initialize
from worker import run_job


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize()

    def test_http_routes(self):
        client=app.test_client()
        self.assertEqual(client.get('/health').status_code,200)
        self.assertEqual(client.get('/api/status').status_code,200)
        self.assertEqual(client.get('/api/videos?days=-1').status_code,400)
        self.assertEqual(client.get('/.env').status_code,404)
        self.assertEqual(client.get('/database.py').status_code,404)
        with client.get('/') as response:
            self.assertEqual(response.status_code,200)

    def test_api_errors_hide_secrets(self):
        with patch.dict('os.environ',{'YOUTUBE_API_KEY':'test-secret-never-log'}):
            with patch('collector.requests.get',side_effect=requests.ConnectionError('https://api?key=test-secret-never-log')):
                with self.assertRaises(RuntimeError) as caught:
                    collector.youtube('videos')
                self.assertNotIn('test-secret',str(caught.exception))

    def test_worker_persists_interval_and_does_not_repeat(self):
        conn=connect()
        try:
            with conn.cursor() as c:
                c.execute('DELETE FROM collection_status WHERE job=%s',('test_interval',))
            conn.commit()
            calls=[]
            self.assertTrue(run_job('test_interval',900,lambda:calls.append(1)))
            self.assertFalse(run_job('test_interval',900,lambda:calls.append(2)))
            self.assertEqual(calls,[1])
        finally:
            with conn.cursor() as c:
                c.execute('DELETE FROM collection_status WHERE job=%s',('test_interval',))
            conn.commit();conn.close()

    def test_worker_failure_keeps_error_and_releases_lock(self):
        conn=connect()
        try:
            with conn.cursor() as c:
                c.execute('DELETE FROM collection_status WHERE job=%s',('test_failure',))
            conn.commit()
            def fail():
                raise RuntimeError('sensitive-request-url')
            self.assertFalse(run_job('test_failure',900,fail))
            with conn.cursor() as c:
                conn.commit()
                c.execute('SELECT last_error,last_success_at FROM collection_status WHERE job=%s',('test_failure',))
                error,success=c.fetchone()
                self.assertNotIn('sensitive-request-url',error)
                self.assertIsNone(success)
                c.execute("SELECT GET_LOCK('radar_viral_collection',0)")
                self.assertEqual(c.fetchone()[0],1)
                c.execute("SELECT RELEASE_LOCK('radar_viral_collection')")
                c.fetchone()
        finally:
            with conn.cursor() as c:
                c.execute('DELETE FROM collection_status WHERE job=%s',('test_failure',))
            conn.commit();conn.close()


if __name__=='__main__':
    unittest.main()
