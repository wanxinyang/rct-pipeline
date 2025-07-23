#!/bin/bash

# Require a single full-path raycloud filename
if [ -z "$1" ]; then
  echo "Usage: $0 /PATH/TO/raycloud.ply"
  exit 1
fi

# Get absolute path to avoid issues with relative paths
INPUT_PATH="$(realpath "$1")"
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
  -e FILENAME="$FILENAME" \
  -e BASENAME="$BASENAME" \
  -v "$USER_DIR":/workspace \
  -w /workspace \
  docker.io/tdevereux/raycloudtools \
  bash -c '

echo -e "\n=== Terrain extraction - " $(date) >> "$LOGFILE"
echo "Command: rayextract terrain \"$FILENAME\"" >> "$LOGFILE"
rayextract terrain "$FILENAME" 2>&1 \
  | tr "\r" "\n" \
  | grep -v -e "read and process" -e "rays processed" -e "^[[:space:]]*$" \
  >> "$LOGFILE"

echo -e "\n=== Trunks extraction - " $(date) >> "$LOGFILE"
echo "Command: rayextract trunks \"$FILENAME\"" >> "$LOGFILE"
rayextract trunks "$FILENAME" 2>&1 \
  | tr "\r" "\n" \
  | grep -v -e "read and process" -e "^[[:space:]]*$" \
  >> "$LOGFILE"

echo -e "\n=== Trees extraction - " $(date) >> "$LOGFILE"
echo "Command: rayextract trees \"$FILENAME\" \"${BASENAME}_mesh.ply\" --grid_width 50 --height_min 2 --use_rays" >> "$LOGFILE"
rayextract trees "$FILENAME" "${BASENAME}_mesh.ply" --grid_width 50 --height_min 2 --use_rays 2>&1 \
  | tr "\r" "\n" \
  | grep -v -e "read and process" -e "^[[:space:]]*$" \
  >> "$LOGFILE"

echo -e "\n=== Leaves extraction - " $(date) >> "$LOGFILE"
echo "Command: rayextract leaves \"$FILENAME\" \"${BASENAME}_trees.txt\"" >> "$LOGFILE"
rayextract leaves "$FILENAME" "${BASENAME}_trees.txt" 2>&1 \
  | tr "\r" "\n" \
  | grep -v -e "read and process" -e "^[[:space:]]*$" \
  >> "$LOGFILE"

echo -e "\n=== Treeinfo extraction - " $(date) >> "$LOGFILE"
echo "Command: treeinfo \"${BASENAME}_trees.txt\" --branch_data" >> "$LOGFILE"
treeinfo "${BASENAME}_trees.txt" --branch_data >> "$LOGFILE" 2>&1
' 2>> "$LOGFILE"


# # Run commands in individual containers (if needed)
# # Segment trees and terrain from a raycloud file
# # docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract terrain "$FILENAME"
# # docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trunks "$FILENAME"
# echo "=== Trees extraction - $(date) ===" >> "$LOGFILE"
# /usr/bin/time -v docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract trees "$FILENAME" "${BASENAME}_mesh.ply" --grid_width 50 --height_min 2 --use_rays 2>> "$LOGFILE"
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools rayextract leaves "$FILENAME" "${BASENAME}_trees.txt" 2>> "$LOGFILE"
# docker run --rm --name "${BASENAME}_$$" -v "$USER_DIR":/workspace docker.io/tdevereux/raycloudtools treeinfo "${BASENAME}_trees.txt" --branch_data
