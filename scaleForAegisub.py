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
    systemCall = "ffmpeg -hide_banner -f f32le -ar " + str(args.samplingrate) + " -guess_layout_max 0 -ac "
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
    parser.add_argument('filePaths', type=argparse.FileType('r'), nargs='+',
                        help="Path to the the MKV file")
    parser.add_argument('storePath', type=str,
                        help="Folder where mkv will be stored under same name")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase output verbosity")
    return parser
    
# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()


    channelsToHold = [ int(i) for i in args.channelsToHold.replace(" ", "").split(",") ]
    complexFilter = "pan="
    if len(channelsToHold) == 1: complexFilter += "mono"
    elif len(channelsToHold) == 2: complexFilter += "stereo"
    else: complexFilter += str(len(channelsToHold))
    for targetChannel, channel in enumerate(channelsToHold):
        complexFilter += "|c" + str(targetChannel) + "<c" + str(channel)
    complexFilter += "[result]"

    print(channelsToHold)
    # Catch control+c
    running = True
    # Get external abort
    def aborted(signal, frame):
        global running
        running = False
    signal.signal(signal.SIGINT, aborted)

    for filePath in args.filePaths:
        ffmpegCall = "ffmpeg -hide_banner -i " + str(filePath.name) + " -filter_complex \""
        metadata = ""
        meta = " -metadata:s:a:"
        dataList = mkv.loadAudio(filePath.name)
        maxValues = []
        reformat = False
        for i,data in enumerate(dataList):
            print(data["title"])
            maxValue = 0
            measuresToHold = []
            for channel in channelsToHold:
                try: measuresToHold.append(data["data"].dtype.names[channel])
                except IndexError: continue
                maxValue = max(maxValue, np.max(data["data"][measuresToHold[-1]]))
            scaleFactor = 1.0/maxValue
            maxValues.append(maxValue)
            ffmpegCall += complexFilter + "; [result]volume=" + str(round(scaleFactor,6))
            metadata += meta + str(i) + " title=\"" + str(data["title"]) + "\""
            metadata += meta + str(i) + " CHANNELS=" + str(len(channelsToHold))
            metadata += meta + str(i) + " scalefactor=\"" + str(scaleFactor) + "\""
            metadata += meta + str(i) + " CHANNEL_TAGS=\"" +",".join(measuresToHold) + "\""

        ffmpegCall += "\" -map "
        for i in range(len(dataList)): ffmpegCall += "a:" + str(i)
        ffmpegCall += " -c:a wavpack " + metadata + " -y " + str(os.path.join(args.storePath, os.path.basename(filePath.name)))

        if reformat:
            ffmpegCall = ffmpegCall.replace(filePath.name, str(os.path.join(args.storePath, "temp.mkv")))

        print(ffmpegCall)
        mkv.__call_ffmpeg(ffmpegCall)
        if reformat:
            import subprocess
            subprocess.check_output(['rm', '-rf', str(os.path.join(args.storePath, "temp.mkv"))])

    print("Bye Bye from " + str(os.path.basename(__file__)))
