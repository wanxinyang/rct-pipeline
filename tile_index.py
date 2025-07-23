#%%
import os
import sys
import glob
import json
import argparse

from tqdm import tqdm
import pandas as pd
import numpy as np

import ply_io
import pdal

import threading
import concurrent.futures
#%%
def tile_index(ply, args):

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
            print(f'write tile index: {T} {Xmin:.2f} {Xmax:.2f} {Ymin:.2f} {Ymax:.2f}')

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

    args.Lock = threading.Lock()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.num_prcs) as executor:
        futures = [executor.submit(tile_index, ply, args) for ply in args.pc]
        for _ in tqdm(concurrent.futures.as_completed(futures),
                      total=len(futures), desc='Processing tiles'):
            pass