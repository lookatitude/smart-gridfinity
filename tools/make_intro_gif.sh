#!/usr/bin/env bash
# Build docs/intro.gif from assembly_intro.scad: render each distinct frame with OpenSCAD,
# write a caption under it, and join the frames. Needs OpenSCAD and ImageMagick.
# Takes about 25 minutes: OpenSCAD needs about 30 s per frame, and frames are rendered one
# at a time.   tools/make_intro_gif.sh [work dir]
set -euo pipefail
cd "$(dirname "$0")/.."
WORK="${1:-$(mktemp -d)}"; mkdir -p "$WORK"
CAMERA="-42,0,22,48,0,24,540"       # angles must match CAM in assembly_intro.scad
FONT="${FONT:-Liberation-Sans-Bold}"

caption() {   # caption for frame $1
    local f=$1
    if   (( f < 3 ));  then echo "1. Start with a starter tile"
    elif (( f < 15 )); then echo "2. Add tiles: they snap together and find each other"
    elif (( f < 21 )); then echo "3. The power bin brings in power and keeps the map"
    elif (( f < 41 )); then echo "4. Drop bins in anywhere, any way round"
    elif (( f < 46 )); then echo "5. The base reads each bin's ID and where it stands"
    else                    echo "6. Ask for an item: its compartment lights up"
    fi
}

frame() {   # render frame $1 once, with its caption
    local f=$1 raw="$WORK/raw_$1.png" out="$WORK/frame_$1.png"
    [[ -s "$out" ]] && return
    [[ -s "$raw" ]] || openscad -o "$raw" -D f="$f" --imgsize=960,540 --colorscheme=Tomorrow --projection=p \
        --camera="$CAMERA" assembly_intro.scad 2>&1 | grep -E 'WARNING|ERROR' || true
    # the render's flat light background becomes the docs site's dark surface
    magick "$raw" -alpha off -fuzz 3% -fill '#131a22' -floodfill +1+1 '#f8f8f8' -floodfill +958+1 '#f8f8f8' \
        -floodfill +1+538 '#f8f8f8' -floodfill +958+538 '#f8f8f8' \
        -resize 800x450 -gravity south -background '#0c1117' -splice 0x44 \
        -font "$FONT" -pointsize 21 -fill white -annotate +0+11 "$(caption "$f")" "$out"
}

# "frame:hundredths of a second it stays". A frame listed twice is rendered once.
PLAN="0:130
3:8 4:8 5:8 6:8 7:8 8:70
9:8 10:8 11:8 12:8 13:8 14:90
15:8 16:8 17:8 18:8 19:8 20:100
21:8 22:8 23:8 24:8 25:45
26:8 27:8 28:8 29:8 30:45
31:8 32:8 33:8 34:8 35:45
36:8 37:8 38:8 39:8 40:100
41:50 42:50 43:50 44:200
46:55 47:25 46:160
50:55 47:25 50:160
54:280"

args=()
for step in $PLAN; do
    f=${step%%:*}; d=${step##*:}
    echo "frame $f"
    frame "$f"
    args+=(-delay "$d" "$WORK/frame_$f.png")
done
magick "${args[@]}" -loop 0 -colors 128 -layers Optimize docs/intro.gif
ls -la docs/intro.gif
