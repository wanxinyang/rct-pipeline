#!/bin/bash

# Require a single full-path raycloud filename
if [ -z "$1" ]; then
  echo "Usage: $0 /PATH/TO/raycloud.ply"
  exit 1
fi

INPUT_PATH="$1"
USER_DIR="$(dirname "$INPUT_PATH")"
FILENAME="$(basename "$INPUT_PATH")"
BASENAME="$(basename "$INPUT_PATH" .ply)"

## Run the Docker commands in sequence
# Split trees into individual files
mkdir -p "${USER_DIR}/${BASENAME}_treesplit"
cp "${USER_DIR}/${BASENAME}_trees.txt" "${USER_DIR}/${BASENAME}_treesplit/"
docker run --rm -v "${USER_DIR}/${BASENAME}_treesplit":/workspace docker.io/tdevereux/raycloudtools treesplit "${BASENAME}_trees.txt" per-tree
rm "${USER_DIR}/${BASENAME}_treesplit/${BASENAME}_trees.txt"

# Generate tree attr summary and mesh model for individual trees
# Process each tree file in parallel (limit to $JOBS concurrent jobs) using xargs
JOBS=${JOBS:-$(nproc || echo 4)}
find "${USER_DIR}/${BASENAME}_treesplit" -name '*.txt' | \
xargs -n1 -P "${JOBS}" -I {} bash -c '
  base="$(basename "{}" .txt)"
  docker run --rm -v "'"${USER_DIR}/${BASENAME}_treesplit"':/workspace" docker.io/tdevereux/raycloudtools treeinfo "${base}.txt"
  docker run --rm -v "'"${USER_DIR}/${BASENAME}_treesplit"':/workspace" docker.io/tdevereux/raycloudtools treemesh "${base}.txt"
'
