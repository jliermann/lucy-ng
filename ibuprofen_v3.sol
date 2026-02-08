# From file: ibuprofen_v3.lsd.
; LSD input for Ibuprofen C13H18O2 - Version 3
; Phase 26-05 - Explicit benzene ring structure

; ============================================
; MULT: Atom definitions
; ============================================

; Carboxylic acid
MULT 1 C 2 0    ; C=O
MULT 2 O 2 0    ; =O
MULT 3 O 3 1    ; -OH

; Benzene ring (6 carbons, 4 CH + 2 quaternary)
MULT 4 C 2 0    ; Aromatic quat (140.84)
MULT 5 C 2 1    ; Aromatic CH (129.38)
MULT 6 C 2 1    ; Aromatic CH (127.26)
MULT 7 C 2 0    ; Aromatic quat (136.96)
MULT 8 C 2 1    ; Aromatic CH (127.26)
MULT 9 C 2 1    ; Aromatic CH (129.38)

; Substituents
MULT 10 C 3 2   ; Benzylic CH2 (44.90)
MULT 11 C 3 1   ; Isopropyl CH (30.14)
MULT 12 C 3 3   ; Isopropyl CH3 (22.37)
MULT 13 C 3 3   ; Isopropyl CH3 (22.37)
MULT 14 C 3 1   ; CH bearing COOH (45.03)
MULT 15 C 3 3   ; CH3 on C14 (18.09)

; sp2: 8 ✓ | H: 18 ✓

; ============================================
; HSQC
; ============================================

HSQC 5 5
HSQC 6 6
HSQC 8 8
HSQC 9 9
HSQC 10 10
HSQC 11 11
HSQC 12 12
HSQC 13 13
HSQC 14 14
HSQC 15 15

; ============================================
; Benzene ring structure (explicit)
; ============================================

BOND 4 5        ; Ring C-C
BOND 5 6        ; Ring C-C
BOND 6 7        ; Ring C-C
BOND 7 8        ; Ring C-C
BOND 8 9        ; Ring C-C
BOND 9 4        ; Ring C-C (closes ring)

; ============================================
; Substituent connections
; ============================================

BOND 4 10       ; Benzene C4 → benzylic CH2
BOND 10 11      ; CH2 → isopropyl CH
BOND 11 12      ; CH → CH3
BOND 11 13      ; CH → CH3

BOND 7 14       ; Benzene C7 → CH
BOND 14 15      ; CH → CH3
BOND 14 1       ; CH → C=O

; ============================================
; Carboxylic acid
; ============================================

BOND 1 2        ; C=O
BOND 1 3        ; C-OH

; ============================================
; HMBC (just a few for validation)
; ============================================

HMBC 1 15       ; C=O to CH3
HMBC 4 10       ; Aromatic quat to CH2
HMBC 7 14       ; Aromatic quat to CH

#
OUTLSD
15 1
 1  C 4 0 3 3  0  14 1   2 2   3 1   0 0
 1  O 2 0 1 1  0   1 2   0 0   0 0   0 0
 1  O 2 1 1 1  0   1 1   0 0   0 0   0 0
 1  C 4 0 3 3  0   5 2   9 1  10 1   0 0
 1  C 4 1 2 2  0   4 2   6 1   0 0   0 0
 1  C 4 1 2 2  0   5 1   7 2   0 0   0 0
 1  C 4 0 3 3  0   6 2   8 1  14 1   0 0
 1  C 4 1 2 2  0   7 1   9 2   0 0   0 0
 1  C 4 1 2 2  0   8 2   4 1   0 0   0 0
 1  C 4 2 2 2  0   4 1  11 1   0 0   0 0
 1  C 4 1 3 3  0  10 1  12 1  13 1   0 0
 1  C 4 3 1 1  0  11 1   0 0   0 0   0 0
 1  C 4 3 1 1  0  11 1   0 0   0 0   0 0
 1  C 4 1 3 3  0   7 1  15 1   1 1   0 0
 1  C 4 3 1 1  0  14 1   0 0   0 0   0 0
0
