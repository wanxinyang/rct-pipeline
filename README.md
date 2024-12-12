# Usage:

## 1. Convert RIEGL RiSCAN Project Outputs to Tiled PLY-Format Point Clouds

### Command:
```bash
python riproject2ply.py --riproject /PATH/TO/XXXX.RiSCAN
```

### Optional Parameters:
- `--tile <size>`: Defines the size of each tile (default: 20).
- `--tile-overlap <size>`: Sets the overlap between tiles (default: 5).
- `--deviation <value>`: Filters points based on deviation, keeping only those below the specified value (default: 15).
- `--reflectance <min> <max>`: Filters points based on reflectance values within the specified range (e.g., -20 to 5).
- `--rotate-bbox`: Rotates the bounding box to better align with the point cloud's orientation.
- `--verbose`: Enables detailed logging for debugging and progress tracking.
- `--pos <position>`: Specifies a scan position identifier to process a single scan (e.g., `001`).

## 2. Downsample Tiled Point Clouds

### Commands:
```bash
mkdir downsample && cd downsample
python downsample.py -i '../' --length .02 --verbose
```

### Parameters:
- `-i <input_path>`: Specifies the input directory containing tiled point clouds.
- `--length <voxel_size>`: Defines the voxel size for downsampling (default: 0.02).
- `--verbose`: Enables detailed logging for debugging and progress tracking.

## 3. Run RayCloudTools (RCT) in Docker

### For Individual Files/Tiles:
Run the following command to process a single file or tile:
```bash
run_rct_full.sh downsample/ xxxx.ply
```

### For Multiple Files/Tiles:
Run the batch processing script with absolute paths:
```bash
python batch_run_rct_parallal.py -i downsample/ -s /PATH/TO/run_rct_full.sh
```

### Parameters:
- `-i <input_path>`: Specifies the directory containing downsampled files.
- `-s <script_path>`: Provides the path to the `run_rct_full.sh` script.
