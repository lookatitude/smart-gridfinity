// Gridfinity standard dimensions (mm). Single source of truth:
// every other file includes this one and never hardcodes these numbers.

GRID      = 42;     // X/Y pitch of one cell
UNIT_Z    = 7;      // height of one "u"
CLEARANCE = 0.5;    // total X/Y gap between a bin and its grid space (0.25 per side)

// Bin foot: stepped chamfer, listed bottom to top as [z, inset from the foot's top outline].
FOOT_PROFILE = [[0, 2.95], [0.8, 2.15], [2.6, 2.15], [4.75, 0]];
FOOT_H       = 4.75;
BIN_R        = 3.75;   // outer corner radius of a bin

// Socket (baseplate cell and stacking lip): [z, inset from the 42 mm grid outline].
SOCKET_PROFILE = [[0, 2.85], [0.7, 2.15], [2.5, 2.15], [4.65, 0]];
SOCKET_H       = 4.65;
SOCKET_R       = 4;    // corner radius at the top of a socket

// Bin body
WALL      = 0.95;   // wall thickness
FLOOR_Z   = 7;      // top of the bin floor, measured from the bottom of the foot
LIP_H     = 4.4;    // nominal stacking-lip height above the bin body
LIP_TRIM  = 0.4;    // shave the knife edge off the lip tip so it prints cleanly
LIP_INSET = SOCKET_PROFILE[0][1] - CLEARANCE / 2;   // lip overhang from the outer wall (2.6)

// Magnets (optional)
MAGNET_D      = 6.5;
MAGNET_H      = 2.4;
MAGNET_OFFSET = 13;   // hole centre distance from the cell centre, in X and Y

EPS = 0.01;   // overlap used to avoid coincident faces in boolean cuts
$fn = 48;
