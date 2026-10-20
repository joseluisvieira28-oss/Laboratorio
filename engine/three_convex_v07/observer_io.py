"""Observer-only durable delivery helpers. No exchange access."""
from contextlib import contextmanager
import os
from pathlib import Path

@contextmanager
def instance_lock(folder):
    """OS releases lock after process death; works on Windows and POSIX."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    f=(folder/'observer.instance.lock').open('a+b')
    try:
        f.seek(0);f.write(b'0');f.flush();f.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:f.close()


def drain(db,table,sent_column,send,now,limit,order):
    # Serialize selection + HTTP + receipt across independent SQLite connections.
    # An HTTP ACK lost before local COMMIT remains ambiguous; no exactly-once claim.
    count=0
    for _ in range(limit):
        try:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute(f'SELECT id,message FROM {table} WHERE {sent_column} IS NULL ORDER BY {order} LIMIT 1').fetchone()
            if row is None:
                db.commit();break
            key,message=row
            if 'CONVEX_' in key:
                try:late=now-int(key.rsplit(':',1)[-1])>180000
                except ValueError:late=False
                if late:message+='\n⚠️ ALERTA ATRASADO — janela de elegibilidade ultrapassada; registo informativo.'
            receipt=send(message)
            receipt=receipt if type(receipt) is int and receipt>0 else None
            db.execute(f'UPDATE {table} SET {sent_column}=?,telegram_message_id=? WHERE id=? AND {sent_column} IS NULL',(now,receipt,key))
            db.commit();count+=1
        except BaseException:
            db.rollback();raise
    return count


def add_receipt_column(db,table):
    if 'telegram_message_id' not in {r[1] for r in db.execute(f'PRAGMA table_info({table})')}:
        db.execute(f'ALTER TABLE {table} ADD COLUMN telegram_message_id INTEGER')
    db.commit()
