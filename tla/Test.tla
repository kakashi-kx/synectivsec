---- MODULE Test ----
EXTENDS Integers

CONSTANTS
    A, B, C

VARIABLE x

Init == x = 0
Next == x' = x + 1
Spec == Init /\ [][Next]_x

====
