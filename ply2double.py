import pandas as pd
import numpy as np
import argparse
import os
from glob import glob
from ply_io_double import read_ply, write_ply


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert the datatype from float64 to double in a ply file')
    parser.add_argument('-i', '--input', type=str, help='dir of ply file(s)')
    parser.add_argument('-o', '--output', type=str, help='dir to save converted ply file(s)')
    args = parser.parse_args()

    fl = glob(os.path.join(args.input, '*.ply'))
    for f in fl:
        print(f)
        # filename
        fn = os.path.basename(f)
        # read the ply file
        df = read_ply(f)
        # rewrite the ply file
        os.makedirs(args.output, exist_ok=True)
        write_ply(os.path.join(args.output, fn), df)
        
