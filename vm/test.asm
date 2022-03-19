[org 100]
;  |OP|A0   |A1
db 1,  lp, 0,  2,  0 ;Load H[2] = LOOP (branch arg!)
db 1,  5,   0,  0,  0 ;Load H[0] = 5
db 1,  1,   0,  1,  0 ;Load H[1] = 1

lp:
db 3,  1,   0,  0,  0 ;Set DIFF operation
db 5,  0,   0,  0,  0 ;CRUNCH!

db 3,  2,	0,	0,	0 ;Set BNZ operation
db 5,  0,	0,	0,	0 ;CRUNCH!
