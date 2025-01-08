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

### Optional parameters:
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

### Commands:
```bash
mkdir downsample && cd downsample
python downsample.py -i '../' --length .02 --verbose
python ply2double.py -i ./ -o ./
```

### Parameters:
- `-i <input_path>`: Specifies the input directory containing tiled point clouds.
- `--length <voxel_size>`: Defines the voxel size for downsampling (default: 0.02), unit in metre.
- `--verbose`: Enables detailed logging for debugging and progress tracking.

## 3. Run raycloudtools (rct) in Docker

### Prerequisites
Install rct docker image from Docker Hub
```bash
docker pull docker.io/tdevereux/raycloudtools:latest
```

### For individual files/tiles:
Run the following command to process a single file or tile. Replace `<ABSOLUTE_PATH>` with the absolute path to your directory and `<FILENAME>` with the name of the `.ply` file you want to process.
```bash
run_rct_full.sh /<ABSOLUTE_PATH>/downsample/ <FILENAME>.ply
```
Example:
```bash
run_rct_full.sh /home/user/riscan2ply/downsample/ 0000.downsample.ply
```

### For multiple files/tiles:
Run the batch processing script. Replace `<ABSOLUTE_PATH>` with the absolute path to your directory.
```bash
python batch_run_rct_parallel.py -i /<ABSOLUTE_PATH>/downsample/ -s /<ABSOLUTE_PATH>/run_rct_full.sh
```
Example:
```bash
python batch_run_rct_parallel.py -i /home/user/riscan2ply/downsample/ -s /home/user/rct_pipeline/run_rct_full.sh
```

### Parameters:
- `-i <input_path>`: Specifies the directory containing downsampled files.
- `-s <script_path>`: Provides the path to the `run_rct_full.sh` script.
