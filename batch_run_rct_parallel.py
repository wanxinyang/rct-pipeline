import os
import subprocess
import argparse
from multiprocessing import Pool, cpu_count

def process_file(args):
    script_path, input_dir, ply_file = args
    full_path = os.path.join(input_dir, ply_file)
    print(f"Processing {ply_file}...")
    try:
        subprocess.run([script_path, input_dir, ply_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while processing {ply_file}: {e}")

def main(input_dir, script_path):
    # Search for all .ply files whose filenames do not contain '_raycloud'
    ply_files = [f for f in os.listdir(input_dir) if f.endswith(".ply") and "_raycloud" not in f]

    if not ply_files:
        print("No .ply files found excluding '_raycloud' in the filename in the specified directory.")
        return

    # Sort the files for better readability, in case order matters
    ply_files.sort()

    # Prepare arguments for multiprocessing
    args_list = [(script_path, input_dir, ply_file) for ply_file in ply_files]

    # Use multiprocessing to process files in parallel
    num_cores = cpu_count()
    with Pool(num_cores) as pool:
        pool.map(process_file, args_list)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch run the bash script for multiple .ply files.")
    parser.add_argument("-i", "--input", required=True, help="Path to the directory containing the .ply files.")
    parser.add_argument("-s", "--script", required=True, help="Path to the run_rct.sh script.")
    args = parser.parse_args()

    main(args.input, args.script)
