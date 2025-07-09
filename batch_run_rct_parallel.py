import os
import subprocess
import argparse
from multiprocessing import Pool, cpu_count
import glob

SCRIPT_PATH = None

def process_file(file_path):
    print(f"Processing {file_path}...")
    try:
        subprocess.run([SCRIPT_PATH, file_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while processing {file_path}: {e}")

def main(patterns, script_path):
    # Expand input patterns to absolute file paths
    file_paths = []
    for pat in patterns:
        file_paths.extend(glob.glob(pat))
    if not file_paths:
        print("No matching .ply files found.")
        return
    # get aboslute paths
    file_paths = [os.path.abspath(fp) for fp in file_paths if os.path.isfile(fp)]
    file_paths.sort()

    global SCRIPT_PATH
    SCRIPT_PATH = script_path

    # Use multiprocessing to process files in parallel
    num_cores = cpu_count()
    with Pool(num_cores) as pool:
        pool.map(process_file, file_paths)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch run the bash script for multiple .ply files.")
    parser.add_argument("-i", "--input", nargs="+", 
                        help="Single or multiple input filename(s)")
    parser.add_argument("-s", "--script_path", required=True, 
                        help="Path to the rct script, can be 'rayextract_on_raycloud.sh', 'rayextract_on_nonraycloud.sh', or 'treesplit_and_treemesh.sh'")
    args = parser.parse_args()

    main(args.input, args.script_path)
