# !/usr/bin/python

import os
import sys
from os.path import basename

from mkv import mkv
import argparse
import time

# _______________Can be called as main__________________
def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('storeFolder', type=str,
                        help="Path where results get stored to.")
    parser.add_argument('dataFolder', type=str,
                        help="Path to the MKV (and srt) file(s)")
    parser.add_argument('--srtFolder', type=str,
                        help="Optional different path to the SRT file(s)")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase output verbosity")
    return parser
    
# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()

    # Files must have same basenames!
    allFiles = []

    for file in os.listdir(args.dataFolder):
        if file.endswith(".mkv") or file.endswith(".srt"):
            allFiles.append(os.path.join(args.dataFolder, file))
    if args.srtFolder is not None:
        for file in os.listdir(args.srtFolder):
            if file.endswith(".srt"):
                allFiles.append(os.path.join(args.srtFolder, file))

    # grouping
    groups = {os.path.basename(file).split(".")[0]:{"mkv": None, "srt": None} for file in allFiles}
    for file in allFiles:
        filo = os.path.basename(file).split(".")
        groups[filo[0]][filo
        [1]] = file

    for name in groups:
        group = groups[name]
        if group["mkv"] is not None and group["srt"] is not None:
            meta = mkv.getMeta(group["mkv"])
            key =  set(["Title", "title", "TITLE", "NAME", "Name", "name"]).intersection(set(meta.keys()))
            if len(key) > 0:
                title = meta[next(iter(key))]
            else:
                title = name
            outPath = os.path.join(args.storeFolder, name + ".mkv")
            mkv.bakeSubtitles(group["mkv"], group["srt"], outPath, titles=title)
    print("Bye Bye from " + str(os.path.basename(__file__)))
