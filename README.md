# Usage:

## 1. Convert RIEGL RiSCAN project outputs to tiled ply-format point clouds

This is a modification version of [rxp-pipeline](https://github.com/philwilkes/rxp-pipeline), which reads in rdbx files and allows user-defined overlap area between tiles.
### Prerequisites
Install a PDAL environment. Detailed instructions can be found in **"Compiling PDAL with python bindings and .rxp support"** section in [rxp-pipeline README](https://github.com/philwilkes/rxp-pipeline/blob/main/README.md).

### Command:
```bash
mkdir riscan2ply && cd riscan2ply
python riproject2ply.py --riproject /PATH/TO/XXXX.RiSCAN
```

Optional parameters:
- `--tile <size>`: Defines the size of each tile (default: 20), unit in metre.
- `--tile-overlap <size>`: Sets the overlap between tiles (default: 5), unit in metre.
- `--buffer <size>`: Sets the size of buffer around the bounding box (plot boundary) (default: 10), unit in metre.
- `--deviation <value>`: Filters points based on deviation, keeping only those below the specified value (default: 15).
- `--reflectance <min> <max>`: Filters points based on reflectance values within the specified range (e.g., -20 to 5).
- `--rotate-bbox`: Rotates the bounding box to better align with the point cloud's orientation.
- `--verbose`: Enables detailed logging for debugging and progress tracking.
- `--pos <position>`: Specifies a scan position identifier to process a single scan (e.g., `001`).

More available parameters can be found in [riproject2ply.py](https://github.com/wanxinyang/rct-pipeline/blob/main/riproject2ply.py).

## 2. Downsample tiled point clouds

```bash
mkdir downsample && cd downsample
python downsample.py -i '../' --length .02 --verbose
python ply2double.py -i ./ -o ./
```

Parameters:
- `-i <input_path>`: Specifies the input directory containing tiled point clouds.
- `--length <voxel_size>`: Defines the voxel size for downsampling (default: 0.02), unit in metre.
- `--verbose`: Enables detailed logging for debugging and progress tracking.

## 3. Run raycloudtools pipeline in Docker

### Prerequisites
Install rct docker image from Docker Hub
```bash
docker pull docker.io/tdevereux/raycloudtools:latest
```

### Run rayextract pipeline on a single file/tile
Note: need to check the **--grid_width** value in the script and adjust if necessary.

Case 1: for raw point cloud that hasn't been transformed into raycloud
```bash
run_rayextract_on_raycloud.sh <FILENAME>.ply
```

Case 2: for existing raycloud file

```bash
run_rayextract_on_nonraycloud.sh <FILENAME>.ply
```

### Run treesplit and treemesh on a segmented raycloud
```bash
run_treesplit_and_treemesh.sh <FILENAME>.ply
```

### Batch processing script for multiple files/tiles:
This Python script allows to run the above scripts on multiple files/tiles in a batch.
```bash
python batch_run_rct_parallel.py -i <PATTERN>.ply -s <SCRIPT>.sh
```
