#!/bin/bash

# Require a single full-path .ply filename
if [ -z "$1" ]; then
  echo "Usage: $0 /path/to/filename.ply"
  exit 1
fi

INPUT_PATH="$1"
USER_DIR="$(dirname "$INPUT_PATH")"
FILENAME="$(basename "$INPUT_PATH")"
BASENAME="$(basename "$INPUT_PATH" .ply)"

# Run the Docker commands in sequence
# Segment trees and terrain from a raycloud file
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayimport "$FILENAME" ray 0,0,-1 --max_intensity 0
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract terrain "${BASENAME}_raycloud.ply"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trunks "${BASENAME}_raycloud.ply"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trees "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_mesh.ply" --grid_width 50 --height_min 2 --use_rays
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract leaves "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_trees.txt"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools treeinfo "${BASENAME}_raycloud_trees.txt"