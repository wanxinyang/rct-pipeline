#!/bin/bash

# Require a single full-path raycloud filename
if [ -z "$1" ]; then
  echo "Usage: $0 /PATH/TO/raycloud.ply"
  exit 1
fi

INPUT_PATH="$(realpath "$1")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_DIR="$(dirname "$INPUT_PATH")"
FILENAME="$(basename "$INPUT_PATH")"
BASENAME="$(basename "$INPUT_PATH" .ply)"

## Run the Docker commands in sequence
mkdir -p "${USER_DIR}/${BASENAME}_treesplit"
cp "${USER_DIR}/${BASENAME}_trees.txt" "${USER_DIR}/${BASENAME}_treesplit/"

# extract individual point clouds and tree attributes
docker run --rm --name "${BASENAME}_$$" \
  -v "${USER_DIR}":/workspace \
  -v "${USER_DIR}/${BASENAME}_treesplit":/workspace_treesplit \
  docker.io/tdevereux/raycloudtools \
  bash -c "raysplit \"${BASENAME}_segmented.ply\" seg_colour && treesplit \"/workspace_treesplit/${BASENAME}_trees.txt\" per-tree"

# Reindex segmented files to align with treefiles treeid.
# raysplit outputs 0-based IDs (_segmented_0.ply, _segmented_1.ply, ...)
# treesplit outputs 1-based IDs (_trees_1_info.txt, _trees_2_info.txt, ...)
# so reindex.py adds +1 to each segmented filename.
seg_files=("${USER_DIR}/${BASENAME}_segmented_"[0-9]*.ply)
if [ -e "${seg_files[0]}" ]; then
  python "${SCRIPT_DIR}/reindex.py" -i "${seg_files[@]}" -odir "${USER_DIR}/${BASENAME}_treesplit"
else
  echo "No segmented ply files found for ${BASENAME}"
fi

# Move the background segment (-1) into treesplit alongside the tree files.
# It has no matching _trees_N_info.txt but is kept for reference.
bg_file="${USER_DIR}/${BASENAME}_segmented_-1.ply"
if [ -f "${bg_file}" ]; then
  mv "${bg_file}" "${USER_DIR}/${BASENAME}_treesplit/"
fi

# Remove the copied trees.txt file from the split subdirectory to save space
rm "${USER_DIR}/${BASENAME}_treesplit/${BASENAME}_trees.txt"

# Process all tree files in one container
docker run --rm --name "${BASENAME}_$$" \
  -v "${USER_DIR}/${BASENAME}_treesplit":/workspace \
  -w /workspace \
  docker.io/tdevereux/raycloudtools \
  bash -c '\
for f in ./*.txt; do
  treemesh "$f"
  segply="${f/_trees_/_segmented_}"
  rayextract leaves "$segply" "$f"
  treeinfo "$f" --branch_data
done'