# From file: /Users/steinbeck/Dropbox/develop/lucy-ng/.claude/worktrees/agent-a21738128f728cb0b/.planning/phases/72-design-re-validation/experiment/arm_a.lsd.
; arm_a.lsd -- Emergent test: no SKEL benzene, full constraints preserved
; D-04 question: does aromatic ring emerge from COSY/HMBC constraints alone?
; Derived from iteration_03/compound_native.lsd by removing SKEL/PATH/F3 from FEXP
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

DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
DEFF F2 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring4"
FEXP "NOT F1 AND NOT F2"
#
OUTLSD
15 1
 1  C 4 0 3 3  0  14 2  15 1   9 1   0 0
 1  C 4 0 3 3  0   9 1   4 2   3 1   0 0
 1  C 4 0 3 3  0   6 2   8 1   2 1   0 0
 1  C 4 1 2 2  0   7 1   2 2   0 0   0 0
 1  C 4 1 2 2  0   6 1   7 2   0 0   0 0
 1  C 4 1 2 2  0   5 1   3 2   0 0   0 0
 1  C 4 1 2 2  0   4 1   5 2   0 0   0 0
 1  C 4 2 2 2  0  10 1   3 1   0 0   0 0
 1  C 4 1 3 3  0  13 1   1 1   2 1   0 0
 1  C 4 1 3 3  0  11 1  12 1   8 1   0 0
 1  C 4 3 1 1  0  10 1   0 0   0 0   0 0
 1  C 4 3 1 1  0  10 1   0 0   0 0   0 0
 1  C 4 3 1 1  0   9 1   0 0   0 0   0 0
 1  O 2 0 1 1  0   1 2   0 0   0 0   0 0
 1  O 2 1 1 1  0   1 1   0 0   0 0   0 0
15 2
 1  C 4 0 3 3  0  14 2  15 1   9 1   0 0
 1  C 4 0 3 3  0   9 1   4 2   5 1   0 0
 1  C 4 0 3 3  0   6 1   8 1   7 2   0 0
 1  C 4 1 2 2  0   7 1   2 2   0 0   0 0
 1  C 4 1 2 2  0   6 2   2 1   0 0   0 0
 1  C 4 1 2 2  0   5 2   3 1   0 0   0 0
 1  C 4 1 2 2  0   4 1   3 2   0 0   0 0
 1  C 4 2 2 2  0  10 1   3 1   0 0   0 0
 1  C 4 1 3 3  0  13 1   1 1   2 1   0 0
 1  C 4 1 3 3  0  11 1  12 1   8 1   0 0
 1  C 4 3 1 1  0  10 1   0 0   0 0   0 0
 1  C 4 3 1 1  0  10 1   0 0   0 0   0 0
 1  C 4 3 1 1  0   9 1   0 0   0 0   0 0
 1  O 2 0 1 1  0   1 2   0 0   0 0   0 0
 1  O 2 1 1 1  0   1 1   0 0   0 0   0 0
0
