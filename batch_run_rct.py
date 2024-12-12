import os
import subprocess
import argparse

def main(input_dir, script_path):
    # Search for all .ply files whose filenames do not contain '_raycloud'
    ply_files = [f for f in os.listdir(input_dir) if f.endswith(".ply") and "_raycloud" not in f]
    if not ply_files:
        print("No .ply files found excluding '_raycloud' in the filename in the specified directory.")
        
    # Search for all .ply files matching 'Tile?.ply' or 'Tile??.ply'
    # ply_files = [f for f in os.listdir(input_dir) if f.startswith("Tile") and f.endswith(".ply") and (len(f) == 8 or len(f) == 9)]
    # if not ply_files:
    #     print("No .ply files found matching the pattern 'Tile?.ply' or 'Tile??.ply' in the specified directory.")
        return

    # Sort the files for better readability, in case order matters
    ply_files.sort()

    # Run the bash script for each .ply file found
    for ply_file in ply_files:
        full_path = os.path.join(input_dir, ply_file)
        print(f"Processing {ply_file}...")
        try:
            subprocess.run([script_path, input_dir, ply_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while processing {ply_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch run the bash script for multiple .ply files.")
    parser.add_argument("-i", "--input", required=True, help="Path to the directory containing the .ply files.")
    parser.add_argument("-s", "--script", required=True, help="Path to the run_rct.sh script.")
    args = parser.parse_args()

    main(args.input, args.script)
