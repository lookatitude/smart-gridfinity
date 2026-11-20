#!/usr/bin/env bash
# Give rendered pictures the docs site's dark background: the flat background colour is
# replaced, starting from the four corners. Safe to run twice (already dark files are skipped).
#   tools/darken_pictures.sh docs/smart/set.png [more.png ...]
set -euo pipefail
DARK="${DARK:-#131a22}"
for f in "$@"; do
    read -r r g b < <(magick "$f" -alpha off -format '%[fx:int(255*p{2,2}.r)] %[fx:int(255*p{2,2}.g)] %[fx:int(255*p{2,2}.b)]' info:; echo) || true
    if (( r + g + b < 200 )); then echo "skip  $f (already dark)"; continue; fi
    w=$(magick identify -format '%w' "$f"); h=$(magick identify -format '%h' "$f")
    bg="rgb($r,$g,$b)"
    magick "$f" -alpha off -fuzz 3% -fill "$DARK" \
        -floodfill +1+1 "$bg" -floodfill +$((w - 2))+1 "$bg" \
        -floodfill +1+$((h - 2)) "$bg" -floodfill +$((w - 2))+$((h - 2)) "$bg" "$f"
    echo "dark  $f"
done
