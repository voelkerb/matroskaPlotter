"""Display million points without showing all (still in memory)."""
# !/usr/bin/python

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time




class Data():

    def __init__(self, data=None, dataGetter=None):
        self.data = data
        self.dataGetter = None

    def __getitem__(self, index):
        if self.data is not None: return self.data[index]

        if self.dataGetter is None: return None

        if isinstance(index, slice):
            # do your handling for a slice object:
            self.dataGetter(index.start, index.stop, index.step)
        elif isinstance(index, int):
            self.dataGetter(index.start, index.start+1, 1)
        else:
            raise TypeError("Invalid argument type.")

    def __len__(self):
        """Make this class compilaant with len() call."""
        if self.data is not None: return len(self.data)
        else: return len(self.dataGetter(0,-1,1))

class MillionPointsPlot(pg.PlotCurveItem):
    def __init__(self, *args, **kwds):
        self.data = Data()
        self.samplingRate = 1
        self.max = 0
        self.min = 0
        self.showT = False
        self.limit = 10000  # maximum number of samples to be plotted
        self.updateFunc = None
        pg.PlotCurveItem.__init__(self, *args, **kwds)

    def setMillionData(self, data=None, samplingRate=None, startTs=None, showT=False, dataGetter=None):
        self.startTs = None
        if startTs is not None: self.startTs = float(startTs)
        self.data.dataGetter = dataGetter
        self.data.data = data
        self.samplingRate = samplingRate
        self.showT = showT
        self.updateFunc = self.updateMillionPointsPlot
        self.max = len(self.data)
        self.min = 0
        if self.showT:
            self.updateFunc = self.updateMillionPointsWithTPlot
            self.max = len(self.data)/(self.samplingRate)
        if self.startTs is not None:
            self.updateFunc = self.updateMillionPointsWithDate
            self.max = len(self.data)/(self.samplingRate)+self.startTs
            self.min = self.startTs

    def viewRangeChanged(self):
        if self.updateFunc: self.updateFunc()

    def updateMillionPointsPlot(self):
        if self.data is None or self.data[:] is None:
            self.setData([])
            return
        vb = self.getViewBox()
        # help(self.parentItem())
        if vb is None:
            return  # no ViewBox yet
        # Determine what data range must be read from HDF5
        xrange = vb.viewRange()[0]
        start = max(0,int(xrange[0])-1)
        stop = min(len(self.data), int(xrange[1]+2))

        # Decide by how much we should downsample
        ds = int((stop-start) / self.limit) + 1

        if ds == 1:
            # Small enough to display with no intervention.
            visible = self.data[start:stop]
            scale = 1
        else:
            # Here convert data into a down-sampled array suitable for visualizing.
            # Must do this piecewise to limit memory usage.
            samples = 1 + ((stop-start) // ds)
            visible = None

            sourcePtr = start
            targetPtr = 0

            # read data in chunks of ~1M samples
            chunkSize = (1000000//ds) * ds
            while sourcePtr < stop-1:
                chunk = self.data[sourcePtr:min(stop,sourcePtr+chunkSize)]
                if visible is None: visible = np.zeros(samples*2, dtype=chunk.dtype)
                sourcePtr += len(chunk)
                # reshape chunk to be integral multiple of ds
                chunk = chunk[:(len(chunk)//ds) * ds].reshape(len(chunk)//ds, ds)

                # compute max and min
                chunkMax = chunk.max(axis=1)
                chunkMin = chunk.min(axis=1)

                # interleave min and max into plot data to preserve envelope shape
                visible[targetPtr:targetPtr+chunk.shape[0]*2:2] = chunkMin
                visible[1+targetPtr:1+targetPtr+chunk.shape[0]*2:2] = chunkMax
                targetPtr += chunk.shape[0]*2

            visible = visible[:targetPtr]
            scale = ds * 0.5
        self.setData(visible.reshape(len(visible),)) # update the plot
        self.setPos(start, 0) # shift to match starting index
        self.resetTransform()
        self.scale(scale, 1)  # scale to match downsampling


    def updateMillionPointsWithTPlot(self):
        if self.data is None or self.data[:] is None:
            self.setData([])
            return

        vb = self.getViewBox()
        if vb is None:
            return  # no ViewBox yet
        timeFactor = self.samplingRate
        xrange = vb.viewRange()[0]
        start = max(0,(int(xrange[0])-1)*timeFactor)
        stop = min(len(self.data[:]), int(xrange[1]*timeFactor))

        # Decide by how much we should downsample
        ds = int((stop-start) / self.limit) + 1

        if ds == 1:
            # Small enough to display with no intervention.
            visible = self.data[start:stop]
            scale = 1
        else:
            # Here convert data into a down-sampled array suitable for visualizing.
            # Must do this piecewise to limit memory usage.
            samples = 1 + ((stop-start) // ds)
            visible = None
            sourcePtr = start
            targetPtr = 0

            # read data in chunks of ~1M samples
            chunkSize = (1000000//ds) * ds
            while sourcePtr < stop-1:
                chunk = self.data[sourcePtr:min(stop,sourcePtr+chunkSize)]
                if visible is None: visible = np.zeros(samples*2, dtype=chunk.dtype)
                sourcePtr += len(chunk)

                # reshape chunk to be integral multiple of ds
                chunk = chunk[:(len(chunk)//ds) * ds].reshape(len(chunk)//ds, ds)

                # compute max and min
                chunkMax = chunk.max(axis=1)
                chunkMin = chunk.min(axis=1)

                # interleave min and max into plot data to preserve envelope shape
                visible[targetPtr:targetPtr+chunk.shape[0]*2:2] = chunkMin
                visible[1+targetPtr:1+targetPtr+chunk.shape[0]*2:2] = chunkMax
                targetPtr += chunk.shape[0]*2
            if visible is None: return
            visible = visible[:targetPtr]
            scale = ds * 0.5

        startT = start/(timeFactor)
        stopT = stop/(timeFactor)
        t = np.linspace(startT, stopT, len(visible))
        self.setData(t, visible.reshape(len(visible),)) # update the plot
        # self.setPos(start, 0) # shift to match starting index
        # self.resetTransform()
        #self.scale(scale, 1)  # scale to match downsampling

    def updateMillionPointsWithDate(self):
        if self.data is None or self.data[:] is None:
            self.setData([])
            return

        vb = self.getViewBox()
        if vb is None:
            return  # no ViewBox yet
        timeFactor = self.samplingRate
        xrange = vb.viewRange()[0]
        startTime = xrange[0]
        stopTime = xrange[1]
        start = max(0, int((startTime-self.startTs)*timeFactor))
        stop = min(len(self.data), int((stopTime-self.startTs)*timeFactor))

        # Decide by how much we should downsample
        ds = int((stop-start) / self.limit) + 1

        if ds == 1:
            # Small enough to display with no intervention.
            visible = self.data[start:stop]
            scale = 1
        else:
            # Here convert data into a down-sampled array suitable for visualizing.
            # Must do this piecewise to limit memory usage.
            samples = 1 + ((stop-start) // ds)
            visible = None
            sourcePtr = start
            targetPtr = 0

            # read data in chunks of ~1M samples
            chunkSize = (1000000//ds) * ds
            while sourcePtr < stop-1:
                chunk = self.data[sourcePtr:min(stop,sourcePtr+chunkSize)]
                if visible is None: visible = np.zeros(samples*2, dtype=chunk.dtype)
                sourcePtr += len(chunk)

                # reshape chunk to be integral multiple of ds
                chunk = chunk[:(len(chunk)//ds) * ds].reshape(len(chunk)//ds, ds)

                # compute max and min
                chunkMax = chunk.max(axis=1)
                chunkMin = chunk.min(axis=1)

                # interleave min and max into plot data to preserve envelope shape
                visible[targetPtr:targetPtr+chunk.shape[0]*2:2] = chunkMin
                visible[1+targetPtr:1+targetPtr+chunk.shape[0]*2:2] = chunkMax
                targetPtr += chunk.shape[0]*2
            if visible is None: return
            visible = visible[:targetPtr]
            scale = ds * 0.5

        startT = start/(timeFactor)
        stopT = stop/(timeFactor)
        # t = np.linspace(startT, stopT, len(visible))
        t = np.linspace(self.startTs + startT, self.startTs + stopT, len(visible))
        self.setData(t, visible.reshape(len(visible),)) # update the plot
        # self.setData(t, numpy.random.rand(len(t))) # update the plot
        
        # self.setPos(start, 0) # shift to match starting index
        # self.resetTransform()
        #self.scale(scale, 1)  # scale to match downsampling



"""
This module provides date-time aware axis
"""

__all__ = ["DateAxisItem"]

import numpy
from pyqtgraph import AxisItem
from datetime import datetime, timedelta
from time import mktime


class DateAxisItem(AxisItem):
    """
    A tool that provides a date-time aware axis. It is implemented as an
    AxisItem that interpretes positions as unix timestamps (i.e. seconds
    since 1970).
    The labels and the tick positions are dynamically adjusted depending
    on the range.
    It provides a  :meth:`attachToPlotItem` method to add it to a given
    PlotItem
    """
    
    # Max width in pixels reserved for each label in axis
    _pxLabelWidth = 80

    def __init__(self, *args, **kwargs):
        AxisItem.__init__(self, *args, **kwargs)
        self._oldAxis = None

    def tickValues(self, minVal, maxVal, size):
        """
        Reimplemented from PlotItem to adjust to the range and to force
        the ticks at "round" positions in the context of time units instead of
        rounding in a decimal base
        """

        maxMajSteps = int(size/self._pxLabelWidth)

        dt1 = datetime.fromtimestamp(minVal)
        dt2 = datetime.fromtimestamp(maxVal)

        dx = maxVal - minVal
        majticks = []

        if dx > 63072001:  # 3600s*24*(365+366) = 2 years (count leap year)
            d = timedelta(days=366)
            for y in range(dt1.year + 1, dt2.year):
                dt = datetime(year=y, month=1, day=1)
                majticks.append(mktime(dt.timetuple()))

        elif dx > 5270400:  # 3600s*24*61 = 61 days
            d = timedelta(days=31)
            dt = dt1.replace(day=1, hour=0, minute=0,
                             second=0, microsecond=0) + d
            while dt < dt2:
                # make sure that we are on day 1 (even if always sum 31 days)
                dt = dt.replace(day=1)
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 172800:  # 3600s24*2 = 2 days
            d = timedelta(days=1)
            dt = dt1.replace(hour=0, minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 7200:  # 3600s*2 = 2hours
            d = timedelta(hours=1)
            dt = dt1.replace(minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 1200:  # 60s*20 = 20 minutes
            d = timedelta(minutes=10)
            dt = dt1.replace(minute=(dt1.minute // 10) * 10,
                             second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 120:  # 60s*2 = 2 minutes
            d = timedelta(minutes=1)
            dt = dt1.replace(second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 20:  # 20s
            d = timedelta(seconds=10)
            dt = dt1.replace(second=(dt1.second // 10) * 10, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 2:  # 2s
            d = timedelta(seconds=1)
            majticks = range(int(minVal), int(maxVal))

        else:  # <2s , use standard implementation from parent
            return AxisItem.tickValues(self, minVal, maxVal, size)

        L = len(majticks)
        if L > maxMajSteps and maxMajSteps != 0:
            majticks = majticks[::int(numpy.ceil(float(L) / maxMajSteps))]

        return [(d.total_seconds(), majticks)]

    def tickStrings(self, values, scale, spacing):
        """Reimplemented from PlotItem to adjust to the range"""
        ret = []
        if not values:
            return []

        if spacing >= 31622400:  # 366 days
            fmt = "%Y"

        elif spacing >= 2678400:  # 31 days
            fmt = "%Y %b"

        elif spacing >= 86400:  # = 1 day
            fmt = "%b/%d"

        elif spacing >= 3600:  # 1 h
            fmt = "%b/%d-%Hh"

        elif spacing >= 60:  # 1 m
            fmt = "%H:%M"

        elif spacing >= 1:  # 1s
            fmt = "%H:%M:%S"

        else:
            # less than 2s (show microseconds)
            # fmt = '%S.%f"'
            fmt = '[+%fms]'  # explicitly relative to last second

        for x in values:
            try:
                t = datetime.fromtimestamp(x)
                ret.append(t.strftime(fmt))
            except ValueError:  # Windows can't handle dates before 1970
                ret.append('')

        return ret

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

    def detachFromPlotItem(self):
        """Remove this axis from its attached PlotItem
        (not yet implemented)
        """
        raise NotImplementedError()  # TODO
