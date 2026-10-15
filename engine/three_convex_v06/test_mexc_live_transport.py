"""Synthetic transport fixtures. No authenticated requests, real orders, or secrets."""
import json
import re
import unittest
from dataclasses import replace
from urllib.parse import urlparse

from engine.three_convex_v06.mexc_futures_live_transport import (
    PrivateKey, FuturesV06Transport, OneUseMutationTicket,
    MEXCTransportHalt, signature,
)


class MockReply:
    status=200
    def __init__(self,payload=None):
        self.payload=payload or {"success":True,"data":{"orderId":"MOCK-123"}}
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def read(self,limit=None):return json.dumps(self.payload).encode("utf8")


class FakeHTTP:
    def __init__(self,raises=False):
        self.requests=[]
        self.raises=raises
    def __call__(self,request,timeout):
        self.requests.append((request,timeout))
        if self.raises:raise TimeoutError("mock timeout")
        return MockReply()


def fixture():
    f=FakeHTTP()
    c=FuturesV06Transport(PrivateKey("FAKE_PUBLIC_KEY","FAKE_PRIVATE_SECRET"),
                           opener=f,clock_ms=lambda:10000)
    return c,f


def ticket(endpoint="/api/v1/private/order/create",symbol="SOL_USDT",
           issued=9999):
    return OneUseMutationTicket(endpoint,symbol,issued,"f"*64)


class TransportTests(unittest.TestCase):
    def test_get_signed_only_allowlist(self):
        c,f=fixture()
        c.account_assets()
        req,timeout=f.requests[0]
        self.assertEqual(req.get_method(),"GET")
        self.assertEqual(urlparse(req.full_url).netloc,"api.mexc.com")
        self.assertEqual(req.get_header("Signature"),
            signature("FAKE_PUBLIC_KEY","FAKE_PRIVATE_SECRET",10000,""))
        self.assertEqual(timeout,9)

    def test_post_real_endpoint_with_explicit_one_use_ticket(self):
        c,f=fixture()
        auth=ticket()
        c.submit_long("SOL_USDT",1,"SOL.123",ticket=auth)
        req,_=f.requests[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertTrue(auth.consumed)
        self.assertEqual(urlparse(req.full_url).path,
                         "/api/v1/private/order/create")
        d=json.loads(req.data)
        self.assertEqual(d["openType"],1)
        self.assertEqual(d["leverage"],10)
        self.assertEqual(d["positionMode"],1)
        self.assertEqual(d["vol"],1)
        self.assertEqual(d["side"],1)
        self.assertEqual(d["type"],5)
        self.assertEqual(req.get_header("Signature"),
            signature("FAKE_PUBLIC_KEY","FAKE_PRIVATE_SECRET",10000,
                      req.data.decode("utf8")))

    def test_without_ticket_real_post_blocked(self):
        c,f=fixture()
        with self.assertRaisesRegex(MEXCTransportHalt,"INDEPENDENT_AUTHORITY"):
            c.submit_long("SOL_USDT",1,"SOL.123",ticket=None)
        self.assertEqual(f.requests,[])

    def test_double_send_blocked(self):
        c,f=fixture()
        t=ticket()
        c.submit_long("SOL_USDT",1,"SOL.123",ticket=t)
        with self.assertRaisesRegex(MEXCTransportHalt,"STALE_OR_INVALID"):
            c.submit_long("SOL_USDT",1,"SOL.123",ticket=t)
        self.assertEqual(len(f.requests),1)

    def test_stale_ticket_rejected(self):
        c,f=fixture()
        with self.assertRaisesRegex(MEXCTransportHalt,"STALE_OR_INVALID"):
            c.submit_long("SOL_USDT",1,"SOL.123",ticket=ticket(issued=10))
        self.assertEqual(len(f.requests),0)

    def test_ticket_symbol_mismatch(self):
        c,f=fixture()
        with self.assertRaisesRegex(MEXCTransportHalt,"SYMBOL_TICKET_MISMATCH"):
            c.submit_long("SOL_USDT",1,"SOL.123",ticket=ticket(symbol="BNB_USDT"))
        self.assertEqual(len(f.requests),0)

    def test_nonapproved_symbol_rejected(self):
        c,f=fixture()
        with self.assertRaisesRegex(MEXCTransportHalt,"ONE_CONTRACT_LONG_ONLY"):
            c.submit_long("BTC_USDT",1,"BTC.123",ticket=ticket())

    def test_size_gt_one_blocked(self):
        c,f=fixture()
        with self.assertRaisesRegex(MEXCTransportHalt,"ONE_CONTRACT_LONG_ONLY"):
            c.submit_long("SOL_USDT",2,"SOL.123",ticket=ticket())

    def test_stop_by_position_real_post(self):
        c,f=fixture()
        t=ticket("/api/v1/private/stoporder/place")
        c.place_full_long_position_stop(12345,1,"96.00",ticket=t)
        req,_=f.requests[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(urlparse(req.full_url).path,
                         "/api/v1/private/stoporder/place")
        data=json.loads(req.data)
        self.assertEqual(data["positionId"],12345)
        self.assertEqual(data["vol"],1)
        self.assertEqual(data["lossTrend"],2)
        self.assertEqual(data["stopLossType"],0)

    def test_stop_without_real_position_id(self):
        c,f=fixture()
        with self.assertRaisesRegex(MEXCTransportHalt,"INVALID_PROTECTION"):
            c.place_full_long_position_stop(0,1,96,ticket=ticket(
                "/api/v1/private/stoporder/place"))
        self.assertEqual(len(f.requests),0)

    def test_unknown_network_outcome_consumes_ticket(self):
        fake=FakeHTTP(raises=True)
        c=FuturesV06Transport(PrivateKey("K","S"),opener=fake,
                             clock_ms=lambda:10000)
        t=ticket()
        with self.assertRaisesRegex(MEXCTransportHalt,"OUTCOME_UNVERIFIED"):
            c.submit_long("SOL_USDT",1,"SOL.123",ticket=t)
        self.assertTrue(t.consumed)
        with self.assertRaisesRegex(MEXCTransportHalt,"STALE_OR_INVALID"):
            c.submit_long("SOL_USDT",1,"SOL.123",ticket=t)
        self.assertEqual(len(fake.requests),1)

    def test_non200_fails_closed(self):
        class ErrorReply(MockReply):
            status=503
        class Server:
            def __call__(self,*a,**k):return ErrorReply()
        c=FuturesV06Transport(PrivateKey("K","S"),opener=Server(),
                             clock_ms=lambda:10000)
        with self.assertRaisesRegex(MEXCTransportHalt,"OUTCOME_UNVERIFIED"):
            c.account_assets()

    def test_failed_broker_response(self):
        class Server:
            def __call__(self,*a,**k):
                return MockReply({"success":False,"message":"MOCKFAIL"})
        c=FuturesV06Transport(PrivateKey("K","S"),opener=Server(),
                             clock_ms=lambda:10000)
        with self.assertRaisesRegex(MEXCTransportHalt,"BROKER_REJECTED"):
            c.account_assets()

    def test_private_key_not_represented_in_transport_exceptions(self):
        c,f=fixture()
        try:
            c._exchange("POST","/api/v1/private/unlisted",{},ticket=ticket())
        except Exception as exc:
            self.assertNotIn("FAKE_PRIVATE_SECRET",str(exc))
        else:
            self.fail("did not fail")


if __name__=="__main__":
    unittest.main()
