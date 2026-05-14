# RCT-pipeline


End-to-end command-line workflow that pre-processes plot-level LiDAR point clouds, orchestrates [RayCloudTools](https://github.com/csiro-robotics/raycloudtools) command-line tools for tree segmentation and reconstruction, and provides custom wrapper scripts and post-processing tools to automate multi-step processing from plot-level data to per-tree outputs with extracted structural attributes.

---

## Overview

1. **Pre-process** — co-register and convert LiDAR data to PLY-format point clouds suitable for RayCloudTools.
2. **Use RayCloudTools for tree segmentation and reconstruction** — import rayclouds, tile large plots, extract terrain, trunks, trees, and generate mesh models.
3. **Post-processing** — extract tree-level attributes, select candidate trees, and prepare point clouds for QSM reconstruction.

---
## Project Data File Structure
Example RIEGL TLS project data file structure, where `ScanPos001`, `ScanPos002`, ... `ScanPosXXX` are the raw data from the scanner and `matrix` are derived RiSCAN Pro. `rxp2ply` and `downsample` are preprocessed data by performing [rxp-pipeline](https://github.com/tls-tools-ucl/rxp-pipeline).
```
20XX-XX-XX.XXX.riproject
  ├── raw
  |   ├── ScanPos001
  |   ├── ScanPos002
  |   ├── ScanPosXXX
  ├── matrix
  |   ├── ScanPos001.DAT
  |   ├── ScanPos002.DAT
  |   └── ScanPosXXX.DAT
  └── extraction
      ├── rxp2ply
      |   └── tiles created by rxp2ply.py from rxp-pipeline
      ├── downsample
      |   └── tiles created by downsample.py from rxp-pipeline
      └── rct-pipeline
          └── output from RCT-pipeline

```

---
## Phase 1: Pre-process LiDAR data

### Co-register scans and export PLY-format point clouds
- **For RIEGL TLS data**: Use [rxp-pipeline](https://github.com/tls-tools-ucl/rxp-pipeline) to convert raw plot-level data (`.rxp` or `.rdbx`) into downsampled and tiled PLY-format point clouds.
- **For LiDAR data collected from other instruments or platforms**: Pre-process the data independently and produce PLY-format point cloud files.

### Convert coordinate data types to `float` or `double`

RayCloudTools is written in C/C++ and expects standard PLY type names: `float` (32-bit) and `double` (64-bit). If the `x`, `y`, and `z` properties in a PLY file are labelled `float32` or `float64` (Python/MATLAB conventions), they must be renamed to `float` or `double` respectively before RayCloudTools can read the file correctly.


**Create and activate a conda environment:**

```bash
# Create environment (only needed once)
# Option 1: Using mamba (faster, recommended if available)
mamba env create -f environment.yml

# Option 2: Using conda (works everywhere but slower)
conda env create -f environment.yml

# Activate environment (required for each session)
conda activate rctpipeline
```


**Use [`ply2double.py`](scripts/ply2double.py) to perform this conversion.**

*Case 1: Convert a single file*

```bash
python scripts/ply2double.py -i input.ply -o output.ply
```

*Case 2: Convert all files in a directory*

```bash
python scripts/ply2double.py --idir input_directory --odir output_directory
```

---

## Phase 2: Tree segmentation and reconstruction from plot-level point cloud

### Prerequisites

Pull the RayCloudTools Docker image:

```bash
docker pull docker.io/tdevereux/raycloudtools:latest
```


> **Note:** Replace placeholder values such as `<PLOT_NAME>`, `<FILENAME>`, `<BASENAME>`, `<tile_size_in_x>`, `<tile_size_in_y>`, and `<overlap_size>` with values from your own dataset before running the commands listed below.



### Workflow 1 — `rayextract` workflow

Segment instances from the plot data.

#### Workflow overview

1. Convert point clouds into rayclouds.
`rayimport <FILENAME>.ply ray 0,0,-1 --max_intensity 0`
2. Extract terrain undersurface to mesh.
`rayextract terrain <FILENAME>.ply`
3. Extract tree trunk base locations and radii to text file.
`rayextract trunks <FILENAME>.ply`
4. Extract trees, and save segmented (coloured per-tree) cloud, tree attributes to text file, and mesh file.
`rayextract trees <FILENAME>.ply <BASENAME>_mesh.ply --grid_width <tile_size> --height_min <min_tree_H> --use_rays`
5. Report tree & branch info and save to `_info.txt` file.
`treeinfo <BASENAME>_trees.txt --branch_data`

#### Case 1 — No tiling needed (single plot point cloud)

If the plot point cloud is a single PLY file and does not need to be tiled, the workflow can be executed via our wrapper scripts [`run_rayextract_on_nonraycloud.sh`](scripts/run_rayextract_on_nonraycloud.sh) directly for streamlined and reproducible processing.

```bash
scripts/run_rayextract_on_nonraycloud.sh <FILENAME>.ply
```

#### Case 2 — Tiling needed

If the plot has already been tiled externally, or if it is large (e.g. 1 ha) or memory is limited, use RCT internal tiling to create tiled rayclouds before running the [rayextract workflow (command 2–5)](#workflow-overview) on each tile.

RCT internal tiling is preferred because it groups root points across neighbouring grid cells before forming initial tree segments, which helps avoid duplicate trees. Processing externally tiled data independently can reconstruct the same tree multiple times and lead to duplicated trees in the segmented outputs.

##### Step 1 — Convert point clouds into rayclouds

Import each PLY file as a raycloud:

```bash
docker run --rm \
-v "$PWD":/workspace \
-w /workspace \
docker.io/tdevereux/raycloudtools \
sh -lc 'for f in downsample/*downsample.ply; do rayimport "$f" ray 0,0,-1 --max_intensity 0; done'
```

##### Step 2 — Combine rayclouds 

If the plot contains more than one raycloud (e.g. one per tile or scan), combine them into a single whole-plot raycloud:

```bash
docker run --rm \
-v "$PWD":/workspace \
-w /workspace \
docker.io/tdevereux/raycloudtools \
sh -lc 'raycombine downsample/*_raycloud.ply --output rct-pipeline/<PLOT_NAME>_raycloud.ply'
```

If the plot contains only one raycloud, skip this step.

##### Step 3 — Split large rayclouds into tiles 

For large plots (e.g. 1 ha), split the whole-plot raycloud into tiles to reduce memory requirements. For small plots, or when available RAM is sufficient to process the whole plot, this step can be skipped.

**Tile size selection:** Avoid excessively small tile sizes, as they increase the proportion of trees that span tile boundaries. For a 1 ha plot, a tile size of 50 m × 50 m is a sensible starting point.

**Overlap size selection:** Set the overlap value to approximately the maximum expected crown radius to reduce edge effects and ensure trees at tile boundaries are fully captured.

```bash
cd rct-pipeline/

# Split the plot into a <tile_size_in_x>,<tile_size_in_y>,0 grid with a <overlap_size> buffer
docker run --rm \
-v "$PWD":/workspace \
-w /workspace \
docker.io/tdevereux/raycloudtools \
sh -lc 'raysplit <PLOT_NAME>_raycloud.ply grid <tile_size_in_x>,<tile_size_in_y>,0 <overlap_size>'

# Remove the whole-plot raycloud to save disk space
rm <PLOT_NAME>_raycloud.ply

# Move tiled rayclouds into a dedicated directory
mkdir tiled
mv ./*.ply tiled/
```

##### Step 4 — Generate tile index and tile boundaries (Optional)

Following Step 3, [`tile_index.py`](scripts/tile_index.py) generates the tile index and the spatial boundary of each tile (`xmin`, `xmax`, `ymin`, `ymax`).

**Note**: The tile index is useful for post-processing and spatial queries but is not required for tree segmentation. If Step 3 was skipped, skip this step as well.

```bash
conda activate rctpipeline
python scripts/tile_index.py -i tiled/*[0-9].ply -o ./tile_index.dat --verbose
```

##### Step 5 — Run `rayextract` on tiled rayclouds

The [rayextract workflow commands 2-5](#workflow-overview) can be executed via our wrapper scripts [`run_rayextract_on_raycloud.sh`](scripts/run_rayextract_on_raycloud.sh) for streamlined and reproducible processing.

> **Note:** Check wrapper script argument values and adjust if necessary:
> - `--grid_width 50` : tile grid width in metres
> - `--height_min 2` : minimum height (m) for a point to be counted as a tree
> - `--use_rays` : use rays (rather than just points) to reduce trunk radius overestimation in noisy cloud data


**To process a single tiled raycloud**

```bash
scripts/run_rayextract_on_raycloud.sh <FILENAME>.ply
```

**To process multiple tiled rayclouds**

*Option 1: Serial processing (recommended for single servers)*

Process tiles sequentially to avoid memory crashes. This is the safest approach when running on a single server with limited RAM.

```bash
for f in tiled/*[0-9].ply; do scripts/run_rayextract_on_raycloud.sh "$f"; done
```

*Option 2: Parallel processing (recommended for HPC or small rayclouds)*

Process tiles in parallel using [`batch_run_rct_parallel.py`](scripts/batch_run_rct_parallel.py). Recommended when:
- Running on HPC systems with job scheduling
- Individual rayclouds are < 10 GB each
- Sufficient RAM is available for concurrent processing

```bash
python scripts/batch_run_rct_parallel.py -i tiled/*[0-9].ply -s scripts/run_rayextract_on_raycloud.sh
```


### Workflow 2 — `treesplit` and `treemesh` workflow

Separate individual segmented trees from the plot or tiled rayclouds, and produce per-tree clouds, mesh models, and info files.

#### Workflow overview

1. Segment individual point clouds using unique colours
`raysplit <BASENAME>_segmented.ply seg_colour`
2. Extract tree data for each segmented instance.
`treesplit <BASENAME>_trees.txt per-tree`
3. Reindex segmented clouds to align with tree_id in treeinfo files.
[`reindex.py`](scripts/reindex.py): `python scripts/reindex.py -i <BASENAME>_segmented_*[0-9].ply -odir <BASENAME>_treesplit/`
4. Generate mesh models for individual segmented instances.
`treemesh <BASENAME>_treesplit/*_trees_[0-9]+\\.txt`
5. Reconstruct the leaf locations for individual segmented instances, and generate leaves mesh models.
```bash
find . -type f -regextype posix-extended -regex '.*_trees_[0-9]+\.txt$' | while read -r f; do
  segply="${f/_trees_/_segmented_}"
  rayextract leaves "$segply" "$f"
done
```
6. Export tree- & branch-level attributes.
`treeinfo <BASENAME>_treesplit/*_trees_[0-9]+\\.txt --branch_data`

#### Wrapper script

The workflow can be executed via our wrapper script [`run_treesplit_and_treemesh.sh`](scripts/run_treesplit_and_treemesh.sh) for streamlined and reproducible processing.

**To process a single tiled raycloud**

```bash
scripts/run_treesplit_and_treemesh.sh <FILENAME>.ply
```

**To process multiple tiled rayclouds**

Process tiles in parallel using [`batch_run_rct_parallel.py`](scripts/batch_run_rct_parallel.py):

```bash
python scripts/batch_run_rct_parallel.py -i tiled/*[0-9].ply -s scripts/run_treesplit_and_treemesh.sh
```

---

## Phase 3: Post-processing

### Extract tree-level attributes

[`extract_rct_tree_attrs.py`](scripts/extract_rct_tree_attrs.py) generates a CSV table summarising individual tree-level attributes from the RayCloudTools pipeline outputs. Attributes include:

| Attribute | Description |
|---|---|
| `x`, `y`, `z` | Tree base position |
| `height` | Total tree height |
| `DBH` | The smallest trunk diameter estimated across three height ranges proportional to tree height (H): 0.04–0.06 × H, 0.08–0.12 × H, and 0.12–0.18 × H. This value is derived from the RCT reconstructed QSM, not from point cloud. |
| `total_vol_L` | Total estimated wood volume in litre|
| `crown_radius` | Mean crown radius |


If a `matrix` directory is provided, the script computes the plot boundary from scan position matrices and classifies each segmented instance as inside or outside the plot. This classification is recorded as an attribute in the output CSV.

```bash
python scripts/extract_rct_tree_attrs.py \
    -r /path/to/rct-pipeline/tiled/ \
    -m /path/to/matrix/ \
    -s <site> \
    -p <plotid> \
    [-o /path/to/output_dir]
```

### Select candidate tree point clouds

Candidate tree point clouds can be selected based on `tree_id`, following the naming convention:

```
*_treesplit/*_segmented_{tree_id}.ply
```

Example criteria for filtering candidate trees are as below; adjust thresholds based on your specific requirements.

- `in_plot = True`
- `height >= 3 m`
- `DBH >= 0.1 m`

### Quality control and QSM reconstruction

Visually inspect the selected candidate segmented point clouds before further processing. Where segment errors are present, manual cleaning is recommended.

Once cleaned, QSMs can be reconstructed from the individual-tree point clouds.

---

## Citation

If you use this pipeline—or any part of the code in this repository—in any context (including research, operational workflows, teaching, commercial or non-commercial applications, or derivative software), please cite the RCT-pipeline:

> Yang, W., Wilkes, P. and Scholes, M. (2025) "RCT-pipeline: End-to-end workflow for plot-level LiDAR-based tree segmentation, 3D reconstruction, and attribute extraction using RayCloudTools". Zenodo. doi:10.5281/zenodo.17593930.

```bibtex
@misc{yang2025rctpipeline,
  author       = {Wanxin Yang and Phil Wilkes and Matthew Scholes},
  title        = {RCT-pipeline: End-to-end workflow for plot-level LiDAR-based tree segmentation, 3D reconstruction, and attribute extraction using RayCloudTools},
  year         = {2025},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.17593930},
  url          = {https://zenodo.org/record/17593930}
}
```
