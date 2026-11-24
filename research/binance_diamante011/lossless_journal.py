#!/usr/bin/env python3
"""Lossless UTF-8 JSONL original-Journal tee into independent gzip chunks.
NO market transformation, resampling, serialization or changed timestamps.
"""
from __future__ import annotations
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"binance_diamante003"))
from book_core import Journal

CHUNK_MAX_RAW=16_000_000
ARCHIVE_MAX=160_000_000
RAW_MAX=520_000_000
MAX_SEGMENTS=50
FILENAME="lossless_segments_manifest.json"

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

class ByteIdenticalTee:
    """Single original Journal.fp.write() is first mirrored verbatim to raw
    and then gzip, with per-line boundaries and immutable arrival order.
    """
    def __init__(self,original_fp,owner,output,chunk_max=CHUNK_MAX_RAW):
        self.raw=original_fp
        self.owner=owner
        self.out=Path(output)
        self.chunk_max=chunk_max
        self.gz=None
        self.path=None
        self.chunks=[]
        self.raw_sha=hashlib.sha256()
        self.raw_bytes=0
        self.closed=False
        self.chunk_hasher=None
        self.chunk_bytes=0
        self.start_seq=None
        self.last_seq=None
        self.chunk_rows=0

    def _open(self):
        if len(self.chunks)>=MAX_SEGMENTS:
            raise ValueError("SEGMENT_COUNT_CAP")
        seq=len(self.chunks)+1
        self.path=self.out/f"journal-part-{seq:04d}.jsonl.gz"
        self.gz=gzip.GzipFile(filename=str(self.path),mode="wb",
                               compresslevel=6,mtime=0)
        self.start_seq=self.owner.n+1
        self.last_seq=self.owner.n
        self.chunk_rows=0
        self.chunk_bytes=0
        self.chunk_hasher=hashlib.sha256()

    def _finish(self):
        if self.gz is None:return
        self.gz.close()
        compressed=self.path.stat().st_size
        self.chunks.append({
            "file":self.path.name,
            "record_seq_first":self.start_seq,
            "record_seq_last":self.last_seq,
            "records":self.chunk_rows,
            "original_bytes":self.chunk_bytes,
            "original_sha256":self.chunk_hasher.hexdigest(),
            "gzip_bytes":compressed,
            "gzip_sha256":sha_file(self.path)
        })
        self.gz=None

    def write(self,encoded:str):
        if self.closed:raise ValueError("TEE_ALREADY_CLOSED")
        if not isinstance(encoded,str) or not encoded.endswith("\n"):
            raise ValueError("JOURNAL_WRITE_MUST_BE_COMPLETE_UTF8_LINE")
        raw=encoded.encode("utf-8")
        if len(raw)>self.chunk_max:
            raise ValueError("JOURNAL_RECORD_EXCEEDS_SEGMENT_LIMIT")
        if self.raw_bytes+len(raw)>RAW_MAX:
            raise ValueError("ORIGINAL_JOURNAL_HARD_CAP")
        if self.gz is None:self._open()
        if self.chunk_bytes and self.chunk_bytes+len(raw)>self.chunk_max:
            self._finish()
            self._open()
        self.raw.write(encoded)
        self.gz.write(raw)
        self.raw_sha.update(raw)
        self.raw_bytes+=len(raw)
        self.chunk_hasher.update(raw)
        self.chunk_bytes+=len(raw)
        self.chunk_rows+=1
        self.last_seq=self.owner.n+1
        return len(encoded)

    def flush(self):
        if self.closed:return
        self.raw.flush()
        if self.gz is not None:self.gz.flush()

    def close(self):
        if self.closed:return
        self._finish()
        self.raw.flush()
        self.raw.close()
        self.closed=True
        report={
            "study":"BINANCE-DIAMANTE-011",
            "format":"exact original 003 Journal UTF-8 JSONL records, gzip members independent",
            "chunk_uncompressed_max_bytes":self.chunk_max,
            "raw_hard_cap_bytes":RAW_MAX,
            "compressed_total_cap_bytes":ARCHIVE_MAX,
            "raw_utf8_sha256":self.raw_sha.hexdigest(),
            "raw_utf8_bytes":self.raw_bytes,
            "total_chained_records":self.owner.n,
            "journal_last_chain_sha256":self.owner.prev,
            "chunks":self.chunks,
            "chunk_count":len(self.chunks),
            "compressed_total_bytes":sum(x["gzip_bytes"] for x in self.chunks),
            "contains_no_sampled_or_discarded_original_market_frames":True,
            "no_orders":True,"no_real_fills":True
        }
        dest=self.out/FILENAME
        dest.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
        (self.out/(FILENAME+".sha256")).write_text(
            sha_file(dest)+"  "+FILENAME+"\n")

class SegmentedJournal(Journal):
    """Original proven Journal.append/digest executed UNMODIFIED."""
    def __init__(self,path,chunk_max=CHUNK_MAX_RAW):
        super().__init__(path)
        self.fp=ByteIdenticalTee(self.fp,self,Path(path).parent,chunk_max)

def verify_segments(out,remove_raw=False):
    """Compare each uncompressed gzip byte to the original uncompressed JSONL
    while computing all component SHA256s. Streaming O(1MB) memory.
    Returns proof metadata. Raw original deleted only during final package.
    """
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    plain=out/"journal.jsonl"
    indexpath=out/FILENAME
    result={
        "study":"BINANCE-DIAMANTE-011",
        "status":"ARCHIVE_BLOCKED",
        "compression_roundtrip_byte_exact":False,
        "original_uncompressed_file_retained_in_public_artifact":False,
        "no_trades":True
    }
    try:
        idx=json.loads(indexpath.read_text())
        if sha_file(indexpath)!=(out/(FILENAME+".sha256")).read_text().split()[0]:
            raise ValueError("SEGMENT_MANIFEST_SHA_CHANGED")
        if not plain.is_file():raise ValueError("ORIGINAL_EPHEMERAL_JOURNAL_MISSING")
        if not idx["chunks"] or len(idx["chunks"])>MAX_SEGMENTS:
            raise ValueError("NO_SEGMENTS_OR_TOO_MANY")
        if idx["compressed_total_bytes"]>ARCHIVE_MAX:
            raise ValueError("COMPRESSED_ARCHIVE_160MB_CAP")
        if idx["raw_utf8_bytes"]>RAW_MAX:
            raise ValueError("ORIGINAL_JOURNAL_520MB_CAP")
        n=0;raw_size=0;gz_size=0
        digest=hashlib.sha256()
        with plain.open("rb") as origin:
            for part in idx["chunks"]:
                n+=1
                if part["file"]!=f"journal-part-{n:04d}.jsonl.gz":
                    raise ValueError("OUT_OF_ORDER_GZIP_CHUNKS")
                if part["record_seq_first"]!=(1 if n==1 else idx["chunks"][n-2]["record_seq_last"]+1):
                    raise ValueError("GAP_IN_CHUNK_RECORD_SEQUENCE")
                if part["record_seq_last"]-part["record_seq_first"]+1!=part["records"]:
                    raise ValueError("BAD_CHUNK_RECORD_COUNT")
                archived=out/part["file"]
                if not archived.is_file() or archived.stat().st_size!=part["gzip_bytes"]:
                    raise ValueError("MISSING_OR_TRUNCATED_GZIP_MEMBER")
                if sha_file(archived)!=part["gzip_sha256"]:
                    raise ValueError("GZIP_SHA256_MISMATCH")
                gz_size+=part["gzip_bytes"]
                chunk_digest=hashlib.sha256();chunk_size=0
                with gzip.open(archived,"rb") as member:
                    while True:
                        block=member.read(1024*1024)
                        if not block:break
                        expected=origin.read(len(block))
                        if block!=expected:raise ValueError("ORIGINAL_JSONL_BYTE_MISMATCH")
                        digest.update(block)
                        chunk_digest.update(block)
                        chunk_size+=len(block)
                if chunk_size!=part["original_bytes"] or chunk_digest.hexdigest()!=part["original_sha256"]:
                    raise ValueError("CHUNK_RAW_BYTE_SHA256_MISMATCH")
                raw_size+=chunk_size
            if origin.read(1):raise ValueError("ORIGINAL_JSONL_HAS_UNARCHIVED_TRAILING_BYTES")
        if raw_size!=idx["raw_utf8_bytes"] or raw_size!=plain.stat().st_size:
            raise ValueError("ORIGINAL_TOTAL_BYTE_COUNT_MISMATCH")
        if gz_size!=idx["compressed_total_bytes"]:
            raise ValueError("COMPRESSED_TOTAL_BYTE_COUNT_MISMATCH")
        if digest.hexdigest()!=idx["raw_utf8_sha256"]:
            raise ValueError("ORIGINAL_RAW_SHA256_MISMATCH")
        if idx["total_chained_records"]!=idx["chunks"][-1]["record_seq_last"]:
            raise ValueError("ORIGINAL_JOURNAL_SEQUENCE_MISMATCH")
        receipt=out/"source_manifest.json"
        source=json.loads(receipt.read_text()) if receipt.exists() else None
        if source and source.get("journal_file_sha256")!=idx["raw_utf8_sha256"]:
            raise ValueError("SOURCE_004_RAW_SHA256_NOT_EQUAL_LOSSLESS_SOURCE")
        if source and source.get("journal_chain_sha256")!=idx["journal_last_chain_sha256"]:
            raise ValueError("SOURCE_004_JOURNAL_CHAIN_NOT_EQUAL_LOSSLESS_SOURCE")
        result.update({
            "status":"LOSSLESS_SEGMENTED_COMPRESSION_SHA256_PASS",
            "compression_roundtrip_byte_exact":True,
            "raw_uncompressed_sha256":idx["raw_utf8_sha256"],
            "journal_last_chain_sha256":idx["journal_last_chain_sha256"],
            "raw_byte_count":raw_size,
            "compressed_byte_count":gz_size,
            "gzip_chunks":n,
            "records":idx["total_chained_records"],
            "compressed_vs_raw_ratio":round(gz_size/raw_size,6) if raw_size else None,
            "capture_status":source.get("status") if source else "SOURCE_MANIFEST_NOT_FOUND"
        })
    except Exception as exc:
        result.update({"blocker_type":type(exc).__name__,"blocker":str(exc)[:230]})
    finally:
        if remove_raw:
            try:plain.unlink(missing_ok=True)
            except OSError as exc:result["cleanup_error_type"]=type(exc).__name__
        result["original_uncompressed_file_retained_in_public_artifact"]=plain.exists()
        dest=out/("segmented_archive_final_receipt.json" if remove_raw else "segmented_archive_verification.json")
        dest.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        (out/(dest.name+".sha256")).write_text(sha_file(dest)+"  "+dest.name+"\n")
    return result
