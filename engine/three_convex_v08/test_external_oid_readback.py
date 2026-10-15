import json
import unittest
from engine.three_convex_v06.mexc_futures_live_transport import FuturesV06Transport,PrivateKey,MEXCTransportHalt
OID="CL8"+"a"*28

class Reply:
    status=200
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return json.dumps({"success":True,"data":self.data}).encode()

class HTTP:
    def __init__(self,data):self.data=data;self.requests=[]
    def __call__(self,req,timeout):
        self.requests.append(req)
        return Reply(self.data)

class ExternalRecoveryTests(unittest.TestCase):
    def client(self,data):
        network=HTTP(data)
        c=FuturesV06Transport(PrivateKey("KEY","SECRET"),opener=network,clock_ms=lambda:10000)
        return c,network

    def test_authenticated_oid_lookup(self):
        obj={"orderId":"12345","externalOid":OID,"symbol":"SOL_USDT","state":3,"dealVol":1}
        c,net=self.client(obj)
        self.assertEqual(c.get_order_by_external_oid("SOL_USDT",OID)["orderId"],"12345")
        self.assertEqual(net.requests[0].get_method(),"GET")

    def test_path_injection_blocked(self):
        c,net=self.client({})
        with self.assertRaisesRegex(MEXCTransportHalt,"LOOKUP_INPUT_INVALID"):
            c.get_order_by_external_oid("SOL_USDT",OID+"/../../order/create")
        self.assertEqual(len(net.requests),0)

    def test_null_order_not_confused_with_safe_resend(self):
        c,net=self.client(None)
        with self.assertRaisesRegex(MEXCTransportHalt,"MISSING_OR_UNKNOWN"):
            c.get_order_by_external_oid("SOL_USDT",OID)
        self.assertEqual(len(net.requests),1)

    def test_wrong_symbol_refused(self):
        c,net=self.client({"orderId":"10","externalOid":OID,"symbol":"BNB_USDT"})
        with self.assertRaisesRegex(MEXCTransportHalt,"IDENTITY_MISMATCH"):
            c.get_order_by_external_oid("SOL_USDT",OID)

    def test_missing_order_id_refused(self):
        c,net=self.client({"externalOid":OID,"symbol":"SOL_USDT"})
        with self.assertRaisesRegex(MEXCTransportHalt,"ID_ABSENT"):
            c.get_order_by_external_oid("SOL_USDT",OID)
