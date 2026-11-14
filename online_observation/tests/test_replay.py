"""Check delivery, archive scope, and causal replay outputs."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from online_observation import causal_replay, measurements
from online_observation.__main__ import main
from online_observation.association_probe import birth_candidates, evaluate_births
from online_observation.fusion_probe import _forecasts
from online_observation.positions import event_batches
from online_observation.registration_probe import estimate_translation
from online_observation.stream import StreamState


HEADER = 'batch,source,time,lat,lon,vel,cou\n'


class CausalReplayCliTests(unittest.TestCase):
    def test_normal_entry_releases_only_current_rows_and_keeps_empty_ticks(self):
        with tempfile.TemporaryDirectory() as directory:
            measurements = Path(directory) / 'measurements.csv'
            output = Path(directory) / 'replay.jsonl'
            measurements.write_text(HEADER + 'future,B,3,0,0,10,90\n'
                                    'before,B,-0.1,0,0,10,90\n'
                                    'moving,A,1.2,0,0,10,90\n'
                                    'moving,A,2,0,1,10,90\n'
                                    'later,C,4.1,0,0,10,90\n', encoding='utf-8')
            args = ['causal-replay', '--measurements', str(measurements), '--start', '0', '--stop', '4',
                    '--stale-after-seconds', '3', '--output', str(output)]
            self.assertEqual(main(args), 0)
            original = output.read_text(encoding='utf-8')
            protocol, *ticks = map(json.loads, original.splitlines())
            self.assertEqual(protocol['arrival_clock'], 'ideal_measurement_time')
            self.assertFalse(protocol['warmup'])
            self.assertEqual(protocol['source_rows'], 5)
            self.assertEqual(protocol['scheduled_rows'], 3)
            self.assertEqual([row['result']['query_time'] for row in ticks], list(range(5)))
            self.assertEqual([row['received_rows'] for row in ticks], [0, 0, 2, 1, 0])
            self.assertEqual([len(row['result']['tracks']) for row in ticks], [0, 0, 1, 2, 2])
            moving = next(track for track in ticks[4]['result']['tracks'] if track['batch'] == 'moving')
            self.assertEqual(moving['observation_time'], 2)
            self.assertGreater(moving['longitude'], 1)

            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                main(args)
            self.assertEqual(result.exception.code, 2)
            self.assertEqual(output.read_text(encoding='utf-8'), original)

    def test_unschedulable_time_fails_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            measurements = Path(directory) / 'bad.csv'
            output = Path(directory) / 'replay.jsonl'
            measurements.write_text(HEADER + 'x,A,nan,0,0,1,90\n', encoding='utf-8')
            with redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit) as result:
                main(['causal-replay', '--measurements', str(measurements), '--start', '0', '--stop', '0',
                      '--stale-after-seconds', '1', '--output', str(output)])
            self.assertEqual(result.exception.code, 2)
            self.assertIn('no schedulable time', stderr.getvalue())
            self.assertFalse(output.exists())

    def test_archive_only_opens_measurement_and_refuses_reclassified_test_scene(self):
        splits = dict(T_core=['0'], T_head=[], V_select=[], T_test=['1'])
        manifest = dict(dataset_level='Level1', all_scenes=['0', '1'], splits=splits,
                        caps={split: len(ids) for split, ids in splits.items()},
                        components={'0': 'a', '1': 'b'}, component_members={'a': ['0'], 'b': ['1']},
                        component_splits={'a': 'T_core', 'b': 'T_test'},
                        label_members={'0': {}, '1': {}}, development_scenes=['0'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path, roster = root / 'data.zip', root / 'manifest.json'
            roster.write_text(json.dumps(manifest), encoding='utf-8')
            with zipfile.ZipFile(archive_path, 'w') as archive:
                for scene in manifest['all_scenes']:
                    archive.writestr(f'Level1/关联表/关联结果-{scene}.csv', 'unreadable label')
                    archive.writestr(f'Level1/真实场景/场景-{scene}.csv', 'unreadable reference')
                    archive.writestr(f'Level1/量测场景/场景-{scene}.csv',
                                     (HEADER + '片段,A,0,0,0,1,90\n').encode('gb18030'))
            measurement_name = 'Level1/量测场景/场景-0.csv'
            with zipfile.ZipFile(archive_path) as archive:
                measurement_offset = archive.getinfo(measurement_name).header_offset
            payload = archive_path.read_bytes()
            header_end = payload.index(HEADER.encode('ascii'), measurement_offset) + len(HEADER)
            cuts = (0, measurement_offset + 11, header_end + 1, len(payload))
            parts = [root / f'part{i}.zip' for i in range(3)]
            for part, start, stop in zip(parts, cuts, cuts[1:]):
                part.write_bytes(payload[start:stop])
            opened = []
            read = zipfile.ZipFile.read

            def record_read(archive, member, *args, **kwargs):
                opened.append(member.filename)
                return read(archive, member, *args, **kwargs)

            with patch.object(measurements, '_LEVEL1_MANIFEST', roster), \
                    patch.object(zipfile.ZipFile, 'read', record_read):
                rows = measurements.read_archive_rows([archive_path], roster, '0')
                self.assertEqual(rows[0]['batch'], '片段')
                self.assertEqual(measurements.read_archive_rows(parts, roster, '0'), rows)
                self.assertEqual(opened, [measurement_name, measurement_name])
                with self.assertRaises((ValueError, zipfile.BadZipFile)):
                    measurements.read_archive_rows(parts[-1:], roster, '0')
                forged = root / 'alternate.json'
                alternate = {**manifest, 'splits': {**splits, 'T_core': ['1'], 'T_test': ['0']},
                             'component_splits': {'a': 'T_test', 'b': 'T_core'},
                             'development_scenes': ['1']}
                forged.write_text(json.dumps(alternate), encoding='utf-8')
                with self.assertRaises(ValueError):
                    measurements.read_archive_rows([archive_path], forged, '1')
                self.assertEqual(opened, [measurement_name, measurement_name])

    def test_public_entry_runs_without_offline_tree_or_site_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = Path(causal_replay.__file__).parent
            shutil.copytree(package, root / package.name,
                            ignore=shutil.ignore_patterns('tests', '__pycache__'))
            source = root / 'input.zip'
            output = root / 'output.jsonl'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('Level1/量测场景/场景-0.csv', HEADER + 'x,A,0,0,0,1,90\n')
            roster = root / package.name / 'data' / 'mtad-level1-scene3000.json'
            roster.write_text(json.dumps(dict(
                dataset_level='Level1', all_scenes=['0'],
                splits=dict(T_core=['0'], T_head=[], V_select=[], T_test=[]),
            )), encoding='utf-8')
            isolated_entry = (
                'import runpy, sys\n'
                'sys.path.insert(0, sys.argv.pop(1))\n'
                'runpy.run_module("online_observation", run_name="__main__", alter_sys=True)\n'
            )
            completed = subprocess.run(
                [sys.executable, '-I', '-S', '-c', isolated_entry, str(root),
                 'causal-replay', '--archive', str(source), '--manifest', str(roster), '--scene', '0',
                 '--start', '0', '--stop', '1', '--stale-after-seconds', '2', '--output', str(output)],
                cwd=root, capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            _, *ticks = map(json.loads, output.read_text(encoding='utf-8').splitlines())
            self.assertEqual([row['result']['query_time'] for row in ticks], [0, 1])
            self.assertGreater(ticks[1]['result']['tracks'][0]['longitude'], 0)

    def test_virtual_serial_queue_accumulates_and_drains_without_changing_ticks(self):
        # Two 1.5s services accumulate a queue. Subsequent 0.2s services drain it.
        clock = iter((0, 1500000000, 1500000000, 3000000000, 3000000000, 3200000000,
                      3200000000, 3400000000, 3400000000, 3600000000))
        out = io.StringIO()
        causal_replay._write_ticks(out, StreamState(stale_after_seconds=10), [], 20, 24,
                                   clock_ns=lambda: next(clock))
        ticks = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([row['result']['query_time'] for row in ticks], [20, 21, 22, 23, 24])
        for row, wait, latency in zip(ticks, (0., .5, 1., .2, 0.), (1.5, 2., 1.2, .4, .2)):
            self.assertAlmostEqual(row['timing']['modeled_queue_wait_seconds'], wait)
            self.assertAlmostEqual(row['timing']['modeled_result_latency_seconds'], latency)


def stream_row(time, *, source="9001", batch="0", lat="0", lon="0", vel="10", cou="90"):
    return dict(time=str(time), source=source, batch=batch, lat=lat, lon=lon, vel=vel, cou=cou)


class StreamTests(unittest.TestCase):
    def test_empty_cold_start_and_no_arrival_prediction(self):
        state = StreamState(stale_after_seconds=2)
        self.assertEqual(state.predict(0)["tracks"], [])
        state.ingest([stream_row(1)], arrival_time=1)
        track = state.predict(1)["tracks"][0]
        self.assertTrue(track["appeared"])
        self.assertTrue(track["latest_observation_updated"])
        self.assertFalse(track["predicted"])
        self.assertEqual(track["longitude"], 0)
        self.assertAlmostEqual(track["speed_mps"], 5.144444444444444)
        current = state.predict(2)
        track = current["tracks"][0]
        self.assertEqual(current["query_time"], 2)
        self.assertFalse(track["appeared"])
        self.assertFalse(track["latest_observation_updated"])
        self.assertTrue(track["predicted"])
        self.assertAlmostEqual(track["longitude"], 0.0000462651)
        self.assertEqual(len(state.predict(3)["tracks"]), 1)
        self.assertEqual(state.predict(4)["disappeared"],
                         [dict(source="9001", batch="0", reason="stale")])
        state.ingest([stream_row(5)], arrival_time=5)
        self.assertTrue(state.predict(5)["tracks"][0]["appeared"])

    def test_late_arrival_keeps_latest_event_and_does_not_reactivate_stale_track(self):
        state = StreamState(stale_after_seconds=2)
        state.ingest([stream_row(2)], arrival_time=2)
        state.predict(2)
        state.ingest([stream_row(1, lon="20")], arrival_time=3)
        track = state.predict(3)["tracks"][0]
        self.assertEqual(track["observation_time"], 2)
        self.assertEqual(track["arrival_time"], 2)
        self.assertFalse(track["latest_observation_updated"])
        state.predict(5)
        state.ingest([stream_row(4)], arrival_time=8)
        self.assertEqual(state.predict(8)["tracks"], [])

    def test_duplicate_and_late_conflict_apply_from_arrival(self):
        state = StreamState(stale_after_seconds=5)
        first = stream_row(0, cou="0")
        state.ingest([first, first, stream_row(0, source="9002")], arrival_time=0)
        published = state.predict(0)
        self.assertEqual(published["audit"]["exact_duplicate_rows_removed"], 1)
        self.assertEqual(len(published["tracks"]), 2)
        state.ingest([stream_row(0, cou="360")], arrival_time=1)
        following = state.predict(1)
        self.assertEqual(following["audit"]["quarantine_reasons"], {"conflicting_same_time": 1})
        self.assertEqual(following["disappeared"],
                         [dict(source="9001", batch="0", reason="quarantined")])
        state.ingest([stream_row(2)], arrival_time=2)
        self.assertEqual([track["source"] for track in state.predict(2)["tracks"]], ["9002"])
        self.assertEqual(len(published["tracks"]), 2)

    def test_invalid_state_is_quarantined_when_observed(self):
        state = StreamState(stale_after_seconds=5)
        state.ingest([stream_row(0, cou="360"), stream_row(0, batch="1", cou="-1")], arrival_time=0)
        current = state.predict(0)
        self.assertEqual(current["tracks"][0]["course_degrees"], 0)
        self.assertEqual(current["audit"]["quarantine_reasons"], {"missing_course": 1})

    def test_forecast_from_pole_and_across_antimeridian(self):
        state = StreamState(stale_after_seconds=5)
        state.ingest([
            stream_row(0, lat="90", lon="30", cou="0"),
            stream_row(0, batch="1", lat="-90", lon="30", cou="0"),
            stream_row(0, batch="2", lon="179.99999"),
        ], arrival_time=0)
        north, south, crossing = state.predict(1)["tracks"]
        self.assertAlmostEqual(north["latitude"], 89.9999537349)
        self.assertAlmostEqual(north["longitude"], -150)
        self.assertAlmostEqual(south["latitude"], -89.9999537349)
        self.assertAlmostEqual(south["longitude"], 30)
        self.assertAlmostEqual(crossing["longitude"], -179.9999637349)

    def test_clock_errors_reject_whole_batch(self):
        state = StreamState(stale_after_seconds=5)
        with self.assertRaises(ValueError):
            state.ingest([stream_row(0), stream_row(2)], arrival_time=1)
        self.assertEqual(state.predict(0)["audit"]["received_rows"], 0)
        with self.assertRaises(ValueError):
            state.ingest([stream_row(0)], arrival_time=0)
        state.ingest([stream_row(1)], arrival_time=2)
        with self.assertRaises(ValueError):
            state.predict(1)
        self.assertEqual(state.predict(2)["tracks"][0]["arrival_time"], 2)
        with self.assertRaises(ValueError):
            state.predict(2)


def position_row(time, source, batch, lon):
    return dict(time=time, source=source, batch=batch, lat=0, lon=lon,
                vel="unavailable", cou="unavailable")


class StrictReplayTests(unittest.TestCase):
    def test_forecast_uses_only_prefix_and_ignores_speed_and_course_validity(self):
        prefix = [position_row(0, "A", "1", 0.), position_row(2, "A", "1", .0001)]
        modified = [dict(observation, vel=-9, cou="nan") for observation in prefix]
        modified.append(position_row(3, "A", "1", 80.))
        first = _forecasts(prefix)
        second = _forecasts(modified)
        self.assertEqual([next(first) for _ in range(3)], [next(second) for _ in range(3)])

    def test_same_epoch_is_atomic_and_raw_fragment_number_has_no_rank(self):
        original = [position_row(0, "A", "1", 0.), position_row(0, "B", "2", .001),
                    position_row(0, "B", "3", -.001)]
        labels = {("A", "1"): "truth", ("B", "2"): "truth", ("B", "3"): "other"}
        first = evaluate_births(birth_candidates(original), labels)
        changed = [dict(observation, batch="alias-" + observation["batch"])
                   for observation in reversed(original)]
        changed_labels = {(source, "alias-" + batch): identity
                          for (source, batch), identity in labels.items()}
        second = evaluate_births(birth_candidates(changed), changed_labels)
        self.assertEqual(first, second)
        self.assertEqual(first["cross_source", 60, "hold", 250]["nearest_mixed_tie"], 1)

    def test_conflicting_positions_fail_even_if_unused_fields_agree(self):
        with self.assertRaisesRegex(ValueError, "conflicting same-time positions"):
            list(event_batches([position_row(0, "A", "1", 0), position_row(0, "A", "1", .1)]))

    def test_frozen_registration_ignores_the_evaluation_period(self):
        points = {(source, str(i)): (0, lon + shift)
                  for source, shift in (("A", 0), ("B", .02))
                  for i, lon in enumerate((0, .5, 1))}
        prefix = [(time, points) for time in (30, 60, 90)]
        fit = estimate_translation(prefix)
        self.assertEqual(fit["status"], "fitted")
        self.assertAlmostEqual(fit["translation_east_north_m"][0], 2223.8985, places=3)
        self.assertEqual(fit, estimate_translation(
            prefix + [(601, {("C", "0"): (30, 30)})]
        ))
