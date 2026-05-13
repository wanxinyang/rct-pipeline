"""
================================================================================
Tree-Level Attributes Extraction from RCT-pipeline Outputs
================================================================================

This script extracts tree-level attributes from RCT-pipeline outputs,
including tile, tree_id, in_plot, x, y, z, height, DBH, total_vol_L, and crown_radius.

Main functionalities:
1. Read tree attributes and root x, y, z locations from RCT treeinfo files
2. Calculate scan-based plot boundaries and determine in-plot trees
3. Export tree-level attributes into a CSV file

Author: Wanxin Yang
Created: 2025-10-10
Last Modified: 2026-05-04
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
import logging
import numpy as np
import pandas as pd
import geopandas as gp
from shapely.geometry import Point

def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract tree-level attributes from RCT-pipeline outputs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Usage example:\n"
            "python extract_rct_tree_attrs.py\n"
            "  -r /path/to/rct_extraction_dir\n"
            "  -m /path/to/matrix_dir\n"
            "  -s <site>\n"
            "  -p <plotid>\n" 
            "  [-o /path/to/output_dir] \n"
        )
    )
    
    # Required input paths
    parser.add_argument('-r', '--dir_rct_extraction', type=str, required=True,
                        help='Required. Path to RCT-pipeline extraction results directory')
    parser.add_argument('-m', '--dir_matrix', type=str, required=True,
                        help='Required. Path to directory containing SOP matrix files (*.DAT or *.dat)')
    
    # Required plot metadata
    parser.add_argument('-s', '--site', type=str, required=True,
                        help='Required. Site name, e.g. Epping')
    parser.add_argument('-p', '--plotid', type=str, required=True,
                        help='Required. Plot ID, e.g. P1')

    # Optional arguments
    parser.add_argument('-o', '--odir', type=str, default='.',
                        help='Optional. Output directory for tree attributes CSV files (default: current directory)')
    
    return parser.parse_args()

def setup_logging(odir, site, plotid):
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = odir / f'{site}_{plotid}_tree_extraction_{timestamp}.log'

    logger = logging.getLogger('TreeExtraction')
    logger.setLevel(logging.INFO)

    logger.handlers.clear()
    
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.INFO)
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    logger.info("="*80)
    logger.info("Tree Attribute Extraction from RCT-pipeline Outputs")
    logger.info("="*80)
    logger.info(f"Log file: {log_filename}")
    
    return logger


def parse_scan_id_from_stem(stem):
    
    parts = stem.split('ScanPos', 1)
    if len(parts) == 2 and parts[1] != '':
        return parts[1]
    return stem

if __name__ == '__main__':
    args = parse_args()
    
    # Validate required metadata
    if not args.site:
        raise ValueError("Site information is required. Please provide --site argument.")
    if not args.plotid:
        raise ValueError("Plot ID information is required. Please provide --plotid argument.")
    
    # Extract arguments
    site = args.site
    plotid = args.plotid
    dir_matrix = Path(args.dir_matrix)
    dat_files = list(dir_matrix.glob('*.DAT')) + list(dir_matrix.glob('*.dat'))
    parent_dir = Path(args.dir_rct_extraction)
    odir = Path(args.odir)
    
    if not odir.exists():
        raise ValueError(f"Output directory does not exist: {odir}\nPlease create it first or specify an existing directory.")
    
    logger = setup_logging(odir, site, plotid)
    
logger.info(f"Site: {site}")
logger.info(f"Plot ID: {plotid}")
logger.info("")

logger.info("Input directories:")
logger.info(f"  SOP matrix dir: {dir_matrix}")
logger.info(f"  SOP matrix files found: {len(dat_files)}")
logger.info(f"  RCT extraction dir: {parent_dir}")
logger.info("")
logger.info("Output directories:")
logger.info(f"  CSV output dir: {odir}")
logger.info("")

logger.info("Discovering input files...")
treeinfo_files = sorted(parent_dir.glob('*_info.txt'))

treeinfo_files = [str(f) for f in treeinfo_files]

logger.info(f"Found {len(treeinfo_files)} treeinfo files")
if treeinfo_files:
    logger.info(f"  Example: {treeinfo_files[0]}")
logger.info("")


def treeinfo_attributes_tree(tree_file):
    """
    Adapted from: Tim Devereux / PyTreeFile
    Source: https://github.com/tim-devereux/PyTreeFile/blob/main/pytreefile/treefiles.py
    """
    line_list = []
    root_xyz = []
    with open(tree_file, "r") as file:
        lines = file.readlines()
        for line in lines:
            chunks = line.split(", ")
            cell_data = chunks[0].strip().split(",")
            if len(cell_data) == 7:
                line_list.append(cell_data)
                if len(chunks) > 1:
                    root_parts = chunks[1].strip().split(",")
                    root_xyz.append(root_parts[:3])
                else:
                    root_xyz.append([None, None, None])
    
    df = pd.DataFrame(line_list[1:], columns=line_list[0]).astype(float)
    if len(df) >= 1:
        df.insert(0, "tree_id", range(1, len(df) + 1))

    xyz_df = pd.DataFrame(root_xyz[1:], columns=['x', 'y', 'z']).astype(float)
    df = pd.concat([df.reset_index(drop=True), xyz_df.reset_index(drop=True)], axis=1)

    df_segments = treeinfo_attributes_segment(tree_file)
    total_vol_l = ensure_segment_volume_l(df_segments).groupby(df_segments["tree_id"]).sum()
    total_vol_l = total_vol_l.rename("total_vol_L")
    df = df.merge(total_vol_l, left_on="tree_id", right_index=True, how="left")
    df["total_vol_L"] = df["total_vol_L"].fillna(0.0).round(2)

    return df


def treeinfo_attributes_segment(tree_file):
    """
    Adapted from: Tim Devereux / PyTreeFile
    Source: https://github.com/tim-devereux/PyTreeFile/blob/main/pytreefile/treefiles.py
    """
    line_list = []
    tree_ids = []
    tree_id = 0

    with open(tree_file, "r") as file:
        lines = file.readlines()
        line_count = 0
        for line in lines:
            data = line.split(", ")
            for row in data:
                section_data = row.strip().split(", ")
                cell_data = section_data[0].strip().split(",")
                if len(cell_data) == 7 and all(
                    x.replace(".", "", 1).replace("-", "", 1).isdigit() for x in cell_data
                ):
                    tree_id += 1
                if len(cell_data) > 7:
                    if tree_id != 0:
                        tree_ids.append(tree_id)
                    line_list.append(cell_data)
            line_count += 1
    df = pd.DataFrame(line_list[1:], columns=line_list[0]).astype(float)
    if len(tree_ids) != len(df):
        raise ValueError(
            f"tree_id count ({len(tree_ids)}) does not match segment row count ({len(df)}) in {tree_file}"
        )
    df.insert(0, "tree_id", tree_ids)
    # remove row where parent_id is -1.0
    df = df[df["parent_id"] != -1.0]
    return df


def ensure_segment_volume_l(df_segments):
    if "volume" not in df_segments.columns:
        raise ValueError("Column 'volume' not found in segment attributes.")

    volume_m3 = pd.to_numeric(df_segments["volume"], errors="coerce").fillna(0.0)
    return volume_m3 * 1000.0


df_trees_info = pd.DataFrame()
for fn in treeinfo_files:
    x, y = os.path.split(fn)[1].split('.')[0].split('_')[3:5]
    tile = f'Tile_{x}_{y}'
    
    df = treeinfo_attributes_tree(fn)
    df['tile'] = tile
    
    cols = list(df.columns)
    cols = [cols[-1]] + cols[:-1]
    df = df[cols]
    df_trees_info = pd.concat([df_trees_info, df])

logger.info(f"Loaded {len(df_trees_info)} tree records from treeinfo files")
df_trees_info

df_trees_merged = df_trees_info.copy()

df_trees_merged = df_trees_merged.drop_duplicates(subset=['x', 'y', 'z'], keep=False)

df_trees_merged['plot_id'] = plotid.split('_')[-1]

cols = list(df_trees_merged.columns)
cols = [cols[-1]] + cols[:-1]
df_trees_merged = df_trees_merged[cols]

df = df_trees_merged.copy()

sp = gp.GeoDataFrame(columns=['x', 'y', 'z', 'sp'], geometry=[])

dir_matrix_path = Path(dir_matrix)

dat_files = list(dir_matrix_path.glob('*.DAT')) + list(dir_matrix_path.glob('*.dat'))
if not dat_files:
    raise ValueError(f"No .DAT or .dat files found in {dir_matrix_path}. Please check the directory path.")

for i, dat in enumerate(dat_files):
    sp.loc[i, 'ScanPos'] = parse_scan_id_from_stem(dat.stem)
    sp.iloc[i, :3] = np.loadtxt(str(dat))[:3, 3]

sp['geometry'] = [Point(r.x, r.y) for r in sp.itertuples()]
sp = sp.set_geometry('geometry')

extent = sp.unary_union.minimum_rotated_rectangle
area = extent.area
logger.info(f'Plot area (minimum rotated rectangle): {area / 1e4:.2f} ha')

df['geometry'] = [Point(x, y) for x, y in zip(df['x'], df['y'])]
df = gp.GeoDataFrame(df, geometry='geometry')  
df['in_plot'] = df.within(extent)
df['site'] = site

cols = list(df.columns)
cols = [cols[-1]] + cols[:3] + ['in_plot'] + cols[3:-3]
df = df[cols]

## Filter trees of interest (in-plot, with minimum height and DBH thresholds)
trees_interested = df[(df.in_plot == True) & (df.height >= 3) & (df.DBH >= 0.1)]

# Keep only requested output columns in the required order
output_cols = [
    'site', 'plot_id', 'tile', 'tree_id', 'in_plot', 'x', 'y', 'z',
    'height', 'DBH', 'total_vol_L', 'crown_radius'
]
missing_output_cols = [c for c in output_cols if c not in df.columns]
if missing_output_cols:
    raise ValueError(f"Missing required output columns: {missing_output_cols}")
df = df[output_cols]

# Generate output filename
ofn = odir / f'{site}_{plotid}_treeLevel_attr_rct.csv'

# Save to CSV
df.to_csv(str(ofn), index=False)
# Log summary statistics
logger.info("")
logger.info("="*80)
logger.info("PROCESSING COMPLETE - SUMMARY STATISTICS")
logger.info("="*80)
logger.info(f"Total instances extracted: {len(df)}")
logger.info(f"In-plot instances: {df['in_plot'].sum()}")
logger.info(f"Instances with H>=3m & DBH>=10cm: {len(trees_interested)}")
logger.info(f"")
logger.info(f"Output CSV: {ofn}")
logger.info("="*80)
logger.info("Pipeline completed successfully!")
logger.info("="*80)
