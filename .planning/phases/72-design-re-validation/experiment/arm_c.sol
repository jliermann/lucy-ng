# From file: /Users/steinbeck/Dropbox/develop/lucy-ng/.claude/worktrees/agent-a21738128f728cb0b/.planning/phases/72-design-re-validation/experiment/arm_c.lsd.
; arm_c.lsd -- Bond-range 4J test: arm_a base + HMBC X Y 2 4 for 3 known 4J suspects
; D-01 validation: does extended bond range keep solutions? Does aromatic ring still emerge?
; Derived from arm_a.lsd + 3 HMBC X Y 2 4 lines for 4J W-path correlations
;
MULT 1 C 2 0
MULT 2 C 2 0
MULT 3 C 2 0
MULT 4 C 2 1
MULT 5 C 2 1
MULT 6 C 2 1
MULT 7 C 2 1
MULT 8 C 3 2
MULT 9 C 3 1
MULT 10 C 3 1
MULT 11 C 3 3
MULT 12 C 3 3
MULT 13 C 3 3
MULT 14 O 2 0
MULT 15 O 3 1

HSQC 4 4
HSQC 5 5
HSQC 6 6
HSQC 7 7
HSQC 8 8
HSQC 9 9
HSQC 10 10
HSQC 11 11
HSQC 12 12
HSQC 13 13

BOND 1 14
BOND 1 15
BOND 10 11
BOND 10 12

COSY 9 13
COSY 4 7
COSY 5 6
COSY 8 10
COSY 10 11

HMBC 1 9
HMBC 1 13
HMBC 2 9
HMBC 10 11
HMBC 13 9
HMBC (8 9) 6
HMBC (8 9) 4
HMBC (8 9) 11
HMBC 3 6
HMBC 2 4
HMBC 3 8 2 4    ; Cq(136.96) -- CH2(45.03), 4J W-path through aromatic ring (D-01 test)
HMBC 3 13 2 4   ; Cq(136.96) -- CH3(18.09), 4J W-path
HMBC 3 9 2 4    ; Cq(136.96) -- CH(44.90), 4J W-path (removed in iter3; re-added as extended range)

DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
#
OUTLSD
15 1
 1  C 4 0 3 3  0  14 2  15 1   9 1   0 0
 1  C 4 0 3 3  0   3 2   8 1   4 1   0 0
 1  C 4 0 3 3  0   9 1   2 2   6 1   0 0
 1  C 4 1 2 2  0   7 2   2 1   0 0   0 0
 1  C 4 1 2 2  0   6 2   7 1   0 0   0 0
 1  C 4 1 2 2  0   5 2   3 1   0 0   0 0
 1  C 4 1 2 2  0   4 2   5 1   0 0   0 0
 1  C 4 2 2 2  0  10 1   2 1   0 0   0 0
 1  C 4 1 3 3  0  13 1   1 1   3 1   0 0
 1  C 4 1 3 3  0  11 1  12 1   8 1   0 0
 1  C 4 3 1 1  0  10 1   0 0   0 0   0 0
 1  C 4 3 1 1  0  10 1   0 0   0 0   0 0
 1  C 4 3 1 1  0   9 1   0 0   0 0   0 0
 1  O 2 0 1 1  0   1 2   0 0   0 0   0 0
 1  O 2 1 1 1  0   1 1   0 0   0 0   0 0
0
