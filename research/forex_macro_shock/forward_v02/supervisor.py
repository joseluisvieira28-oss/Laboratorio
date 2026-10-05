"""Portable foreground supervisor. No service installation or event activation."""
import subprocess
import sys
import time
import collector as c


def main():
    failures=0
    try:
        while time.time()+30<c.SETUP_STOP:
            result=subprocess.run([sys.executable,str(c.ROOT/'runtime.py'),'--seconds','3600'],cwd=c.ROOT)
            failures = failures+1 if result.returncode else 0
            if failures>=5:raise RuntimeError('FIVE_RUNTIME_FAILURES: fail closed; inspect logs, no restart loop rescue')
            time.sleep(10)
    except KeyboardInterrupt:
        return


if __name__=='__main__':main()
