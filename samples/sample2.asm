438586:
        7.76%
        3EF9 - ADD HL,DE
        3EFA - DEC B
        3EFB - JR NZ,$3EF9
148504:
        2.10%
        FFBC - DEC A
        FFBD - JR NZ,$FFBC
90899:
        3.21%
        484F - LD A,(HL+)
        4850 - LD (DE),A
        4851 - INC DE
        4852 - DEC B
        4853 - JR NZ,$484F
68577:
        1.94%
        0ABF - DEC B
        0AC0 - JR Z,$0AC6
        0AC2 - SUB $08
        0AC4 - JR $0ABF
64077:
        4.76%
        25B0 - LD A,L
        25B1 - CP $A0
        25B3 - JP NC,$25BF
        25B6 - LD A,$B4
        25B8 - LD (HL),A
        25B9 - INC HL
        25BA - INC HL
        25BB - INC HL
        25BC - INC HL
        25BD - JR $25B0
46471:
        1.81%
        0AF8 - LD A,(HL)
        0AF9 - CP $FF
        0AFB - JR NZ,$0B02
        0AFD - ADD HL,DE
        0AFE - DEC B
        0AFF - JR NZ,$0AF8
35238:
        1.25%
        2D02 - LD A,(DE)
        2D03 - LD (HL+),A
        2D04 - INC DE
        2D05 - DEC B
        2D06 - JR NZ,$2D02
