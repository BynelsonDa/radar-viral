import json
import sys
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import collect_static


class StaticCollectorTests(unittest.TestCase):
    now=datetime(2026,11,13,12,tzinfo=timezone.utc)

    def previous(self):
        return {'last_discovery_at':self.now.isoformat(),'videos':[{
            'video_id':'test123','title':'old','published_at':(self.now-timedelta(days=1)).isoformat(),
            'last_seen_at':(self.now-timedelta(hours=1)).isoformat(),'view_count':100}]}

    def response(self,duration='PT1M'):
        return {'items':[{'id':'test123','snippet':{'title':'updated','publishedAt':(self.now-timedelta(days=1)).isoformat(),'channelTitle':'Channel'},
            'contentDetails':{'duration':duration},'statistics':{'viewCount':'160'}}]}

    def test_refresh_without_repeating_expensive_searches(self):
        with patch('collect_static.youtube',return_value=self.response()) as api:
            result=collect_static.collect(self.previous(),self.now)
        self.assertEqual(api.call_count,1)
        self.assertEqual(api.call_args.args[0],'videos')
        self.assertEqual(result['videos'][0]['growth_per_hour'],60)
        self.assertIsNone(result['videos'][0]['like_count'])

    def test_filters_long_videos(self):
        with patch('collect_static.youtube',return_value=self.response('PT4M')):
            self.assertEqual(collect_static.collect(self.previous(),self.now)['videos'],[])

    def test_first_collection_discovers_and_has_no_fake_growth(self):
        def api(endpoint,**params):
            if endpoint=='search':
                return {'items':[{'id':{'videoId':'test123'}}]}
            return self.response()
        with patch('collect_static.youtube',side_effect=api),patch.dict('os.environ',{'SEARCH_TERMS':'curiosidades'}):
            result=collect_static.collect({},self.now)
        self.assertEqual(len(result['videos']),1)
        self.assertIsNone(result['videos'][0]['growth_per_hour'])
        self.assertEqual(result['last_discovery_at'],self.now.isoformat())

    def test_failed_collection_preserves_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'live.json'
            before=json.dumps(self.previous())
            path.write_text(before)
            with patch('collect_static.collect',side_effect=RuntimeError('Cuota agotada')):
                with self.assertRaises(SystemExit):
                    collect_static.main(path)
            self.assertEqual(path.read_text(),before)


if __name__=='__main__':
    unittest.main()
