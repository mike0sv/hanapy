# ruff: noqa: S603
import subprocess
import time


def main():
    while True:
        command = "python client.py {name} {host} mike"

        p1 = subprocess.Popen(command.format(name="bot1", host=1).split())
        time.sleep(2)
        p2 = subprocess.Popen(command.format(name="bot2", host=0).split())

        p1.wait()
        p2.wait()


if __name__ == "__main__":
    main()
