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

# Run the Docker commands in sequence
# Segment trees and terrain from a raycloud file
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract terrain "$FILENAME"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trunks "$FILENAME"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trees "$FILENAME" "${BASENAME}_mesh.ply" --grid_width 50 --height_min 2 --use_rays
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract leaves "$FILENAME" "${BASENAME}_trees.txt"
docker run --rm -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools treeinfo "${BASENAME}_trees.txt"