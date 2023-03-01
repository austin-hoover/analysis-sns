from __future__ import print_function
from datetime import datetime
import math
from math import cos
from math import sin
from math import sqrt
import os
from pprint import pprint
import random
import sys


DIAG_WIRE_ANGLE = math.radians(-45.0)
INF = 1.0e20


def transpose(array):
    return [list(x) for x in zip(*array)]


def split(items, token):
    """Split `items` into sublists, excluding `token`.

    Example:
    >>> items = ['cat', 'dog', 'x', 'tree', 'bark']
    >>> split_list(items, 'x')
    [['cat', 'dog'], ['tree', 'bark']]
    """
    indices = [i for i, item in enumerate(items) if item == token]
    sublists = []
    if items[0] != token:
        sublists.append(items[: indices[0]])
    for lo, hi in zip(indices[:-1], indices[1:]):
        sublists.append(items[lo + 1 : hi])
    if items[-1] != token:
        sublists.append(items[indices[-1] + 1 :])
    return sublists


def string_to_list(string):
    """Convert string to list of floats.
    
    '1 2 3' -> [1.0, 2.0, 3.0])
    """
    return [float(token) for token in string.split()]


class PTA(dict):
    """Dictionary of profiles for one measurement.

    Each key is a wire-scanner ID; each value is a dict with the following keys/values:
        "x" : list
            The horizontal (x) positions [mm].
        "y" : list
            The vertical (y) positions [mm].
        "u" : list
            The diagonal (u) positions [mm].
        "fx" : list
            The horizontal (x) profile (raw).
        "fy" : list
            The vertical (y) profile (raw).
        "fu" : list
            The diagonal (u) profile (raw).
        "fx_fit" : list
            The horizontal (x) profile (Gaussian fit).
        "fy_fit" : list
            The vertical (y) profile (Gaussian fit).
        "fu_fit" : list
            The diagonal (u) profile (Gaussian fit).
        "stats" : dict with the following keys/values:
            [...]
    
    Attributes
    ----------
    filename : str
        Full path to the PTA file.
    filename_short : str
        Only include the filename, not the full path.
    timestamp : datetime
        Represents the time at which the data was taken.
    timestamp_short : str
        "YYMMDDHHMMSS".
    pvloggerid : int
        The PVLoggerID of the measurement (this gives a snapshot of the machine state).
    node_ids : list[str]
        The ID of each wire-scanner. (These are the dictionary keys.)
    """
    def __init__(self, filename):
        dict.__init__(self)
        self.filename = filename
        self.filename_short = filename.split("/")[-1]
        self.timestamp = None
        self.timestamp_short = None
        self.pvloggerid = None
        self.node_ids = None
        self.read_file()

    def read_file(self):
        # Store the timestamp.
        date, time = self.filename.split("WireAnalysisFmt-")[-1].split("_")
        time = time.split(".pta")[0]
        year, month, day = [int(token) for token in date.split(".")]
        hour, minute, second = [int(token) for token in time.split(".")]
        self.timestamp = datetime(year, month, day, hour, minute, second)
        self.timestamp_short = "{}{:02.0f}{:02.0f}{:02.0f}{:02.0f}{:02.0f}".format(
            year, month, day, hour, minute, second
        )
        self.timestamp_short = self.timestamp_short[2:]  # just use last two year digits.

        # Collect lines corresponding to each wire-scanner
        file = open(self.filename, "r")
        lines = dict()
        ws_id = None
        for line in file:
            line = line.rstrip()
            if line.startswith("RTBT_Diag"):
                ws_id = line
                continue
            if ws_id is not None:
                lines.setdefault(ws_id, []).append(line)
            if line.startswith("PVLoggerID"):
                self.pvloggerid = int(line.split("=")[1])
        file.close()
        self.node_ids = sorted(list(lines))

        # Read the lines.
        for node_id in self.node_ids:            
            # Split lines into three sections:
            #     stats: statistical signal parameters;
            #     raw: wire positions and raw signal amplitudes;
            #     fit: wire positions and Gaussian fit amplitudes.
            # There is one blank line after each section.
            sep = ""
            lines_stats, lines_raw, lines_fit = split(lines[node_id], sep)[:3]

            # Remove headers and dashed lines beneath headers.
            lines_stats = lines_stats[2:]
            lines_raw = lines_raw[2:]
            lines_fit = lines_fit[2:]

            # The columns of the following array are ['pos', 'fy', 'fu', 'fx',
            # 'x', 'y', 'u']. (NOTE: This is not the order that is written
            # in the file header.)
            data_arr_raw = [string_to_list(line) for line in lines_raw]
            pos, fy, fu, fx, x, y, u = transpose(data_arr_raw)

            # This next array is the same, but it contains 'fy_fit', 'fu_fit', 'fx_fit',
            # instead of 'y', 'u', 's'.
            data_arr_fit = [string_to_list(line) for line in lines_fit]
            pos, fy_fit, fu_fit, fx_fit, x, y, u = transpose(data_arr_fit)

            # Get statistical signal parameters. (Headers do not give true ordering.)
            stats = dict()
            for line in lines_stats:
                tokens = line.split()
                name = tokens[0].lower()
                vals = [float(val) for val in tokens[1:]]
                stat_y_fit, stat_y_rms, stat_u_fit, stat_u_rms, stat_x_fit, stat_x_rms = vals
                stats["{}_x_rms".format(name)] = stat_x_rms
                stats["{}_x_fit".format(name)] = stat_x_fit
                stats["{}_y_rms".format(name)] = stat_y_rms
                stats["{}_y_fit".format(name)] = stat_y_fit
                stats["{}_u_rms".format(name)] = stat_u_rms
                stats["{}_u_fit".format(name)] = stat_u_fit

            self[node_id] = {
                "x": x,
                "y": y,
                "u": u,
                "fx": fx,
                "fy": fy,
                "fu": fu,
                "fx_fit": fx_fit,
                "fy_fit": fy_fit,
                "fu_fit": fu_fit,
                "stats": stats
            }
            
            
filename = "WireAnalysisFmt-2023.02.27_23.57.00.pta.txt"
wirescan = PTA(filename)
print(wirescan["RTBT_Diag:WS24"]["stats"])