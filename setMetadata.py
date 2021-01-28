# !/usr/bin/python

import os
import sys
from os.path import basename
import argparse
from mkv import mkv

def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=argparse.FileType('r'),
                            help="Path to mkv")
    parser.add_argument('output',  type=str,
                            help="Path for storing")
    parser.add_argument('titles', type=str,
                            help="Titles comma separated e.g. Phase_1,Phase_2,Phase_3")
    parser.add_argument('-m', '--measures', type=str,
                            help="Measures for each stream and channel e.g. \"[p_l1,q_lq],[p_l2,q_l2]\" according to valuesAndUnits.py")
    parser.add_argument('-s', '--streams', type=str, default="0",
                            help="Stream(s) to apply it to. e.g. \"0,1,2\"")
    parser.add_argument('-t', '--type',  type=str, default="audio",
                            help="Type of the stream(s) audio / subtitle / video")
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser

# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()

    measures = None
    if args.measures is not None:
        measures = args.measures.replace(" ", "").replace("],[", ";").replace("]", "").replace("[", "").split(";")
        measures = [meas.split(",") for meas in measures]
    streams = args.streams.replace(" ", "").split(",")
    titles = args.titles.replace(" ", "").split(",")
    if len(titles) != len(streams):
        print("Cannot match " + str(len(titles)) + " titles to " + str(len(streams)) + " streams.")
    print(measures)
    metaArgs = ""
    i = 0
    for stream, title in zip(streams, titles):
        streamInt = int(stream)
        meas = None
        if measures is not None and len(measures) > i: meas = measures[i]
        metaArgs += mkv.makeMetaArgs(title, args.type, measures=meas, stream=streamInt)
        i += 1
    mkv.__call_ffmpeg("ffmpeg -hide_banner -i " + str(args.input.name) + " -map 0 -c copy " + metaArgs + " -y " + str(args.output))


    print(("Bye Bye from " + str(os.path.basename(__file__))))
