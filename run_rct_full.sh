#!/bin/bash

# Get user input for directory and filename
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 /path/to/run_rct_full.sh /path/to/ply_dir xxxx.ply"
  exit 1
fi

USER_DIR=$1
FILENAME=$2
BASENAME=$(basename "$FILENAME" .ply)

# Run the Docker commands in sequence
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayimport "$FILENAME" ray 0,0,-1 --max_intensity 0
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract terrain "${BASENAME}_raycloud.ply"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trunks "${BASENAME}_raycloud.ply"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trees "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_mesh.ply"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract leaves "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_trees.txt"
