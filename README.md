# RCT-pipeline:

End-to-end command-line workflow that converts plot‑level RIEGL TLS data into tiled PLYs, orchestrates the [RayCloudTools](https://github.com/csiro-robotics/raycloudtools/tree/main) command-line tools to segment and reconstruct individual trees, and produces per-tree 3D meshes and structural attribute outputs.

Note: [RayCloudTools](https://github.com/csiro-robotics/raycloudtools/tree/main) is an open-source research library; this repository provides workflows and scripts for the preprocessing, automation and postprocessing required to take raw plot-level TLS data to final individual-tree outputs.

## Overview

- Convert co-registered RIEGL TLS data to tiled PLY point clouds with configurable tile size, overlap, buffer and filtering.
- Downsample and convert point clouds for ingestion into RayCloudTools.
- Run RayCloudTools workflows to extract terrain, trunks, trees, and generate mesh models.
- Optional: produce per-tree segmented outputs.

## Usage

### 1. Convert RIEGL RiSCAN project outputs to tiled ply-format point clouds

This is a modification version of [rxp-pipeline](https://github.com/philwilkes/rxp-pipeline), which reads in rdbx files and allows user-defined overlap area between tiles.
#### Prerequisites
Install a PDAL environment. Detailed instructions can be found in **"Compiling PDAL with python bindings and .rxp support"** section in [rxp-pipeline README](https://github.com/philwilkes/rxp-pipeline/blob/main/README.md).

#### Command:
```bash
# activate the installed PDAL env
conda activate pdal

# run riproject2ply.py
python riproject2ply.py \
--riproject /PATH/TO/XXXX.RiSCAN \
--tile 10 \
--tile-overlap 0 \
--buffer 10 \
--deviation 15 \
--reflectance -20 5 \
--rotate-bbox \
--store-tmp-with-sp \
--verbose 
```

Parameters explanation:
- `--tile <size>`: Defines the size of each tile (default: 20), unit in metre.
- `--tile-overlap <size>`: Sets the overlap between tiles (default: 5), unit in metre.
- `--buffer <size>`: Sets the size of buffer around the bounding box (plot boundary) (default: 10), unit in metre.
- `--deviation <value>`: Filters points based on deviation, keeping only those below the specified value (default: 15).
- `--reflectance <min> <max>`: Filters points based on reflectance values within the specified range (e.g., -20 to 5).
- `--rotate-bbox`: Rotates the bounding box to better align with the point cloud's orientation.
- `--store-tmp-with-sp`: spits out individual tmp files for scans and merge them back afterwards.
- `--verbose`: Enables detailed logging for debugging and progress tracking.
- `--pos <position>`: Specifies a scan position identifier to process a single scan (e.g., `001`).

More available parameters can be found in [riproject2ply.py](https://github.com/wanxinyang/rct-pipeline/blob/main/riproject2ply.py).


### 2. Downsample tiled point clouds and convert them from float64 to double

```bash
mkdir downsample && cd downsample
python downsample.py -i '../' --length .02 --verbose
python ply2double.py -i ./ -o ./
```

Parameters explanation:
- `-i <input_path>`: Specifies the input directory containing tiled point clouds.
- `--length <voxel_size>`: Defines the voxel size for downsampling (default: 0.02), unit in metre.
- `--verbose`: Enables detailed logging for debugging and progress tracking.


### 3. Run raycloudtools pipeline using Docker

#### 3.1 Prerequisites
Install rct docker image from Docker Hub
```bash
docker pull docker.io/tdevereux/raycloudtools:latest
```

Open a docker container:
```bash
docker run -it -v $PWD:/workspace docker.io/tdevereux/raycloudtools
```


#### 3.2 Convert downsampled point cloud into raycloud
```bash
for f in downsample/*downsample.ply; do rayimport "$f" ray 0,0,-1 --max_intensity 0; done
```


#### 3.3 Combine individual rayclouds into a unified whole-plot raycloud 
```bash
raycombine downsample/*_raycloud.ply --output <PLOT_NAME>_raycloud.ply
```


#### 3.4 Split the whole-plot raycloud into tiles of specificed size
To minimise duplicated trees, avoid using excessively small tile sizes, as this increases the likelihood of trees appearing on tile edges or within overlapping buffer zones. For a one-hectare plot, a tile size of **50 m × 50 m with a 10 m overlap** offers a good balance between data integrity and computational efficiency.
```bash
# split the plot into a 50,50,0 centred grid of files, cell width are 50 m in x and y, 0 in z, with a 10 m overlap between cells 
raysplit <PLOT_NAME>_raycloud.ply grid 50,50,0 10

# remove the whole-plot raycloud to save space
rm <PLOT_NAME>_raycloud.ply

# move tiled data into a new dir
mkdir tiled 
mv *.ply tiled/

# exit the docker container
exit
```


#### 3.5 Generate tile index and boundary (xmin, xmax, ymin, ymax)
Note, this command is run with conda env outside the docker container.
```bash
conda activate pdal
python tile_index.py -i tiled/*.ply -o ./tile_index.dat --verbose
```


#### 3.6 Run rayextract workflow on tiled raycloud(s)
##### Workflow overview:
1. Extract terrain undersurface to mesh. 
`rayextract terrain <FILENAME>.ply`
2. Extract tree trunk base locations and radii to text file.
`rayextract trunks <FILENAME>.ply`
3. Extract trees, and save segmented (coloured per-tree) cloud, tree attributes to text file, and mesh file for the whole tile.
`rayextract trees <FILENAME>.ply <BASENAME>_mesh.ply" --grid_width 50 --height_min 2 --use_rays 2`
4. Report tree & branch info and save to _info.txt file.
`treeinfo <BASENAME>_trees.txt --branch_data`

Note: need to check the argument values in `run_rayextract_on_raycloud.sh`, and adjust if necessary:
- `--grid_width 50` : The cloud has been gridded with 50 m
- `--height_min 2` : minimum height of 2 m counted as a tree
- `--use_rays 2` : use rays to reduce trunk radius overestimation in noisy cloud data


##### Run the workflow using my wrapper script:
Case 1: run the workflow for a single tile
```bash
run_rayextract_on_raycloud.sh tiled/<FILENAME>.ply
```

Case 2: batch process multiple tiles
```bash
python batch_run_rct_parallel.py -i tiled/*[0-9].ply -s run_rayextract_on_raycloud.sh
```


#### 3.7 (Optional) Run treesplit and treemesh workflow on the tiled raycloud(s)
##### Workflow overview:
1. Segment individual point clouds using unique colours
`raysplit <BASENAME>_segmented.ply seg_colour`
2. Extract tree data for each segmented instance.
`treesplit <BASENAME>_trees.txt per-tree`
3. Reindex segmented clouds to align with tree_id in treeinfo files.
`python reindex.py -i <BASENAME>_segmented_*[0-9].ply -odir <BASENAME>_treesplit/`
4. Generate mesh models for individual segmented instances.
`treemesh <BASENAME>_treesplit/*_trees_[0-9]+\\.txt`
5. Reconstruct the leaf locations for individual segmented instances, and generate leaves mesh models.
```bash
find . -type f -regextype posix-extended -regex '.*_trees_[0-9]+\\.txt$' | while read -r f; do
  segply="${f/_trees_/_segmented_}"
  rayextract leaves "$segply" "$f"
done
```
6. Export tree- & branch-level attributes.
`treeinfo <BASENAME>_treesplit/*_trees_[0-9]+\\.txt --branch_data`


##### Run the workflow using my wrapper script:
Case 1: run the workflow for a single tile
```bash
run_treesplit_and_treemesh.sh tiled/<FILENAME>.ply
```

Case 2: batch process multiple tiles
```bash
python batch_run_rct_parallel.py -i tiled/*[0-9].ply -s run_treesplit_and_treemesh.sh
```

## Citation

If you use this pipeline—or any part of the code in this repository—in any context (including research, operational workflows, teaching, commercial or non-commercial applications, or derivative software), please cite the RCT-pipeline:

> Yang, W., Wilkes, P. and Scholes, M. (2025) “RCT-pipeline: End-to-end workflow for plot-level LiDAR-based tree segmentation, 3D reconstruction, and attribute extraction using RayCloudTools”. Zenodo. doi:10.5281/zenodo.17593930.

BibTeX

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

