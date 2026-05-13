"""
PLY Double Precision Converter

This script converts the data type of x, y, z coordinate properties in PLY (Polygon File Format) 
files to double precision. It supports both single file and batch directory processing modes.

Usage:
    Single file mode:
        python ply2double.py -i input.ply -o output.ply
    
    Directory mode:
        python ply2double.py --idir input_directory --odir output_directory

Arguments:
    -i, --input          Path to a single input PLY file
    -o, --output         Path to a single output PLY file
    --idir, --idir       Directory containing PLY files to convert
    --odir, --odir       Output directory for converted PLY files
"""

import pandas as pd
import numpy as np
import argparse
import os
from glob import glob
from ply_io import read_ply
from ply_io import write_ply_double as write_ply


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert the datatype from float64 to double in a ply file')
    parser.add_argument('--idir', type=str, help='dir of ply file(s)')
    parser.add_argument('--odir', type=str, help='dir to save converted ply file(s)')
    parser.add_argument('-i', type=str, help='single input ply file')
    parser.add_argument('-o', type=str, help='single output ply file')
    args = parser.parse_args()

    # Handle single file mode
    if args.i and args.o:
        print(args.i)
        # read the ply file
        df = read_ply(args.i)
        # rewrite the ply file
        os.makedirs(os.path.dirname(args.o), exist_ok=True)
        write_ply(args.o, df)
    # Handle directory mode
    elif args.idir and args.odir:
        fl = glob(os.path.join(args.idir, '*.ply'))
        for f in fl:
            print(f)
            # filename
            fn = os.path.basename(f)
            # read the ply file
            df = read_ply(f)
            # rewrite the ply file
            os.makedirs(args.odir, exist_ok=True)
            write_ply(os.path.join(args.odir, fn), df)
    else:
        print('Error: Please provide either (-i and -o) for single file mode or (--idir and --odir) for directory mode')
        
