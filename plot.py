# !/usr/bin/python3


import sys
import os

import numpy as np
import av
from mkv.usefulFunctions import decodeDateString, decodeDateStr
from mkv.millionPointsPlot import MillionPointsPlot, DateAxisItem
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import math
import pysubs2
from mkv import mkv
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as md

import matplotlib
# This is for tex plots according to acm format
matplotlib.rcParams['pdf.fonttype'] = 42
import datetime as datetime
import time
import pytz
import matplotlib.ticker as ticker

# Some predefined colors for specific measures
colors = {}
colors["p"] = (1,0,0)
colors["q"] = (0,0,1)
colors["s"] = (0,1,0)
colors["acc_x"] = (1,0,0)
colors["acc_y"] = (0,0,1)
colors["acc_z"] = (0,1,0)
colors["gyro_x"] = (1,0,0)
colors["gyro_y"] = (0,0,1)
colors["gyro_z"] = (0,1,0)

class PrecisionDateFormatter(ticker.Formatter):
    """
    Extend the `matplotlib.ticker.Formatter` class to allow for millisecond
    precision when formatting a tick (in days since the epoch) with a
    `~datetime.datetime.strftime` format string.

    """

    def __init__(self, fmt, precision=3, tz=None):
        """
        Parameters
        ----------
        fmt : str
            `~datetime.datetime.strftime` format string.
        """
        from matplotlib.dates import num2date
        if tz is None:
            from matplotlib.dates import _get_rc_timezone
            tz = _get_rc_timezone()
        self.num2date = num2date
        self.fmt = fmt
        self.tz = tz
        self.precision = precision

    def __call__(self, x, pos=0):
        if x == 0:
            raise ValueError("DateFormatter found a value of x=0, which is "
                             "an illegal date; this usually occurs because "
                             "you have not informed the axis that it is "
                             "plotting dates, e.g., with ax.xaxis_date()")

        dt = self.num2date(x, self.tz)
        ms = dt.strftime("%f")[:self.precision]

        return dt.strftime(self.fmt).format(ms=ms)

    def set_tzinfo(self, tz):
        self.tz = tz


def format_time(time, time_base):
    if time is None:
        return 'None'
    return '%.3fs (%s or %s/%s)' % (time_base * time, time_base * time, time_base.numerator * time, time_base.denominator)


def initMatplot(subFigs):
    axes = []
    # fig, (axes) = plt.subplots(subFigs, 1, figsize=(10, 3), dpi=200, sharex=True)
    fig, (axes) = plt.subplots(subFigs, 1, figsize=(10, 3), dpi=200, sharex=True, constrained_layout=True)
    fig.subplots_adjust(bottom=0.14, top=0.93, right=0.97, left=0.08, hspace=0.1)
    if subFigs < 2: axes = [axes]
    axes[-1].set_xlabel("Samples")
    # fig.subplots_adjust(bottom=0.11, top=0.98, hspace=0.06)
    return fig, axes


def initPyqtgraph():
    # Make plot white
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')

    pg.setConfigOptions(useOpenGL=True, antialias=True)
    # Make new window
    win = pg.GraphicsWindow(title="Raw Data")
    win.resize(1000,600)
    return win

def getNamesForWhat(what):
    # Try to find a label for the channel
    label = str(what)
    unit = None
    legend = label

    nwhat = what.split("_")[0].upper()
    if nwhat == "P":
        legend = "active power"
    elif nwhat == "Q":
        legend = "reactive power"
    elif nwhat == "S":
        legend = "apparent power"
    if nwhat in ["P","Q","S"]:
        label = "Power"
        unit = "W/var/VA"
    
    if "acc" in what:
        legend = "acceleration " + what
        unit = "g"
        label = "acceleration"
    elif "gyro" in what:
        legend = "rotation rate " + what
        unit = "m/s"
        label = "rotation rate"
    # Construct label and unit
    # NOTE: To be implemented by user
    return legend, label, unit

# Must be called
tnorm = None
def getArbitraryColor(index):
    global tnorm
    cmap = mpl.cm.get_cmap('rainbow')
    return cmap(tnorm(index))

def getColor(index, what):
    try: return colors[what]
    except KeyError: 
        try: return colors[what.split("_")[0]]
        except KeyError:  return getArbitraryColor(index)

def getColorM(index, what):
    return getColor(index, what)

def getColorP(index, what):
    color = getColor(index, what)
    return [int(c*255) for c in color]

def addPyqtgraphCurve(index, plt, data, what, samplingrate, plottime):
    color = getColorP(index, what)
    # Try to find a label for the channel
    legend, label, unit = getNamesForWhat(what)
    # Get known color, else use random one
    if label is not None:
        plt.setLabel('left', label, units=unit)
    # make curve
    curve = MillionPointsPlot(pen=pg.mkPen(color=color, width=3), name=what)
    plt.addItem(curve)

    curve.setMillionData(data, samplingrate, showT=plottime)
    # Set range to full at beginning
    plt.setXRange(0, curve.max)

def plotWithMatplotlib(dataList, measures, verbose=False, show=True, inOneAxis=False, plotType="samples", channelSplitter="_l"):

    # If l1 l2 l3 in data, we need some more figures, calculate how much...
    subFigs = 0
    for dataDict in dataList:
        channels = []
        for c in range(20):
            cha = [ch for ch in dataDict["measures"] if channelSplitter + str(c) in ch]
            if len(cha) > 0: channels.append(cha)
        subFigs += max(len([c for c in channels if len(c) > 0]),1)
    if subFigs == 0: subFigs = 1
    # color normalization
    global tnorm
    tnorm = mpl.colors.Normalize(vmin=0, vmax=len(measures)-1)
    # Init
    if inOneAxis: subFigs = 1

    fig, axes = initMatplot(subFigs)
    for axis in axes:
        axes[0].get_shared_x_axes().join(axes[0], axis)
    # if plottime:
    #     axes[0].set_xlabel("Time in seconds")
    counter = 0
    axisIndex = 0
    tsEnd = 0
    coveredLines = []
    for dataDict in dataList:
        channelTags = dataDict["measures"]
        # Try to sort channels according to L1, L2, L3
        # If e.g. p_l1 and p_l2 are present in this stream they will be plotted in separat plots
        channels = []
        for c in [1,2,3]:
            # Sort after channel here
            cha = [ch for ch in channelTags if channelSplitter + str(c) in ch]
            if len(cha) > 0: channels.append(cha)
        # Else plot everything in one plot
        if len(channels) == 0: channels.append(channelTags)
        for channelArray in channels:
            channelArray.sort(reverse=True)
        if verbose: print("Sorted Channels: " + str(channels))

        # New plot for each channel
        for i, c in enumerate(channels):
            sthin = False
            for what in c:
                # Check if it is a measure to plot
                if what in measures: sthin = True
            # If no channel data here, continue
            if len(c) == 0 or not sthin: continue
            ttitle = dataDict["title"].replace("_"," ")
            # Add L tag if multiple phases were recorded
            if len(channels) > 1: ttitle += " L" + str(i+1)

            if inOneAxis is False: axes[axisIndex].set_title(ttitle, fontdict={'fontsize':9}, pad=2)
            newAxis = True
            lastMeasure = ""
            lines = []
            lastUnit = None
            # Make the lines
            for what in c:
                # Check if it is a measure to plot
                if what not in measures: continue
                data = dataDict["data"][what]
                axis = axes[axisIndex]
                
                legend, label, unit = getNamesForWhat(what)
                # Power can be plotted in same plot
                if unit is not None and lastUnit == unit: 
                    newAxis = True
                else:  
                    if not newAxis:
                        axis = axes[axisIndex].twinx()   
                    newAxis = False  
                lastUnit = unit
                t = None
                lastMeasure = what
                samples = len(data)
                startTs = 0
                convertToDate = False
                if plotType == "date":
                    convertToDate = True
                    startTs = dataDict["timestamp"]
                    duration = samples/dataDict["samplingrate"]
                    timestamps = np.linspace(startTs, startTs + duration, samples)
                    dates = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
                    t = dates
                elif plotType == "seconds":
                    duration = samples/dataDict["samplingrate"]
                    t = np.linspace(0, duration, len(data))
                elif plotType == "samples":
                    t = np.linspace(0, len(data), len(data)+1)
                else:
                    sys.exit("Unsupported plot type" + str(plotType))
                
                t = t[0:len(data)]
                maxPoints = len(t)#1000
                skip = int(len(t)/maxPoints)
                color = getColorM(counter, what)

                # Get known color, else use random one
                if inOneAxis:
                    label = label
                    legend = ttitle
                    color = getArbitraryColor(counter)
                if np.isnan(data).any():
                    if t is not None:
                        line = axis.plot(t[::skip], data[::skip], color=color, label=legend, marker='x')
                    else:
                        line = axis.scatter(np.array(data[0::skip]), color=color, label=legend, marker='x')
                else:
                    if t is not None:
                        line = axis.plot(t[::skip], np.array(data[::skip]), color=color, label=legend)
                    else:
                        line = axis.plot(np.array(data[0::skip]), color=color, label=legend)
                lines.extend(line)

                tsEnd = max(tsEnd, len(dataDict["data"][what])/dataDict["samplingrate"])
                
                show_x = True if axisIndex + 1 == len(axes) else False
                show_y = axisIndex==int(math.ceil(len(axes)/2)-1)
                if not show_x: axes[axisIndex].set_xticklabels([])

                if show_y:
                    txt = "Raw values"
                    if label is not None and unit is not None:
                        txt = str(label) + " in " + str(unit)
                    axis.set_ylabel(txt)
                counter += 1   
                    
            labs = [l.get_label() for l in lines if l.get_label() not in coveredLines]
            coveredLines.extend(labs)
            if len(labs) > 0:
                axis.legend(lines, labs, loc='upper right')

            if plotType == "date":
                #axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S.%f"))
                axis.xaxis.set_major_formatter(PrecisionDateFormatter("%H:%M:%S.{ms}"))

            # rotate and align the tick labels so they look better
            fig.autofmt_xdate(rotation=25, ha='center') 

            #plt.xticks(rotation=45)    
            if "subs" in dataDict:
                for i, sub in enumerate(dataDict["subs"]):
                    if sub.start/1000.0 > tsEnd: break
                    start = sub.start/1000.0 + startTs
                    end = sub.end/1000.0 + startTs
                    middle = start + (end-start)/2
                    if plotType == "date":
                        start = datetime.datetime.fromtimestamp(start)
                        end = datetime.datetime.fromtimestamp(end)
                        middle = datetime.datetime.fromtimestamp(middle)
                    elif plotType == "samples":
                        start = int(start*dataDict["samplingrate"])
                        end = int(end*dataDict["samplingrate"])
                        middle = int(middle*dataDict["samplingrate"])

                    axes[0].axvline(x=start, linewidth=0.1, color=(0,0,0))
                    axes[axisIndex].axvline(x=start, linewidth=0.5, color=(0,0,0))
                    y = axes[axisIndex].get_ylim()[0] + (axes[axisIndex].get_ylim()[1]-axes[axisIndex].get_ylim()[0])/6.5
                    # if i%2 == 0: y += axes[axisIndex].get_ylim()[0] + (axes[axisIndex].get_ylim()[1]-axes[axisIndex].get_ylim()[0])/3
                    text = sub.text.replace("\\N", "\n")
                    text = text.replace(" (", "\n(")
                    axes[axisIndex].text(middle, y, text, rotation=90, fontsize=9, horizontalalignment='center', verticalalignment='bottom')
            if not inOneAxis: 
                axisIndex += 1
                newAxis = True
    if plotType == "date":
        axes[-1].set_xlabel("Time of Day")
    elif plotType == "seconds":
        axes[-1].set_xlabel("Seconds")
    elif plotType == "samples":
        axes[-1].set_xlabel("Samples")
    else:
        axes[-1].set_xlabel(plotType)
    # fig.tight_layout()
    if show:
        plt.show()
    return fig, axes

linkedPlots = []
def updateViews():
    global linkedPlots
    for leftAxisPlot, rightAxisPlot in linkedPlots:
        rightAxisPlot.setGeometry(leftAxisPlot.getViewBox().sceneBoundingRect())
        rightAxisPlot.linkedViewChanged(leftAxisPlot.getViewBox(), rightAxisPlot.XAxis)

def plotWithPyqtgraph(dataList, measures, verbose=False, show=True, plotType="samples"):
    win1 = initPyqtgraph()
    win = pg.GraphicsLayout()    
    win.layout.setSpacing(0.)                                              
    win.setContentsMargins(5., 0., 5., 0.)  
    win1.setCentralItem(win)                                                              
    win1.show()     
    axisIndex = 0
    global tnorm, linkedPlots
    tnorm = mpl.colors.Normalize(vmin=0, vmax=len(measures)-1)
    mainxPlot = None
    plt = None
    tsstart = None
    tsstop = None
    plotNumber = 0
    
    tsEnd = 0
    for dataDict in dataList:
        channelTags = dataDict["measures"]
        # Try to sort channels according to L1, L2, L3
        # If e.g. p_l1 and p_l2 are present in this stream they will be plotted in separat plots
        channels = []
        for c in [1,2,3]:
            # Sort after channel here
            cha = [ch for ch in channelTags if "_l" + str(c) in ch]
            if len(cha) > 0: channels.append(cha)
        # Else plot everything in one plot
        if len(channels) == 0:
            channels.append(channelTags)
            channels[-1].sort(reverse=False)
        for channelArray in channels:
            channelArray.sort()
        if verbose: print("Sorted Channels: " + str(channels))

        # New plot for each channel
        index = 0
        for i, c in enumerate(channels):
            sthin = False
            for what in c:
                # Check if it is a measure to plot
                if what in measures: sthin = True
            # If no channel data here, continue
            if len(c) == 0 or not sthin: continue
            ttitle = dataDict["title"]
            # Add L tag if multiple phases were recorded
            if len(channels) > 1: ttitle += " L" + str(i+1)

            plt = win.addPlot(title=ttitle)
            if plotNumber == 0:
                plt.addLegend()
            plt.enableAutoRange(False, False)

            # Make the lines
            inited = False
            lastUnit = None
            for j, what in enumerate(c):
                index += 1
                myPlt = plt
                # Check if it is a measure to plot
                if what not in measures: continue

                color = getColorP(index, what)
                # Try to find a label for the channel
                legend, label, unit = getNamesForWhat(what)
                # power can be plotted in a single plot
                if inited and unit is not None and unit != lastUnit:
                    myPlt = pg.ViewBox()
                    plt.scene().addItem(myPlt)
                    plt.getAxis('right').linkToView(myPlt)
                    linkedPlots.append((plt, myPlt))
                    if label is not None: plt.setLabel('right', label, units=unit)
                else:
                    if label is not None: myPlt.setLabel('left', label, units=unit)
                lastUnit = unit
                if plotType == "date": 
                    if tsstart is None: tsstart = dataDict["timestamp"]

                # make curve
                # Get known color, else use random one
                curve = MillionPointsPlot(pen=pg.mkPen(color=color, width=3), name=legend)
                myPlt.addItem(curve)

                curve.setMillionData(dataDict["data"][what], dataDict["samplingrate"], startTs=tsstart, showT=plotType=="seconds")
                tsEnd = max(tsEnd, len(dataDict["data"][what])/dataDict["samplingrate"])
                try:
                    ax = myPlt.getAxis('bottom')    #This is the trick  
                    ticks = ax.setStyle(showValues=False)
                except:
                    pass

                inited = True
                if mainxPlot is None: mainxPlot=myPlt
                else: myPlt.setXLink(mainxPlot)

            win.nextRow()
            axisIndex += 1
            # Make label a little smaller
            plt.layout.setRowFixedHeight(0, 0)
            plt.titleLabel.setMaximumHeight(10)
            plt.titleLabel.setMinimumHeight(0)

        plotNumber += 1
        
        ts = 0
        if plotType == "date":
            if tsstart is None and "timestamp" in dataDict: ts = dataDict["timestamp"]
            elif tsstart is not None: ts = float(tsstart)
        if "subs" in dataDict:
            for i, sub in enumerate(dataDict["subs"]):
                if sub.start/1000.0 > tsEnd: break
                start = ts + sub.start/1000.0
                end = ts + sub.end/1000.0
                pos = start + (end-start)/2
                if plotType == "samples":
                    start = int(start*dataDict["samplingrate"])
                    end = int(end*dataDict["samplingrate"])
                    pos = int(pos*dataDict["samplingrate"])
                vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('k', width=1))
                text = pg.TextItem(sub.text, anchor=(0.5,0.5), color=(0, 0, 0, 255))
                # text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">This is the</span><br><span style="color: #FF0; font-size: 16pt;">PEAK</span></div>', anchor=(-0.3,1.3), border='w', fill=(0, 0, 255, 100))
                text.setPos(pos, 10)
                vLine.setPos(start)
                mainxPlot.addItem(text)
                mainxPlot.addItem(vLine)
        
    #  Since all axis are linke, show x axis only on last plot
    # Set range to full at beginning
    if plt is not None:
        if plotType == "date": 
            ts = 0
            if tsstart is None: ts = dataDict["timestamp"]
            if tsstop is None: tsstop = ts + len(dataDict["data"])/dataDict["samplingrate"]
            axis = DateAxisItem(orientation='bottom')
            axis.attachToPlotItem(plt)
        else:
            try:
                ax = plt.getAxis('bottom')    #This is the trick  
                ticks = ax.setStyle(showValues=True)
            except:
                pass

        if plotType == "date":
            plt.setLabel('bottom', "Time of day")
        elif plotType == "seconds":
            plt.setLabel('bottom', "Time (seconds)")
        else:
            plt.setLabel('bottom', "Time", units='samples')
    updateViews()
    for leftAxisPlot, rightAxisPlot in linkedPlots:
        leftAxisPlot.getViewBox().sigResized.connect(updateViews)

    for leftAxisPlot, rightAxisPlot in linkedPlots:
        if leftAxisPlot is not None:
            leftAxisPlot.showAxis('right')
    if tsstart is not None and tsstop is not None:
        plt.setXRange(tsstart, tsstop)
    else:
        plt.setXRange(0, curve.max)

    if show:
        ## Start Qt event loop unless running in interactive mode.
        import sys
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('filePaths', type=argparse.FileType('r'), nargs='+',
                        help="Path to the the MKV file(s)")
    parser.add_argument("-subs", '--subtitlePaths', type=argparse.FileType('r'), nargs='+',
                        help="Path(s) to srt subtitles")
    parser.add_argument("-s", "--streams", type=str, default="-1",
                        help="Select the streams to plot, default=-1 : all streams. e.g. : \"1,2,3\"")
    parser.add_argument("-t", "--title", type=str, 
                        dest='titleList',     # store in 'list'.
                        default=[],
                        action='append',
                        help="Add a title to plot. Use multiple -t to add more titles. e.g -t powermeter01 -t powermeter02")
    parser.add_argument("-m", "--measures", type=str, default="v,i,p,q,s,v_l1,v_l2,v_l3,i_l1,i_l2,i_l3,p_l1,p_l2,p_l3,s_l1,s_l2,s_l3,q_l1,q_l2,q_l3,C0,C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,C11,C12,C13,C14,C15",
                        help="Select the measures to plot. list e.g.: \"v_l1,v_l2,i_l1,i_l2,p_l1,q_l1,C0,C1,C2,C3,C4,C5,C6,C7,C8\"")
    parser.add_argument("-p", "--plot_type", default="samples", choices=["samples", "date", "seconds"],
                        dest='plotType',     # store in 'list'.
                        help="If it should be displayed with datetime on axis, seconds or samples")
    parser.add_argument("--matplotlib", action="store_true",
                        help="If it should be displayed using matplotlib")
    parser.add_argument("--smoothing", type=int, default=None,
                        help="Smoothness parameter, default=No smooting applied")
    parser.add_argument("-a", "--aggregated", type=int,
                        help="Select aggregated stream. This stream will be plotted on top. Default, stream 0 is used.")
    parser.add_argument("--fromSample", type=str, default=None,
                        help="Sample number to start from")
    parser.add_argument("--toSample", type=str, default=None,
                        help="Sample number up to")
    parser.add_argument("--fromTime", type=str, default=None,
                        help="Time to start from format <year>.<month>.<day>_<hour>:<min>:<sec>.<ms>")
    parser.add_argument("--toTime", type=str, default=None,
                        help="Time to plot up to, format <year>.<month>.<day>_<hour>:<min>:<sec>.<ms>")
    parser.add_argument("--noSubs", action="store_true",
                        help="If subs should be plotted")
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Increase output verbosity")
    return parser

# _______________Can be called as main__________________
if __name__ == '__main__':
    import argparse
    parser = initParser()
    args = parser.parse_args()

    # The measures to plot
    # Convert from ',' separated string to a python list here
    measures = args.measures.split(',')
    measures = [measure.lstrip(" ") for measure in measures]


    streamsToLoad = None
    if args.streams != "-1":
        streamsToLoad = args.streams.split(",")
        streamsToLoad = [int(stream) for stream in streamsToLoad]
    if len(args.titleList) > 0:
        myInfo = mkv.info(args.filePath.name)
        titles = [stream["title"] for stream in myInfo["streams"]]
        if streamsToLoad is None: streamsToLoad = []
        streamsToLoad.extend([titles.index(title) for title in args.titleList if title in titles])
        for title in args.titleList:
            if title not in titles:
                printError("Stream with title \"{}\" not found".format(title))

        print(args.titleList)

    audio = []
    remainingSubs = []
    for filePath in args.filePaths:
        if args.verbose:
            print(mkv.info(filePath.name))
            print("Loading mkv.. ", end="", flush=True)
        # Load auido and subs separat, this is way faster
        # dataList = mkv.load(args.filePath.name, streamsToLoad=streamsToLoad, verbose=args.verbose >= 2)
        dataList = mkv.loadAudio(filePath.name, streamsToLoad=streamsToLoad, verbose=args.verbose >= 2)
        if not args.noSubs:
            dataList.extend(mkv.load(filePath.name, streamsToLoad=streamsToLoad, subs=True, audio=False, video=False, verbose=args.verbose >= 2))
        if args.verbose and len(dataList) > 0:
            print(dataList[0]["data"].dtype.names)
            print("Finished")

        if args.verbose > 3:
            print(dataList)
        # Sort subtitles and audio s.t. audio starts with all streams without subtitles
        # Subtitle array will be of same length as audio array with nones for audio streams without subtitles
        dataAudio, dataSub = mkv.mapSubsToAudio(dataList, fallBackMapping=True)
        for a in dataAudio: a["filename"] = filePath
        audio.extend(dataAudio)
        remainingSubs.extend(dataSub)


    if len(remainingSubs) > 0: printBlue("Used fallback mapping: Subtitle mapping might not be correct!")
    subFigs = len(audio)

    # Resorting
    if args.aggregated is not None:
        audio = [a for a in audio if a["streamIndex"] == args.aggregated] + [a for a in audio if a["streamIndex"] != args.aggregated]

    
    if args.toTime is not None:
        timestop = decodeDateStr(args.toTime, "%Y.%m.%d_%H:%M:%S.%f").timestamp()
        for audio_ in audio:
            if "timestamp" not in audio_:
                audio_["timestamp"] = datetime.datetime.timestamp(date) # +2*60*60
            samplestop = int((timestop - audio_["timestamp"])*audio_["samplingrate"])
            audio_["data"] = audio_["data"][:samplestop]

    def timestampFromFileName(fn):
        date = None
        dateStr = "__".join(os.path.basename(fn.rstrip(".mkv")).split("__")[-2:])
        date = decodeDateString(dateStr)
        if date is None:
            date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)#.astimezone(pytz.utc)
        return date.timestamp()

    if args.fromTime is not None:
        timestart = decodeDateStr(args.fromTime, "%Y.%m.%d_%H:%M:%S.%f").timestamp()
        for a in audio:
            if "timestamp" not in a: a["timestamp"] = timestampFromFileName(a["filename"])
            samplestart = int((timestart - a["timestamp"])*a["samplingrate"])
            a["timestamp"] = timestart
            a["data"] = a["data"][samplestart:]
        
    

    if args.toSample is not None:
        # toSample = int(numexpr.evaluate(args.toSample))
        toSample = int(args.toSample)
        if toSample is not None:
            for a in audio:
                a["data"] = a["data"][:toSample]
    if args.fromSample is not None:
        # fromSample = int(numexpr.evaluate(args.fromSample))
        fromSample = int(args.fromSample)
        if fromSample is not None:
            for a in audio:
                a["data"] = a["data"][fromSample:]


    for a in audio:
        a["measures"] = list(set(a["measures"]).intersection(measures))
        a["data"] = a["data"][a["measures"]]

    allMeasures = measures
    
    if args.smoothing is not None:
        for a in audio:
            rawData = a["data"]
            # Uncomment if you want to have integer samplingrate
            # smoothingapplied = int(data["samplingrate"]/args.smoothing)*data["samplingrate"]
            # if args.smoothing != smoothingapplied:
            #     if args.verbose:
            #         print("Smoothing has been set to {} to maintain integer samplingrate".format(smoothingapplied))
            
            smoothingapplied = args.smoothing
            smooth_data = [rawData[d] for d in rawData.dtype.names]
            smooth_data = [np.median(d[0:int(len(d)/smoothingapplied)*smoothingapplied].reshape(-1, smoothingapplied), axis=1) for d in smooth_data]
            dt = [(d, 'f4') for d in rawData.dtype.names]
            # NOTE: Using Recarray is a little bit slower, uncomment if you need it though
            # newData = np.core.records.fromarrays(np.asarray(smooth_powers, dtype='float32'), dtype=dt)
            a["data"] = np.column_stack(smooth_data)
            a["data"].dtype = dt
            # Uncomment if you want to have integer samplingrate
            # data["samplingrate"] = int(data["samplingrate"]/smoothingapplied)
            a["samplingrate"] = a["samplingrate"]/smoothingapplied
            if (a["samplingrate"] == 0) :
                print("samplingrates < 1 are not supported, maybe smoothing problem...")
    measures = list(set(allMeasures))

    if args.plotType == "date":
        # date = datetime.datetime.strptime("/".join(os.path.basename(args.filePath.name).split("_")[0:-1]), '%Y/%m/%d')
        for a in audio:
            if "timestamp" not in a:
                a["timestamp"] = timestampFromFileName(a["filename"]) # +2*60*60

    if args.matplotlib:
        plotWithMatplotlib(audio, measures, verbose=args.verbose>1, show=True, plotType=args.plotType)
    else:
        win = plotWithPyqtgraph(audio, measures, verbose=args.verbose>1, show=True, plotType=args.plotType)



    print("Bye Bye from " + str(os.path.basename(__file__)))
