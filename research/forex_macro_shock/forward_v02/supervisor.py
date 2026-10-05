"""Portable foreground supervisor. No service installation or event activation."""
import subprocess
import sys
import time
from datetime import datetime,timezone,timedelta
import collector as c


def next_window(now):
    # Never start a partial calibration day; decide on UTC clock alone, before
    # observing that day's sources. Warm feeds at 09:58 for the 10:00 UTC grid.
    today=now.replace(hour=9,minute=58,second=0,microsecond=0)
    if now>today:today+=timedelta(days=1)
    while today.weekday()>=5:today+=timedelta(days=1)
    return today,today.replace(hour=16,minute=0)


def main():
    failures=0
    try:
        while time.time()+30<c.SETUP_STOP:
            begin,end=next_window(datetime.now(timezone.utc))
            if begin.timestamp()>=c.SETUP_STOP:break
            print('Next complete burn-in window UTC:',begin.isoformat(),'to',end.isoformat(),flush=True)
            while time.time()<begin.timestamp():time.sleep(min(30,max(0,begin.timestamp()-time.time())))
            duration=max(1,int(end.timestamp()-time.time()))
            result=subprocess.run([sys.executable,str(c.ROOT/'runtime.py'),'--seconds',str(duration)],cwd=c.ROOT)
            failures = failures+1 if result.returncode else 0
            if failures>=5:raise RuntimeError('FIVE_RUNTIME_FAILURES: fail closed; inspect logs, no restart loop rescue')
            if result.returncode:
                print('Interrupted day remains invalid; resume at the next predeclared full window.',flush=True)
    except KeyboardInterrupt:
        return


if __name__=='__main__':main()
