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

# Debug output to verify paths
echo "INPUT_PATH = $INPUT_PATH"
echo "USER_DIR = $USER_DIR"
echo "FILENAME = $FILENAME"
echo "BASENAME = $BASENAME"

LOGFILE="${USER_DIR}/${BASENAME}.log"
# Ensure log file exists
# mkdir -p "$(dirname "$LOGFILE")"
# touch "$LOGFILE"
echo "Docker resource usage log - $(date)" > "$LOGFILE"


# Run all rayextract commands inside one container
echo "**** Segment trees from '$FILENAME' ****" >> "$LOGFILE"

/usr/bin/time -v docker run --rm --name "${BASENAME}_$$" \
  -e LOGFILE="/workspace/${BASENAME}.log" \
  -v "$USER_DIR":/workspace \
  -w /workspace \
  docker.io/tdevereux/raycloudtools \
  bash -c '
echo -e "\n=== Ray import - $(date)" >> "$LOGFILE"
echo "Command: rayimport \"$FILENAME\" ray 0,0,-1 --max_intensity 0" >> "$LOGFILE"
rayimport "$FILENAME" ray 0,0,-1 --max_intensity 0 2>&1 \
  | grep -v -e "^read and process" -e "^rays processed" -e "^[[:space:]]*$" >> "$LOGFILE"

echo -e "\n=== Terrain extraction - $(date)" >> "$LOGFILE"
echo "Command: rayextract terrain \"${BASENAME}_raycloud.ply\"" >> "$LOGFILE"
rayextract terrain "${BASENAME}_raycloud.ply" 2>&1 \
  | grep -v -e "^read and process" -e "^rays processed" -e "^[[:space:]]*$" >> "$LOGFILE"

echo -e "\n=== Trunks extraction - $(date)" >> "$LOGFILE"
echo "Command: rayextract trunks \"${BASENAME}_raycloud.ply\"" >> "$LOGFILE"
rayextract trunks "${BASENAME}_raycloud.ply" 2>&1 \
  | grep -v -e "^read and process" -e "^rays processed" -e "^[[:space:]]*$" >> "$LOGFILE"

echo -e "\n=== Trees extraction - $(date)" >> "$LOGFILE"
echo "Command: rayextract trees \"${BASENAME}_raycloud.ply\" \"${BASENAME}_raycloud_mesh.ply\" --grid_width 50 --height_min 2 --use_rays" >> "$LOGFILE"
rayextract trees "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_mesh.ply" --grid_width 50 --height_min 2 --use_rays 2>&1 \
  | grep -v -e "^read and process" -e "^rays processed" -e "^[[:space:]]*$" >> "$LOGFILE"

echo -e "\n=== Leaves extraction - $(date)" >> "$LOGFILE"
echo "Command: rayextract leaves \"${BASENAME}_raycloud.ply\" \"${BASENAME}_raycloud_trees.txt\"" >> "$LOGFILE"
rayextract leaves "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_trees.txt" 2>&1 \
  | grep -v -e "^read and process" -e "^rays processed" -e "^[[:space:]]*$" >> "$LOGFILE"

echo -e "\n=== Tree info extraction - $(date)" >> "$LOGFILE"
echo "Command: treeinfo \"${BASENAME}_raycloud_trees.txt\" --branch_data" >> "$LOGFILE"
treeinfo "${BASENAME}_raycloud_trees.txt" --branch_data >> "$LOGFILE" 2>&1
' 2>> "$LOGFILE"


# # Run commands in individual containers (if needed)
# # Segment trees and terrain from a raycloud file
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayimport "$FILENAME" ray 0,0,-1 --max_intensity 0
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract terrain "${BASENAME}_raycloud.ply"
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trunks "${BASENAME}_raycloud.ply"
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trees "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_mesh.ply" --grid_width 50 --height_min 2 --use_rays
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract leaves "${BASENAME}_raycloud.ply" "${BASENAME}_raycloud_trees.txt"
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools treeinfo "${BASENAME}_raycloud_trees.txt" --branch_data