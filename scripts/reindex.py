import os
import re
import argparse
import glob

parser = argparse.ArgumentParser(description="Rename .ply files by incrementing the number in their filename")
parser.add_argument('-i', '--input', nargs='+', required=True, help="Path(s) to .ply file(s) to rename. Accepts one or more files.")
parser.add_argument('-odir', '--output_dir', help="Directory to place the renamed file(s)", default='./')
args = parser.parse_args()

output_dir = args.output_dir
file_list = args.input
if not file_list:
    print("Error: No input files provided.")
    exit(1)
single_mode = len(file_list) == 1

def rename_file(src):
    if not os.path.isfile(src):
        print(f"Error: File '{src}' does not exist.")
        exit(1)
    if not src.endswith('.ply'):
        print(f"Error: File '{src}' is not a .ply file.")
        exit(1)
    
    # Handle _tmp files
    if '_tmp.ply' in src:
        m = re.search(r'_(\-?\d+)_tmp\.ply$', src)
        if not m:
            print(f"Error: Filename '{src}' does not contain a number matching the pattern '_<number>_tmp.ply'.")
            exit(1)
        num = int(m.group(1))
        new_num = num + 1
        new_name = os.path.basename(src).replace(f'_{num}_tmp.ply', f'_{new_num}.ply')
    else:
        m = re.search(r'_(\-?\d+)\.ply$', src)
        if not m:
            print(f"Error: Filename '{src}' does not contain a number matching the pattern '_<number>.ply'.")
            exit(1)
        num = int(m.group(1))
        new_num = num + 1
        new_name = os.path.basename(src).replace(f'_{num}.ply', f'_{new_num}.ply')
    
    dest_dir = output_dir if output_dir else os.path.dirname(src)
    if output_dir and not os.path.exists(output_dir):
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return False
    dest = os.path.join(dest_dir, new_name)
    if os.path.exists(dest):
        print(f"Error: Cannot rename '{src}' because '{dest}' already exists. Skipping.")
        return False
    os.rename(src, dest)
    print(f"Renamed {src} to {dest}")
    return True

if not single_mode:
    # First pass: temporary rename
    tmp_files = []
    for f in file_list:
        m = re.search(r'_(\-?\d+)\.ply$', f)
        if m:
            num = m.group(1)
            tmp = f.replace(f'_{num}.ply', f'_{num}_tmp.ply')
            os.rename(f, tmp)
            tmp_files.append(tmp)
    # Second pass: final rename
    for f in tmp_files:
        rename_file(f)
else:
    rename_file(file_list[0])