import datetime
import json
import unittest
from source_census import FIRST, CHUNK, POOL, TOPIC, query_payload, parse_bytes

TS=int(datetime.datetime(2025,6,1,tzinfo=datetime.timezone.utc).timestamp())
HASH="0x"+"c"*64
ADDR="0x"+"b"*40
def block(n,with_event=False):
    d={"header":{"number":n,"timestamp":TS}}
    if with_event:
        d["logs"]=[{"address":POOL,"topics":[TOPIC]+["0x"+"0"*64]*3,
            "data":"0x"+f'{10:064x}'+f'{12:064x}'+f'{int(ADDR,16):064x}'+f'{0:064x}',
            "transactionHash":HASH,"logIndex":0}]
    return d
def payload(rows):
    return ("\n".join(json.dumps(x) for x in rows)+"\n").encode()
class SourceTests(unittest.TestCase):
    def test_frozen_query(self):
        p=query_payload(FIRST)
        self.assertEqual(p["toBlock"],FIRST+CHUNK-1)
        self.assertEqual(p["logs"][0]["address"],[POOL])
        self.assertEqual(p["logs"][0]["topic0"],[TOPIC])
    def test_zero_events_has_end_sentinel(self):
        r=parse_bytes(payload([block(FIRST),block(FIRST+CHUNK-1)]),FIRST)
        self.assertEqual(r["event_count"],0)
    def test_one_valid_event_pseudonymous(self):
        r=parse_bytes(payload([block(FIRST,True),block(FIRST+CHUNK-1)]),FIRST)
        self.assertEqual(r["event_count"],1)
        self.assertEqual(len(r["distinct_liquidator_hashes"]),1)
        self.assertNotIn("bbbb",str(r))
    def test_missing_boundary_is_blocked(self):
        with self.assertRaisesRegex(ValueError,"SENTINEL"):parse_bytes(payload([block(FIRST)]),FIRST)
    def test_out_of_range_block(self):
        with self.assertRaisesRegex(ValueError,"OUT_OF_WINDOW"):parse_bytes(payload([block(FIRST+CHUNK)]),FIRST)
    def test_2026_block_forbidden(self):
        x=block(FIRST); x["header"]["timestamp"]=int(datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc).timestamp())
        with self.assertRaisesRegex(ValueError,"PROTECTED_2026"):parse_bytes(payload([x]),FIRST)
    def test_invalid_event_topic(self):
        x=block(FIRST,True);x["logs"][0]["topics"][0]="0x"+"f"*64
        with self.assertRaisesRegex(ValueError,"INVALID_EVENT_TOPICS"):parse_bytes(payload([x]),FIRST)
    def test_bad_abi(self):
        x=block(FIRST,True);x["logs"][0]["data"]="0x123"
        with self.assertRaisesRegex(ValueError,"INVALID_EVENT_ABI"):parse_bytes(payload([x]),FIRST)
    def test_duplicate_block(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_BLOCK"):parse_bytes(payload([block(FIRST),block(FIRST)]),FIRST)
    def test_wrong_contract(self):
        x=block(FIRST,True);x["logs"][0]["address"]="0x"+"a"*40
        with self.assertRaisesRegex(ValueError,"WRONG_CONTRACT"):parse_bytes(payload([x]),FIRST)
if __name__=="__main__":unittest.main()
