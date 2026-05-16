"""
PLY Double Precision Converter

This script converts the data type of x, y, z coordinate properties in PLY (Polygon File Format) 
files to double precision. It supports both single file and batch directory processing modes.

Usage:
    Single file mode:
        python ply2double.py -i input.ply -o output.ply
    
    Directory mode:
        python ply2double.py --idir input_directory --odir output_directory [--num-prcs N]

Arguments:
    -i, --input          Path to a single input PLY file
    -o, --output         Path to a single output PLY file
    --idir, --idir       Directory containing PLY files to convert
    --odir, --odir       Output directory for converted PLY files
    --num-prcs           Number of parallel worker processes for batch mode (default: cpu_count - 2)
"""

import pandas as pd
import numpy as np
import argparse
import os
from glob import glob
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
from ply_io import read_ply
from ply_io import write_ply_double as write_ply


def convert_one(args_tuple):
    """Convert a single PLY file to double precision. Designed for parallel execution."""
    f, odir = args_tuple
    fn = os.path.basename(f)
    try:
        df = read_ply(f)
        os.makedirs(odir, exist_ok=True)
        write_ply(os.path.join(odir, fn), df)
        return fn, None
    except Exception as e:
        return fn, str(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert the datatype from float64 to double in a ply file')
    parser.add_argument('--idir', type=str, help='dir of ply file(s)')
    parser.add_argument('--odir', type=str, help='dir to save converted ply file(s)')
    parser.add_argument('-i', type=str, help='single input ply file')
    parser.add_argument('-o', type=str, help='single output ply file')
    parser.add_argument('--num-prcs', type=int, default=None,
                        help='Number of parallel worker processes for batch mode (default: cpu_count - 2)')
    args = parser.parse_args()

    # Handle single file mode
    if args.i and args.o:
        print(f"Converting: {args.i}", flush=True)
        df = read_ply(args.i)
        output_dir = os.path.dirname(args.o)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        write_ply(args.o, df)
        print(f"Done: {args.o}", flush=True)
    # Handle directory mode (parallel)
    elif args.idir and args.odir:
        fl = sorted(glob(os.path.join(args.idir, '*.ply')))
        total = len(fl)
        MAX_WORKERS = 8  # I/O-bound task: diminishing returns and RAM cost beyond 8 workers
        n_workers = args.num_prcs if args.num_prcs else max(1, cpu_count() - 2)
        n_workers = min(n_workers, cpu_count(), MAX_WORKERS, total) if total > 0 else 1
        print(f"Converting {total} PLY files to double precision using {n_workers} worker(s)...", flush=True)
        os.makedirs(args.odir, exist_ok=True)
        tasks = [(f, args.odir) for f in fl]
        completed = 0
        errors = []
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(convert_one, t): t[0] for t in tasks}
            for future in as_completed(futures):
                fn, err = future.result()
                completed += 1
                if err:
                    errors.append((fn, err))
                    print(f"[{completed}/{total}] ERROR {fn}: {err}", flush=True)
                else:
                    print(f"[{completed}/{total}] Done: {fn}", flush=True)
        if errors:
            print(f"Completed with {len(errors)} error(s). {total - len(errors)} files written to {args.odir}", flush=True)
        else:
            print(f"Done — {total} files written to {args.odir}", flush=True)
    else:
        print('Error: Please provide either (-i and -o) for single file mode or (--idir and --odir) for directory mode', flush=True)
        
