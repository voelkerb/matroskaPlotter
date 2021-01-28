# !/usr/bin/python
"""Main File to embedd and SRT or ASS subtitle file into an MKV file."""

import os
import sys
from os.path import basename
from mkv import mkv
import argparse
import time


def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputMkv", type=argparse.FileType('r'),
                        help="Path of the input mkv file.")
    parser.add_argument("inputSRT", type=argparse.FileType('r'),
                        help="Path of the output mkv file.")
    parser.add_argument('output', type=str,
                        help="Path and Name of the combined File MKV: e.g. \"~/output.mkv\"")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase output verbosity")
    return parser
    
# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()

    meta = mkv.getMeta(args.inputMkv.name)
    key =  set(["Title", "title", "TITLE", "NAME", "Name", "name"]).intersection(set(meta.keys()))
    if len(key) > 0:
        title = meta[next(iter(key))]
    else:
        title = os.path.basename(args.inputMkv.name).split(".")[0]
    mkv.bakeSubtitles(args.inputMkv.name, args.inputSRT.name, args.output, titles=title)
    print("Bye Bye from " + str(os.path.basename(__file__)))
