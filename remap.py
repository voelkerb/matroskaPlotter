# !/usr/bin/python3
import sys
import os
import time
from mkv import mkv
import argparse
import time
import subprocess
import numpy as np


def constructFFMPEGCall(measures, startTime):
    systemCall = "ffmpeg -hide_banner -i f32le -ar " + str(args.samplingrate) + " -guess_layout_max 0 -ac "
    systemCall += str(len(measures)) + " -i pipe:0 -c:a wavpack "
    meta = " -metadata:s:a:0"
    systemCall += meta + " CHANNELS=" + str(len(measures)) + meta + " CHANNEL_TAGS=\""
    systemCall += ",".join(measures) + "\""
    fileName = ""
    if args.prefix is not "":
        systemCall += meta + " title=" + "\"" + args.prefix + "\""
        fileName += args.prefix + "__"
    fileName += time.strftime("%Y_%m_%d__%H_%M_%S", time.localtime(startTime)) + ".mkv"
    filePath = os.path.join(args.path, fileName)
    systemCall += " -y " + filePath
    return systemCall


def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=argparse.FileType('r'),
                        help="Path to mkv")
    parser.add_argument('output',  type=str,
                        help="Path for storing")
    parser.add_argument('mixing', type=str,
                        help="Channels mixing, e.g. \"0.0.0->0.0.0, 0.0.1->0.0.1, 0.0.2->0.1.1, 0.0.3->0.1.2\" to split \
                        one stream with 4 channels into two streams with 2 channels")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase output verbosity")
    return parser
    
# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()

    mixing = args.mixing.replace(" ", "").split(",")
    mixing = [[mix.split("->")[0], mix.split("->")[1]] for mix in mixing]

    outputChannels = [mix[1].split(".")[1] for mix in mixing]
    numOutChannels = len(set(outputChannels))
    print(numOutChannels)

    mixing = sorted(mixing, key=lambda x: x[0])
    print(mixing)

    systemCall = "ffmpeg -hide_banner -i " + str(args.input.name)

    # We need input this often
    for _ in range(numOutChannels): systemCall += " -map 0"
    for mix in mixing:
        systemCall += " -map_channel " + mix[0] + ":" + mix[1]

    systemCall += " -c:a wavpack -y " + args.output
    # subprocess.
    print(systemCall)
    #eg -i /Users/benny/NILM_Datasets/BuKi/2018_08_28.mkv -map 0 -map_channel 0.0.0:0.0.0 -map_channel 0.0.1:0.0.1 -map 0  -map_channel 0.0.2:0.1.0  -map_channel 0.0.3:0.1.1 -map 0 -map_channel 0.0.4:0.2.0 -map_channel 0.0.5:0.2.1 -c:a wavpack output.mkv



    print("Bye Bye from " + str(os.path.basename(__file__)))
