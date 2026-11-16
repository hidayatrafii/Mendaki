#!/usr/bin/env bash
# Rebuilds the working media from the original edit.
# Usage: tools/prepare-media.sh "/path/to/C3 Nov 2026 Summary Video.mp4"
set -euo pipefail
SRC="$1"
cd "$(dirname "$0")/.."
# 1080p working copy with a keyframe every second (smooth seeking in preview/render)
ffmpeg -y -i "$SRC" -vf scale=1920:1080 -c:v libx264 -crf 20 -preset medium -g 30 \
  -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart assets/footage.mp4
# Presenter keyed off the black stretches (60.2-92.0 s and 99.1-101.6 s), with the
# matte closed so his pupils and hair shadows stay solid.
D=$(printf 'dilation,%.0s' {1..6}); E=$(printf 'erosion,%.0s' {1..6})
for seg in "a 60.2 31.8" "b 99.1 2.5"; do
  set -- $seg
  ffmpeg -y -ss "$2" -t "$3" -i "$SRC" -an -filter_complex \
    "[0]scale=1920:1080,split[c][k];[k]colorkey=0x000000:0.06:0.04,format=rgba,alphaextract,${D}${E}null[a];[c][a]alphamerge,format=yuva420p" \
    -c:v libvpx-vp9 -b:v 4M -g 30 -deadline good -cpu-used 4 -row-mt 1 "assets/presenter-$1.webm"
done
