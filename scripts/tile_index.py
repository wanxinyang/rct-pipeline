"""
================================================================================
Tile Index Generator for RCT-pipeline Tiled Rayclouds
================================================================================

This script generates a tile index file containing the spatial bounds (xmin, xmax,
ymin, ymax) of tiled PLY files produced by RayCloudTools' raysplit command.
The index is useful for post-processing and spatial queries.

Main functionalities:
1. Extract spatial bounds from tiled raycloud PLY files in parallel
2. Generate tile identifiers from grid coordinates (e.g., Tile_0_1)
3. Export tile index with spatial bounds to a text file

Usage:
    python tile_index.py -i tiled/*[0-9].ply -o tile_index.dat --verbose

Arguments:
    -i, --pc              Input tiled PLY files (supports glob patterns)
    -o, --tile-index      Output tile index file (default: tile_index.dat)
    --num-prcs            Number of parallel processes (default: 10)
    --verbose             Print progress information

Author: Wanxin Yang, Phil Wilks
Created: 2025-07-10
Last Modified: 2026-05-14
"""
import os
import sys
import glob
import json
import argparse
import time

from tqdm import tqdm
import pandas as pd
import numpy as np

import ply_io
import pdal

import threading
import concurrent.futures
#%%
def tile_index(ply, args):
    """
    Extract spatial bounds from a PLY file and write to tile index.
    
    Args:
        ply: Path to PLY file
        args: Command line arguments including Lock for thread safety
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if args.verbose:
            with args.Lock:
                print(f'processing: {ply}')

        reader = {"type":f"readers{os.path.splitext(ply)[1]}",
                  "filename":ply}
        stats =  {"type":"filters.stats",
                  "dimensions":"X,Y"}
        JSON = json.dumps([reader, stats])
        pipeline = pdal.Pipeline(JSON)
        pipeline.execute()
        JSON = pipeline.metadata
        # print(f'JSON: {JSON}')

        # Tile x and y coordinates
        Xmin = JSON['metadata']['filters.stats']['statistic'][0]['minimum']
        Xmax = JSON['metadata']['filters.stats']['statistic'][0]['maximum']
        Ymin = JSON['metadata']['filters.stats']['statistic'][1]['minimum']
        Ymax = JSON['metadata']['filters.stats']['statistic'][1]['maximum']

        ## find the middle point of the tile
        # X = JSON['metadata']['filters.stats']['statistic'][0]['average']
        # Y = JSON['metadata']['filters.stats']['statistic'][1]['average']
        # T = int(os.path.split(ply)[1].split('.')[0])
        
        # raysplit grid x,y coords
        x,y = os.path.split(ply)[1].split('.')[0].split('_')[-2:]
        T = f'Tile_{x}_{y}'
        # print(f'Tile: {T}, Xmin: {Xmin:.2f}, Xmax: {Xmax:.2f}, Ymin: {Ymin:.2f}, Ymax: {Ymax:.2f}')
        
        with args.Lock:   
            with open(args.tile_index, 'a') as fh:
                fh.write(f'{T} {Xmin:.2f} {Xmax:.2f} {Ymin:.2f} {Ymax:.2f}\n')
                if args.verbose:
                    print(f'write tile index: {T} {Xmin:.2f} {Xmax:.2f} {Ymin:.2f} {Ymax:.2f}')
        
        return True
        
    except Exception as e:
        with args.Lock:
            print(f'ERROR processing {ply}: {str(e)}', file=sys.stderr)
        return False

def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--pc', type=str, nargs='*', required=True, help='input tiles')
    parser.add_argument('-o','--tile-index', default='tile_index.dat', help='tile index file')
    parser.add_argument('--num-prcs', type=int, default=10, help='number of cores to use')
    parser.add_argument('--verbose', action='store_true', help='print something')
    return parser.parse_args(argv)

#%%
if __name__ == '__main__':

    # ## test 
    # argv = ['-i', 'raycloud_0_3.ply',
    #         '-t', 'tile_index.dat',
    #         '--verbose']
    # args = parse_args(argv)
    
    args = parse_args()
    
    # Remove existing tile index file if it exists
    if os.path.exists(args.tile_index):
        os.remove(args.tile_index)
        if args.verbose:
            print(f'Removed existing tile index: {args.tile_index}')
    
    print(f'Processing {len(args.pc)} tiles...')
    print(f'Output: {args.tile_index}')
    print(f'Parallel workers: {args.num_prcs}')
    
    start_time = time.time()
    args.Lock = threading.Lock()
    
    # Process tiles with progress bar
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_prcs) as executor:
        futures = [executor.submit(tile_index, ply, args) for ply in args.pc]
        results = []
        for future in tqdm(concurrent.futures.as_completed(futures),
                          total=len(futures), 
                          desc='Processing tiles',
                          unit='tile'):
            results.append(future.result())
    
    # Summary
    elapsed_time = time.time() - start_time
    success_count = sum(1 for r in results if r)
    failed_count = len(results) - success_count
    
    print(f'\n=== Summary ===')
    print(f'Total tiles: {len(args.pc)}')
    print(f'Successful: {success_count}')
    print(f'Failed: {failed_count}')
    print(f'Time elapsed: {elapsed_time:.2f} seconds')
    print(f'Average time per tile: {elapsed_time/len(args.pc):.2f} seconds')
    print(f'Tile index saved to: {args.tile_index}')
    
    if failed_count > 0:
        print(f'\nWARNING: {failed_count} tiles failed to process. Check error messages above.')
        sys.exit(1)