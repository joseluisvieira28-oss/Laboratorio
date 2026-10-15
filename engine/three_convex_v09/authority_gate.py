"""V09 offline-first detached Ed25519 authorization checker.

Public verification is not an order API or proof of a good strategy.
A risk-controller key MUST be generated/held independently of the executor.
Private signing key is NEVER compiled or distributed in this repository.
Nonce is persisted and burned BEFORE broker request; no blind retries.
"""
import base64
from dataclasses import dataclass
from decimal import Decimal,InvalidOperation
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


class AuthorityHalt(ValueError):pass


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()

def sha(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()

def D(s,field):
    try:
        x=Decimal(str(s))
        if not x.is_finite():raise ValueError()
        return x
    except (ValueError,InvalidOperation,TypeError):
        raise AuthorityHalt("INVALID_"+field) from None


def verify_detached_permit(*,public_key_bytes,permit,signature_bytes,
                           proposed_order,now_ms,account_snapshot_hash,
                           ledger_nonce_db):
    """Verify AND consume a scoped permit exactly once; no real mutation.
    
    Not a production-issued trading authority; additional scientific and
    venue gates must independently pass before a caller may even attempt POST.
    """
    if not isinstance(permit,dict) or not isinstance(proposed_order,dict):
        raise AuthorityHalt("MALFORMED_PERMIT_OR_ORDER")
    required={"version","venue","scope","symbol","lane","side",
              "position_mode","margin_mode","leverage","contracts",
              "max_modeled_loss_usdt","signal_close_ms","issued_ms",
              "expires_ms","nonce","account_snapshot_hash","order_sha256"}
    if set(permit)!=required:raise AuthorityHalt("UNEXPECTED_PERMIT_FIELDS")
    if permit["version"]!=1 or permit["venue"]!="MEXC_FUTURES" or permit["scope"]!="ONE_ENTRY":
        raise AuthorityHalt("UNAUTHORIZED_PERMIT_SCOPE")
    if permit["symbol"] not in ("SOL_USDT","BNB_USDT") or permit["side"]!="LONG":
        raise AuthorityHalt("UNAUTHORIZED_VENUE_OR_SIDE")
    if permit["lane"] not in ("SOL_CONVEX_NATIVE_5M","SOL_CONVEX_1H","BNB_CONVEX_4H"):
        raise AuthorityHalt("UNKNOWN_SIGNAL_LANE")
    if (permit["symbol"]=="BNB_USDT")!=(permit["lane"]=="BNB_CONVEX_4H"):
        raise AuthorityHalt("LANE_SYMBOL_MISMATCH")
    if permit["position_mode"]!="HEDGE" or permit["margin_mode"]!="ISOLATED":
        raise AuthorityHalt("MARGIN_MODE_UNVERIFIED")
    if type(permit["leverage"])!=int or permit["leverage"]!=10 or type(permit["contracts"])!=int or permit["contracts"]!=1:
        raise AuthorityHalt("RISK_SCOPE_EXCEEDED")
    if D(permit["max_modeled_loss_usdt"],"CASH_RISK")>Decimal("0.50") or D(permit["max_modeled_loss_usdt"],"CASH_RISK")<=0:
        raise AuthorityHalt("CASH_RISK_TOO_HIGH")
    if type(now_ms)!=int or type(permit["issued_ms"])!=int or type(permit["expires_ms"])!=int or type(permit["signal_close_ms"])!=int:
        raise AuthorityHalt("INVALID_CLOCK")
    if (not permit["issued_ms"]<=now_ms<=permit["expires_ms"] or
        permit["expires_ms"]-permit["issued_ms"]>5000 or
        not 0<=now_ms-permit["signal_close_ms"]<=305000):
        raise AuthorityHalt("PERMIT_STALE_OR_OUTSIDE_V5_ENTRY")
    if (not isinstance(permit["account_snapshot_hash"],str) or
        not re.fullmatch("[0-9a-f]{64}",account_snapshot_hash or "") or
        permit["account_snapshot_hash"]!=account_snapshot_hash):
        raise AuthorityHalt("BROKER_ACCOUNT_RECEIPT_NOT_BOUND")
    if permit["order_sha256"]!=sha(proposed_order):
        raise AuthorityHalt("ORDER_PAYLOAD_TAMPERED")
    if proposed_order!={
        "symbol":permit["symbol"],"price":0,"vol":1,"leverage":10,
        "side":1,"type":5,"openType":1,"positionMode":1,
        "externalOid":proposed_order.get("externalOid")
    } or not re.fullmatch(r"CL8[0-9a-f]{28}",str(proposed_order.get("externalOid",""))):
        raise AuthorityHalt("UNFROZEN_ENTRY_PAYLOAD")
    nonce=permit["nonce"]
    if not isinstance(nonce,str) or not re.fullmatch("[a-f0-9]{32}",nonce):
        raise AuthorityHalt("INVALID_NONCE")
    if not isinstance(signature_bytes,bytes) or not isinstance(public_key_bytes,bytes):
        raise AuthorityHalt("MISSING_DETACHED_SIGNATURE_OR_PUBLIC_KEY")
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature_bytes,canonical(permit))
    except (ValueError,InvalidSignature,TypeError):
        raise AuthorityHalt("SIGNATURE_NOT_VERIFIED") from None
    root=Path(ledger_nonce_db)
    root.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(root,timeout=3,isolation_level=None)
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS consumed(nonce TEXT PRIMARY KEY,issued_ms INTEGER,order_hash TEXT)")
        db.execute("INSERT INTO consumed(nonce,issued_ms,order_hash) VALUES(?,?,?)",
                   (nonce,now_ms,permit["order_sha256"]))
        db.execute("COMMIT")
    except sqlite3.IntegrityError:
        db.execute("ROLLBACK")
        raise AuthorityHalt("ONE_USE_PERMIT_ALREADY_BURNED") from None
    except Exception:
        try:db.execute("ROLLBACK")
        except Exception:pass
        raise
    finally:
        db.close()
    return {"status":"CRYPTOGRAPHIC_PERMIT_VERIFIED_AND_BURNED",
            "nonce_consumed_before_network":True,
            "actual_live_order_authorization":False,
            "requires_separate_full_system_go":True}
