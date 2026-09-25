from __future__ import annotations

from datetime import date, datetime, timezone
import csv
import io
import unittest
import zipfile

from radar import ced1d_render_shadow_collector_v03 as collector
from radar.ced1d_bookdepth_transport_adapter_v05 import (
    CED1DBookDepthTransportError,
    normalize_bookdepth_zip,
)


def make_zip(rows):
    text=io.StringIO(newline="")
    writer=csv.writer(text,lineterminator="\n")
    writer.writerows(rows)
    raw=io.BytesIO()
    with zipfile.ZipFile(raw,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("AVAXUSDT-bookDepth-2026-09-23.csv",text.getvalue().encode())
    return raw.getvalue()


class CED1DBookDepthTransportAdapterTests(unittest.TestCase):
    def test_text_timestamp_is_normalized_to_utc_epoch_ms_then_frozen_parser_runs(self):
        raw=make_zip([
            ["timestamp","percentage","depth","notional"],
            ["2026-09-23 00:00:04","-1.00","176483.00000000","1984280.13200000"],
            ["2026-09-23 00:00:04","1.00","180000.00000000","2000000.00000000"],
        ])
        normalized,event=normalize_bookdepth_zip(raw,date(2026,9,23))
        self.assertEqual(event["timestamp_mode"],"UTC_TEXT_NORMALIZED_TO_EPOCH_MS")
        self.assertEqual(event["text_timestamp_rows_normalized"],2)
        self.assertTrue(event["raw_source_hash_preserved_by_collector"])
        snaps=collector.parse_bookdepth_zip(normalized,date(2026,9,23))
        expected=int(datetime(2026,9,23,0,0,4,tzinfo=timezone.utc).timestamp()*1000)
        self.assertIn(expected,snaps)
        self.assertEqual(snaps[expected][-1.0]["notional"],1984280.132)
        self.assertEqual(snaps[expected][1.0]["notional"],2000000.0)

    def test_numeric_timestamp_is_passthrough(self):
        ts=int(datetime(2026,9,23,0,0,4,tzinfo=timezone.utc).timestamp()*1000)
        raw=make_zip([
            ["timestamp","percentage","depth","notional"],
            [str(ts),"-1.00","10","100"],
        ])
        normalized,event=normalize_bookdepth_zip(raw,date(2026,9,23))
        self.assertEqual(normalized,raw)
        self.assertEqual(event["timestamp_mode"],"NUMERIC_PASSTHROUGH")
        self.assertEqual(event["text_timestamp_rows_normalized"],0)

    def test_text_timestamp_wrong_day_fails_closed(self):
        raw=make_zip([
            ["timestamp","percentage","depth","notional"],
            ["2026-09-24 00:00:04","-1.00","10","100"],
        ])
        with self.assertRaisesRegex(
            CED1DBookDepthTransportError,
            "BOOKDEPTH_TIMESTAMP_DAY_MISMATCH",
        ):
            normalize_bookdepth_zip(raw,date(2026,9,23))

    def test_unknown_timestamp_format_fails_closed(self):
        raw=make_zip([
            ["timestamp","percentage","depth","notional"],
            ["2026/09/23 00:00:04","-1.00","10","100"],
        ])
        with self.assertRaisesRegex(
            CED1DBookDepthTransportError,
            "BOOKDEPTH_TIMESTAMP_FORMAT_UNSUPPORTED",
        ):
            normalize_bookdepth_zip(raw,date(2026,9,23))


if __name__=="__main__":
    unittest.main()
