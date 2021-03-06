#!/usr/bin/python3

## system imports
import os
import time
import sys
import queue
import threading
import configparser
import fnmatch
## own imports
from mod.handle import sfv, file
from mod import logger

## constants:
__author__ = "ft"
__email__ = "ft2011@gmail.com"
__version__ = "1.0"

baseDir = os.path.dirname(os.path.abspath(__file__))

## config
config = configparser.RawConfigParser()
config.read(os.path.join(baseDir, "config.ini"))

## vars:
now = time.localtime()
fifoPipe = os.path.abspath(config.get("io", "fifoPipe"))
ftpBase = os.path.abspath(config.get("io", "ftpBase"))
logLevel = config.get("log", "level")
log = logger.getLogger(__file__, logLevel)
que = queue.Queue()
running = True


def worker():
    working = True
    while working:
        entry = que.get()
        name, ext = os.path.splitext(entry)

        if ext.lower() == ".sfv":
            sfv(entry)
        elif os.path.isfile(entry):
            file(entry)
        else:
            log.error("something went wrong... (neither sfv nor file?!)")
        que.task_done()


## daemon, wait for new files
def daemon(pipe):
    t = threading.Thread(target=worker)
    t.setDaemon(True)
    try:
        log.debug("starting daemon...")
        t.start()
        while running:
            with open(pipe, "r") as p:
                newFifo = p.readline()
                fifoSplit = newFifo.split("#")

                if len(fifoSplit) != 2:
                    log.debug("not enough parameters, skipping...")
                    continue

                tmp = (ftpBase + fifoSplit[1]).strip()
                path = os.path.normpath(tmp)

                if fifoSplit[0] == "STOR":
                    # STOR /relative/data/path/file.rar
                    log.debug("new file stored: '" + path + "'")
                    que.put(path)

                elif fifoSplit[0] == "SITE SFV":
                    # SITE SFV /relative/data/path
                    log.debug("rechecking: '" + path + "'")

                    for root, dirs, files in os.walk(path):
                        for name in files:
                            if fnmatch.fnmatch(name, "*.sfv"):
                                result = os.path.join(root, name)
                                log.debug("sfv found: '" + result + "'")
                                que.put(result)
                                break


    except:
        log.debug("Unexpected error in daemon loop: " + str(sys.exc_info()[0]))
        raise

## main
def main(argv=None):
    log.debug("starting...")
    daemon(fifoPipe)


if __name__ == '__main__':
    sys.exit(main())