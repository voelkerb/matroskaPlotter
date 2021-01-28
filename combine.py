# !/usr/bin/python

import os
import sys
from os.path import basename

import argparse
from mkv.mkv import combine

def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=argparse.FileType('r'), nargs='+',
                            help="Path(s) to mkv files to combine")
    parser.add_argument('--outpath',  type=str, default="test.mkv",
                            help="Path to stored mkv")
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser
    
# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()

    combine([f.name for f in args.paths], args.outpath)

    print(("Bye Bye from " + str(os.path.basename(__file__))))
