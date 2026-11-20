#!/usr/bin/env bash
# Run every fit check in tests/fit.scad. A check passes when the two parts share no volume
# (under 0.05 mm3, which allows for faces that only touch).
# bin_on_bin is a known exception: the sprung latch of the upper bin is pressed in by the
# lip of the lower bin, so a small overlap of the undeflected model is expected there.
cd "$(dirname "$0")"
tmp=$(mktemp -d); fail=0
for t in foot_in_socket foot_rotated bin_2x1_on_tile bin_across_tiles floor_in_bin floor_passes_lip \
         floor_in_label_bin floor_passes_label_tab bin_on_label_bin sleeve_in_bin bin_on_bin lid_in_power_bin board_in_power_bin power_bin_seated power_bin_half_turn \
         power_bin_quarter_turn_blocked power_bin_on_normal_cell_blocked normal_bin_on_power_cell \
         tiles_side_by_side key_in_tiles \
         $(for c in 2x2 4x4 4x3 3x3 2x3 2x2_starter 2x3_starter 4x3_starter; do echo fittings_in_$c fittings_vs_ports_$c main_vs_rest_$c strips_vs_rest_$c; done) \
         strip_shifted_blocked fittings_under_bin bin_board_in_foot tile_4x4_and_bin drawer_closed drawer_open drawer_floor_in_shell drawer_unit_on_tile \
         bin_on_drawer_unit control_overlap; do
    out=$(openscad -o "$tmp/$t.stl" -D "test=\"$t\"" fit.scad 2>&1)
    if grep -q "ERROR" <<<"$out" && ! grep -q "top level object is empty" <<<"$out"; then
        echo "ERROR  $t: $(grep ERROR <<<"$out" | head -1)"; fail=1; continue
    fi
    vol=0; [[ -s "$tmp/$t.stl" ]] && vol=$(python3 -c "import stlvol,sys; print('%.2f' % stlvol.measure(sys.argv[1])[0])" "$tmp/$t.stl")
    case $t in
        control_overlap|*_blocked) ok=$(python3 -c "print(int($vol > 1))"); note="must overlap" ;;
        bin_on_bin|bin_on_drawer_unit|bin_on_label_bin) ok=$(python3 -c "print(int($vol < 3))"); note="sprung latch pressed in" ;;
        *)               ok=$(python3 -c "print(int($vol < 0.05))"); note="" ;;
    esac
    if [[ $ok == 1 ]]; then echo "pass   $t  overlap $vol mm3  $note"; else echo "FAIL   $t  overlap $vol mm3"; fail=1; fi
done
rm -rf "$tmp"; exit $fail
