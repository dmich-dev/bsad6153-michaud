"""Regression checks for source-backed example selection and saved-run freshness."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('recording_room', Path(__file__).parents[1] / 'scripts/recording_room.py')
room = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(room)


def write_run(root, name, finished, *, complete=True):
    folder = root / 'data/raw' / name
    (folder / 'catalog').mkdir(parents=True)
    rows = [{'id': 'openai/gpt-4.1', 'created': 100},
            {'id': 'lab/new', 'created': 300},
            {'id': 'lab/unknown', 'created': '9999999999'},
            {'id': 'lab/no-provider', 'created': 500}]
    (folder / 'summary.json').write_text(json.dumps({'finished_at': finished, 'complete': complete}))
    (folder / 'catalog/page-0001.json').write_text(json.dumps({'data': rows}))
    (folder / 'endpoints.json').write_text(json.dumps({'data': [
        {'model_id': row['id'], 'provider_name': 'Provider'} for row in rows[:-1]]}))
    return folder, rows


class RecordingRoomTests(unittest.TestCase):
    def test_newest_related_example_is_not_fixed_and_original_objects_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder, rows = write_run(root, 'run', '2026-11-01T18:00:00+00:00')
            original = (folder / 'catalog/page-0001.json').read_bytes()
            with patch.object(room, 'ROOT', root):
                choices = room.record_from_run(folder)
            self.assertEqual([item['record']['id'] for item in choices], ['lab/new', 'openai/gpt-4.1', 'lab/unknown'])
            self.assertEqual(choices[0]['record'], rows[1])
            self.assertEqual(choices[-1]['catalog_added_at'], 'Unknown')
            self.assertEqual((folder / 'catalog/page-0001.json').read_bytes(), original)

    def test_restart_uses_latest_complete_run_by_timestamp_not_legacy_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_run(root, 'z-old', '2026-11-01T10:00:00+00:00')
            latest, _ = write_run(root, 'a-latest', '2026-11-01T18:00:00+00:00')
            write_run(root, 'newer-incomplete', '2026-11-01T19:00:00+00:00', complete=False)
            with patch.object(room, 'ROOT', root):
                self.assertEqual(room.latest_saved_run(), latest)

    def test_no_related_data_is_reported_instead_of_inventing_an_example(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder, _ = write_run(root, 'run', '2026-11-01T18:00:00+00:00')
            (folder / 'endpoints.json').write_text('{"data": []}')
            with patch.object(room, 'ROOT', root), self.assertRaises(ValueError):
                room.record_from_run(folder)


if __name__ == '__main__':
    unittest.main()
