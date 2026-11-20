// Dimensions for the powered ("smart") base tile and bins.
// Electronics: a passive ring board in each bin foot, one board per tile (see pcb/).
// Concept values: sizes marked BUY must be set to the parts actually purchased.
include <constants.scad>

// Base tile, below the socket floor
FLOOR_T   = 3.2;    // socket floor: magnet pocket (2.4) plus 0.8 under it
CAVITY_H  = 6.5;    // wiring cavity under the floor, open at the back: the edge connector (5.5) is the tallest part
SKIRT_T   = 2.4;    // outer wall of the cavity
RIB_T     = 2.4;    // stiffening ribs under the cell corners
RIB_LEN   = 8;      // each way from the corner; the gap between ribs passes the row boards
UNDER_H   = FLOOR_T + CAVITY_H;

// Contacts: four spring pins per socket, in a row along +X from the cell centre.
// The bin foot carries a round board with four concentric rings (pcb/bin_board), so the
// bin works in any quarter turn.
PIN_R       = [0, 5.4, 9.2, 12.9];   // ID, LED data, 5 V, ground
RINGS       = [[0, 2.6], [4.4, 6.4], [8.2, 10.2], [12.0, 13.8]];   // inner, outer radius of each ring
PIN_HOLE_D  = 2.2;  // BUY: spring-loaded contact with solder tail, 2.0 mm barrel (Mill-Max 0906 class)

// Row boards (pcb/row_main, pcb/row_strip): one board under every row of cells. It carries
// that row's spring pins, soldered by the board maker, so nothing is soldered inside the
// tile. The board of the first row also carries the tile's electronics; every further row
// has a plain strip with one switch chip. A 30 mm flat cable links each row to the next.
// Boards are made four cells long and snapped shorter. Each lies against a boss under every
// cell and is held by one M2 screw per cell; the pins themselves locate it.
PIN_ABOVE_BOARD = 5.5;   // BUY: free height of the pin above its board
PIN_PROUD       = 1.0;   // pin tip above the socket floor, bin not seated
CELL_BOARD_X    = [-7.5, 15.0];    // boss under each cell, along the pin row, from the cell centre
CELL_BOARD_W    = 6.0;             // width of the strip
CELL_BOARD_T    = 1.6;
CELL_BOARD_Z    = PIN_PROUD - PIN_ABOVE_BOARD;   // z of the board face that touches the boss
CELL_SCREW_X    = -3.6;
CELL_PILOT_D    = 1.7;   // BUY: M2 x 6 self-tapping screw
MAX_TILE_SIDE   = 4;     // a row board is four cells long, and the cable chain reaches four rows
STRIP_X0        = -7.5;  // start of a row board, from the centre of its first cell
STRIP_END       = 15.5;  // end of a row board (and its snap lines), from the centre of a cell
TAB_X           = [-7.5, 15.0];   // wider part at the first cell: the cable sockets and the switch chip
TAB_Y           = 10.25;          // half width there; the socket mouths sit at this edge
LINK_X          = 8;              // centre line of the cable sockets and the flat cable
LINK_SOCKET     = [10.1, 5.6, 2.1];  // BUY: 12-way 0.5 mm flat-cable socket, lying, bottom contact
LINK_CABLE_W    = 6.5;            // BUY: 12-way 0.5 mm flat cable, 30 mm long, contacts on the same side
// Board of the first row, corners from the centre of the tile's first cell. The wide part
// (x up to 54) holds the electronics on the face that looks down; the strip beyond it is
// snapped off for narrower tiles. Its tallest part is the radio module (3.2 mm).
MAIN_OUTLINE = [[-12, -7], [54, -7], [54, -3], [141.5, -3], [141.5, 3], [54, 3], [54, 37.5],
                [34.5, 37.5], [34.5, 23], [17, 23], [17, TAB_Y], [-12, TAB_Y]];
MAIN_BODY_X  = 54;
MAIN_PARTS_H = 3.4;
MAIN_SCREW   = [48, 33];  // third screw, at the far corner of the wide part

// Wall-mount screw: one magnet pocket per cell (front left) has a through hole under it.
// For wall mounting, a pan-head M3 screw goes there in place of the magnet. That keeps
// the screw head away from the contact rings.
SCREW_POS    = [-MAGNET_OFFSET, -MAGNET_OFFSET];
SCREW_D      = 3.4;
SCREW_POST_D = 9;

// Snap ring: groove in every socket wall, sprung latch on the bin foot
GROOVE_Z     = 1.65;  // centre height above the socket floor
GROOVE_H     = 1.3;    // wide enough that the sloped flanks of the latch bump clear it
GROOVE_DEPTH = 0.55;
LATCH_LEN    = 16;
LATCH_T      = 1.2;
LATCH_GAP    = 1.0;
LATCH_BUMP   = 0.75;

// Tile-to-tile port, at the middle of every outer cell edge.
// Plug halves go on the right (+X) and back (+Y) edges, socket halves on the left and front,
// so tiles only join one way round and 5 V always meets 5 V.
PORT_W = 15.4; // BUY: 3-pin magnetic connector, 2.54 mm pitch, body about 15 x 4 x 5.5 mm
PORT_H = 6;

// Optional tile-to-tile lock: a dovetail pocket beside every port, open at the underside.
// Tiles join by pushing them together until the magnetic connectors snap. For a permanent
// or wall-mounted grid, a printed bow-tie key pressed into two facing pockets locks them.
KEY_OFFSET = -14;   // along the edge, from the cell centre
KEY_ROOT   = 5;     // width at the tile edge
KEY_TIP    = 8;     // width at the inner end
KEY_DEPTH  = 4.5;
KEY_H      = 8;
KEY_FIT    = 0.15;
KEY_WALL   = 2.4;   // material left round a pocket

// Largest tile: 4 x 4 cells
MAX_TILE_CELLS = 16;

// Bin board (custom, pcb/bin_board): a round board glued into the foot, rings down,
// standing 0.1 mm proud. Its few parts sit in a pocket above it.
BIN_BOARD_D   = 28.6;   // as laid out: 0.5 mm of bare edge outside the ground ring
BIN_BOARD_T   = 1.6;
BIN_BOARD_FIT = 0.2;
PAD_PROUD     = 0.1;
PARTS_POCKET_D   = 24;  // ID chip, diode, solder pads for the LED chain
PARTS_POCKET_TOP = 6.0;
PAD_NOTCH_R      = 14.2; // the three LED solder pads sit up to 13.7 mm from the centre
PAD_NOTCH_ANGLE  = 90;   // the pocket is widened over this arc; turn the board so its pads face it
CABLE_HOLE_D     = 11.5; // wide enough for an LED board, so a finished LED chain can be fed up through it

// False floors. The space under them holds only the LEDs and their cable.
BAY_TOP   = 10.4;      // underside of the false floors: bin floor 7.0 + LED board 3.0 + 0.4
FALSE_FLOOR_T   = 1.2;
FALSE_FLOOR_FIT = 0.2;

// Optional label tab at the back of every compartment: takes 9 mm label tape and doubles
// as a grip. Under it the bin floor has a fixed step at false-floor height, so the false
// floor is shorter and still drops straight in past the tab.
LABEL_DEPTH = 12;
LABEL_T     = 0.8;     // thickness at the front edge; the underside slopes at 45 degrees

// Optional stick-on rubber feet: they go on the screw posts of the tile's four corner cells,
// which are a little wider for that. (A tile on feet is not screwed to a wall, so the screw
// hole under the foot does not matter.)
FOOT_PAD_D  = 10;
FOOT_D      = 8.6;     // BUY: stick-on rubber bumper, 8 mm across, about 2 mm high
FOOT_RECESS = 1.7;     // a 2 mm foot stands only 0.3 mm proud, so tiles with and without feet sit level

// Compartment dividers inside a bin
DIVIDER_T   = 1.2;
WIRE_GAP_W  = 11.5;    // opening at the foot of each divider, under the false floors: an LED board passes through

// LED holder under each clear false floor
LED_PCB_D    = 10.5;  // BUY: single WS2812B-V5/V6 on a round board, 9.4-10 mm across, about 3 mm high
LED_FIT      = 0.2;
LED_HOLDER_H = 1.6;
LED_HOLDER_T = 1.0;

// Clear sleeve round a jar: stands on the lit false floor and carries the light up
JAR_D      = 25.1;   // 20 ml paint jar diameter
JAR_H      = 45;     // jar height, as given
CLEANER_D  = 34.35;  // 60 ml airbrush cleaner bottle
CLEANER_H  = 75;
BOTTLE_D   = 48.2;   // 210 ml bottle
BOTTLE_H   = 120;
JAR_FIT    = 0.5;    // clearance round the jar
SLEEVE_MIN = 0.8;    // thinnest sleeve wall worth printing
SLEEVE_WALL = 1.6;   // wall of the hollow sleeve
SLEEVE_BASE = 0.8;

// Power cell of a starter tile: four feed pins in a row, 12-24 V. They sit in wells below
// the socket floor, so the flat foot of a normal bin can never touch them. The power bin
// reaches them with four brass screw heads that stand proud of its foot. Two pins per
// pole, because one spring pin carries about 2 A.
FEED_X          = [-12, -5, 5, 12];   // minus, plus, plus, minus: the same after a half turn
FEED_WELL_D     = 6.6;
FEED_WELL_DEPTH = 2.6;
FEED_HEAD_D     = 5.6;   // BUY: M3 brass pan-head screw
FEED_HEAD_H     = 2.4;
FEED_SCREW_D    = 3.2;
FEED_PIN_TIP    = -1.6;  // free height of a feed pin tip: 0.8 mm of travel left when the power bin sits
FEED_BOARD_X    = [-15, 15];   // feed board (pcb/feed_board): same idea as the cell board, one screw at its centre
FEED_BOARD_Z    = FEED_PIN_TIP - PIN_ABOVE_BOARD;

// Power bin: opening for the DC input socket in the back wall
DC_JACK_D = 8.2;   // BUY: panel-mount DC barrel socket, 5.5 x 2.1 mm
DC_JACK_Z = 20;      // above the board
POWER_BOARD = [34, 38, 1.6];   // pcb/power_board, lying flat
POWER_BOARD_Z = 12;            // on two ledges, above the nuts of the feed screws
