mario:

    pointer indexing
    110368: 3EF9 - ADD HL,DE
    110368: 3EFA - DEC B
    110368: 3EFB - JR NZ,$3EF9

    delay
    76040: FFBC - DEC A
    76040: FFBD - JR NZ,$FFBC

    memcpy
    30656: 05DE - LD A,(HL+)
    30656: 05DF - LD (DE),A
    30656: 05E0 - INC DE
    30656: 05E1 - DEC BC
    30656: 05E2 - LD A,B
    30656: 05E3 - OR C
    30656: 05E4 - JR NZ,$05DE


    20085: 25B0 - LD A,L
    20085: 25B1 - CP $A0
    19099: 25B3 - JP NC,$25BF
    19099: 25B6 - LD A,$B4
    19099: 25B8 - LD (HL),A
    19099: 25B9 - INC HL
    19099: 25BA - INC HL
    19099: 25BB - INC HL
    19099: 25BC - INC HL
    19099: 25BD - JR $25B0

    memset
    16384: 01C5 - LD (HL-),A
    16384: 01C6 - DEC B
    16384: 01C7 - JR NZ,$01C5

    16198: 2CF0 - LD A,(HL+)
    16198: 2CF1 - LD (DE),A
    16198: 2CF2 - INC DE
    16198: 2CF3 - DEC B
    16198: 2CF4 - JR NZ,$2CF0

pokeman:
    scy wait loop
    5122823: 7292 - LD A,($44+$FF00)
    5122823: 7294 - CP L
    5122823: 7295 - JR NZ,$7292

    scy wait loop
    635946: 44CF - LD A,($44+$FF00)
    635946: 44D1 - CP L
    635946: 44D2 - JR NZ,$44CF

    delay:
    177600: FF86 - DEC A
    177600: FF87 - JR NZ,$FF86


    108659: 019A - LD A,($B8+$FF00)
    108659: 019C - PUSH AF
    108659: 019D - LD A,$03
    108659: 019F - LD ($B8+$FF00),A
    108659: 01A1 - LD ($2000),A
    108659: 01A4 - CALL $4000
    108659: 4000 - LD A,($F8+$FF00)
    108659: 4002 - CP $0F
    108659: 4004 - JP Z,$403C
    108659: 4007 - LD B,A
    108659: 4008 - LD A,($B1+$FF00)
    108659: 400A - LD E,A
    108659: 400B - XOR B
    108659: 400C - LD D,A
    108659: 400D - AND E
    108659: 400E - LD ($B2+$FF00),A
    108659: 4010 - LD A,D
    108659: 4011 - AND B
    108659: 4012 - LD ($B3+$FF00),A
    108659: 4014 - LD A,B
    108659: 4015 - LD ($B1+$FF00),A
    108659: 4017 - LD A,($D730)

dr mario:
    delay:
    193720: FFBC - DEC A
    193720: FFBD - JR NZ,$FFBC

    memcpy:
    31059: 23BC - LD A,(HL+)
    31059: 23BD - LD (DE),A
    31059: 23BE - INC DE
    31059: 23BF - DEC B
    31059: 23C0 - JR NZ,$23BC

    memcpy:
    28512: 2F26 - LD A,(HL+)
    28512: 2F27 - LD (DE),A
    28512: 2F28 - INC DE
    28512: 2F29 - DEC B
    28512: 2F2A - JR NZ,$2F26
