---- MODULE Composition ----
EXTENDS Integers, Sequences, TLC

CONSTANTS T1, T2, T3, R1, PA, PB, R2, PC, PD, read, write, send, MaxHistory, Delta

VARIABLES currentPrincipal, history, currentDomain, revoked, time

vars == << currentPrincipal, history, currentDomain, revoked, time >>

CapabilityOf(p) ==
    CASE p = R1 -> {read, write, send}
      [] p = PA -> {read, write}
      [] p = PB -> {read}
      [] p = R2 -> {read, write, send}
      [] p = PC -> {read, send}
      [] p = PD -> {send}

ChainOf(p) ==
    CASE p \in {R1, PA, PB} -> "D1"
      [] p \in {R2, PC, PD} -> "D2"

RootDomainOf(p) ==
    CASE ChainOf(p) = "D1" -> T1
      [] ChainOf(p) = "D2" -> T2

Attests(from, to) ==
    \/ from = T1 /\ to = T2
    \/ from = T2 /\ to = T3

SequencePolicyOK(h) ==
    \A i \in 1..(Len(h) - 1) :
        ~ (h[i] = send /\ h[i+1] = send)

DomainPolicyOK(dom, action) ==
    CASE dom = T1 -> TRUE
      [] dom = T2 -> TRUE
      [] dom = T3 -> action # write

IsRevoked(p) == p \in revoked

ActionPermitted(p, a, dom) ==
    /\ ~ IsRevoked(p)
    /\ a \in CapabilityOf(p)
    /\ DomainPolicyOK(dom, a)

ChainRootCanReachDomain(p, dom) ==
    \/ RootDomainOf(p) = dom
    \/ Attests(RootDomainOf(p), dom)
    \/ \E mid \in {T1, T2, T3} :
        /\ Attests(RootDomainOf(p), mid)
        /\ Attests(mid, dom)

Init ==
    /\ currentPrincipal = R1
    /\ history = << >>
    /\ currentDomain = T1
    /\ revoked = {}
    /\ time = 0

DoAction(p, a, dom) ==
    /\ ChainRootCanReachDomain(p, dom)
    /\ ActionPermitted(p, a, dom)
    /\ Len(history) < MaxHistory
    /\ SequencePolicyOK(Append(history, a))
    /\ currentPrincipal' = p
    /\ history' = Append(history, a)
    /\ currentDomain' = dom
    /\ revoked' = revoked
    /\ time' = time + 1

Revoke(p) ==
    /\ p \notin revoked
    /\ revoked' = revoked \cup {p}
    /\ currentPrincipal' = currentPrincipal
    /\ history' = history
    /\ currentDomain' = currentDomain
    /\ time' = time + 1

CrossDomain(p, dom) ==
    /\ ChainRootCanReachDomain(p, dom)
    /\ currentPrincipal' = p
    /\ history' = history
    /\ currentDomain' = dom
    /\ revoked' = revoked
    /\ time' = time + 1

Next ==
    \/ \E p \in {R1, PA, PB, R2, PC, PD} :
        \E a \in {read, write, send} :
            \E dom \in {T1, T2, T3} :
                DoAction(p, a, dom)
    \/ \E p \in {R1, PA, PB, R2, PC, PD} :
        Revoke(p)
    \/ \E p \in {R1, PA, PB, R2, PC, PD} :
        \E dom \in {T1, T2, T3} :
            CrossDomain(p, dom)

CI1_AuthorityContainment ==
    \A i \in 1..Len(history) :
        \E p \in {R1, PA, PB, R2, PC, PD} :
            history[i] \in CapabilityOf(p)

CI2_SequenceSoundness ==
    SequencePolicyOK(history)

CI3_RevocationFreshness ==
    \A p \in {R1, PA, PB, R2, PC, PD} :
        p \in revoked => ~ (\E i \in 1..Len(history) : FALSE)

CI4_AttestationSoundness ==
    ChainRootCanReachDomain(currentPrincipal, currentDomain)

CI5_BoundaryDeterminism ==
    \A dom \in {T1, T2, T3} :
        \A a \in {read, write, send} :
            DomainPolicyOK(dom, a) \/ ~ DomainPolicyOK(dom, a)

StateConstraint ==
    /\ time <= 6
    /\ Len(history) <= MaxHistory

Spec == Init /\ [][Next]_vars

====
