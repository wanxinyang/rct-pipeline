#!/bin/bash

# Get user input for directory and filename
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 /path/to/run_rct_full.sh /path/to/ply_dir _raycloud.ply"
  exit 1
fi

USER_DIR=$1
FILENAME=$2
BASENAME=$(basename "$FILENAME" .ply)

# Run the Docker commands in sequence
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract terrain "$FILENAME"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trunks "$FILENAME"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trees "$FILENAME" "${BASENAME}_mesh.ply"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract leaves "$FILENAME" "${BASENAME}_trees.txt"
