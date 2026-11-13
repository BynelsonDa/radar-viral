"""Integration tests: require the configured MySQL database and schema."""
import sys
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dashboard import dashboard_data
import mysql.connector
import os


class DashboardIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.marker = 'test-' + uuid.uuid4().hex[:10]
        cls.ids = [f'{cls.marker}-{i}' for i in range(25)]
        cls.conn = mysql.connector.connect(host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', '3306')), user=os.getenv('DB_USER', 'radar'),
            password=os.getenv('DB_PASSWORD', ''), database=os.getenv('DB_NAME', 'radar_viral'))
        cursor = cls.conn.cursor()
        for i, video_id in enumerate(cls.ids):
            cursor.execute('INSERT INTO videos (video_id,title,channel_title,published_at,duration_seconds,view_count) VALUES (%s,%s,%s,UTC_TIMESTAMP(),30,%s)',
                (video_id, cls.marker, cls.marker, 100+i))
        for views, timestamp in [(100, '2026-01-01 01:00:00'), (160, '2026-01-01 02:00:00')]:
            cursor.execute('INSERT INTO snapshots (video_id,view_count,collected_at) VALUES (%s,%s,%s)', (cls.ids[0],views,timestamp))
        cls.conn.commit()
        cursor.close()

    @classmethod
    def tearDownClass(cls):
        cursor = cls.conn.cursor()
        for video_id in cls.ids:
            cursor.execute('DELETE FROM snapshots WHERE video_id=%s', (video_id,))
            cursor.execute('DELETE FROM videos WHERE video_id=%s', (video_id,))
        cls.conn.commit()
        cursor.close()
        cls.conn.close()

    def test_filtered_summary_sort_and_pagination(self):
        data = dashboard_data({'q':[self.marker]})
        self.assertEqual(data['summary']['total'], 25)
        self.assertEqual(int(data['summary']['views']), sum(range(100,125)))
        self.assertEqual(len(data['videos']), 24)
        self.assertEqual(data['videos'][0]['view_count'],124)
        second = dashboard_data({'q':[self.marker], 'page':['2']})
        self.assertEqual(len(second['videos']),1)
        self.assertEqual(second['videos'][0]['video_id'], self.ids[0])

    def test_growth_and_missing_measurements(self):
        data = dashboard_data({'q':[self.marker], 'sort':['growth'], 'days':['7']})
        self.assertEqual(data['videos'][0]['video_id'], self.ids[0])
        self.assertEqual(float(data['videos'][0]['growth_per_hour']), 60)
        self.assertIsNone(data['videos'][1]['growth_per_hour'])

    def test_invalid_filters(self):
        for params in [{'sort':['bad']}, {'page':['0']}, {'days':['-1']}]:
            with self.assertRaises(ValueError):
                dashboard_data(params)

    def test_search_is_literal(self):
        data = dashboard_data({'q':[self.marker + "' OR 1=1 --"]})
        self.assertEqual(data['summary']['total'],0)
        self.assertEqual(data['videos'],[])

    def test_charts_use_all_filtered_results(self):
        data = dashboard_data({'q':[self.marker]})
        charts = data['charts']
        self.assertEqual(sum(row['count'] for row in charts['timeline']),25)
        self.assertEqual(sum(row['count'] for row in charts['heatmap']),25)
        self.assertEqual(charts['channels'],[{'name':self.marker,'count':25}])
        self.assertEqual(len(charts['top']),5)
        self.assertEqual(charts['top'][0]['view_count'],124)
        self.assertEqual(charts, dashboard_data({'q':[self.marker],'page':['2']})['charts'])


if __name__ == '__main__':
    unittest.main()
