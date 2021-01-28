# !/usr/bin/python

import os
import sys
from os.path import basename
import argparse
from mkv.mkv import concat 

def initParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inFolder", type=str, default=None,
                            help="Folder that contains mkv files")
    parser.add_argument("--inFiles", type=argparse.FileType('r'), nargs='+', default=None,
                            help="Path(s) to mkv files to combine")
    parser.add_argument('--outpath',  type=str,
                            help="Path to stored mkv")
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-r', '--recursive', action='store_true')
    return parser
    
# _______________Can be called as main__________________
if __name__ == '__main__':
    parser = initParser()
    args = parser.parse_args()
    if args.recursive and args.inFolder is not None:
        paths = [os.path.join(args.inFolder, o) for o in os.listdir(args.inFolder) if os.path.isdir(os.path.join(args.inFolder,o))]
        for path in paths:
            files = [os.path.join(path, o) for o in os.listdir(path) if os.path.isfile(os.path.join(path,o))]
            concat(files, os.path.join(path, "joined.mkv"), verbose=args.verbose)
        print(paths)
    else:
        files = []
        if args.inFolder is not None:
            files = [os.path.join(args.inFolder, o) for o in os.listdir(args.inFolder) if os.path.isfile(os.path.join(args.inFolder,o))]

        elif args.inFiles is not None:
            files = [file.name for file in args.inFiles]
        files = [file for file in files if os.path.basename(file)[0] != "."]
        concat([f for f in files], args.outpath, verbose=args.verbose)
        

    print(("Bye Bye from " + str(os.path.basename(__file__))))
