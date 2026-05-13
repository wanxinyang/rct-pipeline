import os
import subprocess
import argparse
from multiprocessing import cpu_count
import glob
from threading import Thread
from queue import Queue

SCRIPT_PATH = None

def process_file_worker(queue):
    while not queue.empty():
        file_path = queue.get()
        print(f"Processing {file_path}...")
        try:
            subprocess.run([SCRIPT_PATH, file_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while processing {file_path}: {e}")
        queue.task_done()

def main(patterns, script_path):
    # Expand input patterns to absolute file paths
    file_paths = []
    for pat in patterns:
        file_paths.extend(glob.glob(pat))
    if not file_paths:
        print("No matching .ply files found.")
        return
    # get absolute paths
    file_paths = [os.path.abspath(fp) for fp in file_paths if os.path.isfile(fp)]
    file_paths.sort()

    global SCRIPT_PATH
    SCRIPT_PATH = script_path

    # Use threading to process files in parallel
    num_threads = min(cpu_count(), 4)
    queue = Queue()
    for file_path in file_paths:
        queue.put(file_path)

    threads = []
    for _ in range(num_threads):
        t = Thread(target=process_file_worker, args=(queue,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch run the bash script for multiple .ply files.")
    parser.add_argument("-i", "--input", nargs="+", 
                        help="Single or multiple input filename(s)")
    parser.add_argument("-s", "--script_path", required=True, 
                        help="Path to the rct script, can be 'rayextract_on_raycloud.sh', 'rayextract_on_nonraycloud.sh', or 'treesplit_and_treemesh.sh'")
    args = parser.parse_args()

    main(args.input, args.script_path)
