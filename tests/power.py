#!/usr/bin/env python3
"""Power budget. The grid is fed at 12-24 V through the power cell of a starter tile; every
tile steps that down to 5 V on the board of its first row, for itself and its own sockets. Only the tile boards and
the hub in the power bin have radios; bins are passive apart from their LEDs.
Currents and efficiency are assumptions to be replaced by measurements. How far one feed
reaches is worked out in pcb/grid_limits.py and pcb/grid_power.py."""

BOARD_5V = 0.087       # A at 5 V, tile board or hub with its radio receiving, switches included
LED_SHOWN = 0.020      # A at 5 V, one LED at a single colour, medium brightness
LED_IDLE = 0.0008      # A at 5 V, one addressable LED switched off
LED_FULL = 0.060       # A at 5 V, one LED full white
EFFICIENCY = 0.88      # step-down converter
PIN_LIMIT = 2.0        # A, one spring pin, and one pin of an edge connector
FEED_PINS = 2          # pins per pole in the power cell
CONVERTER_LIMIT = 2.0  # A at 5 V, per tile board
CABLE_LIMIT = 2 * 0.5 * 0.7  # A at 5 V through the flat cable to the second row: two contacts of 0.5 A,
                             # at the 70 % the socket maker asks for when every contact carries current

def watts(tiles, leds, lit, full=False):
    led = leds * LED_FULL if full else (leds - lit) * LED_IDLE + lit * LED_SHOWN
    return 5 * ((tiles + 1) * BOARD_5V + led) / EFFICIENCY

def budget(name, tiles, leds, lit, most_leds_on_one_tile):
    ok = True
    for volts in (12, 24):
        p = watts(tiles, leds, lit)
        i = p / volts
        fine = i <= PIN_LIMIT
        ok &= fine
        print("%-42s %2d V feed: %4.1f W, %4.2f A in the feed (pins allow %.0f A, one connector pin %.0f A)  %s"
              % (name if volts == 12 else "", volts, p, i, FEED_PINS * PIN_LIMIT, PIN_LIMIT, "OK" if fine else "TOO MUCH"))
    worst = BOARD_5V + most_leds_on_one_tile * LED_FULL
    print("%-42s busiest tile, every LED on it full white: %.2f A at 5 V (converter allows %.1f A)  %s"
          % ("", worst, CONVERTER_LIMIT, "OK" if worst <= CONVERTER_LIMIT else "firmware must cap"))
    behind = most_leds_on_one_tile * LED_FULL    # worst case: all of them in rows two to four
    shown = most_leds_on_one_tile * LED_SHOWN    # every one lit the way an item is shown
    fine = shown <= CABLE_LIMIT
    ok &= fine
    print("%-42s flat cable to the further rows: %.2f A with every LED lit as shown, %.2f A full white (cable allows %.2f A)  %s"
          % ("", shown, behind, CABLE_LIMIT, "TOO MUCH" if not fine else "OK" if behind <= CABLE_LIMIT else "OK as shown; firmware must cap full white at %d LEDs" % int(CABLE_LIMIT / LED_FULL)))
    print("%-42s every LED in the grid full white: %.0f W" % ("", watts(tiles, leds, lit, full=True)))
    return ok

ok = [budget("Test set: 2 tiles, 4 LEDs, 2 lit", 2, 4, 2, 3),
      budget("Full collection: 8 tiles, 58 LEDs, 6 lit", 8, 58, 6, 16),
      budget("Drawer row: 4 tiles, 18 LEDs, 3 lit", 4, 18, 3, 6)]
assert all(ok)
print("PASS")
