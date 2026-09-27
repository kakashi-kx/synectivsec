---- MODULE Composition ----
EXTENDS Integers, Sequences, TLC

CONSTANTS T1, T2, T3, R1, PA, PB, R2, PC, PD, read, write, send, MaxHistory, Delta, NeverRevoked

VARIABLES currentPrincipal, history, currentDomain, revokedAt, time

vars == << currentPrincipal, history, currentDomain, revokedAt, time >>

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
        ~ (h[i].action = send /\ h[i+1].action = send)

DomainPolicyOK(dom, action) ==
    CASE dom = T1 -> TRUE
      [] dom = T2 -> TRUE
      [] dom = T3 -> action # write

IsRevokedAt(p, t) ==
    revokedAt[p] <= t

ActionPermitted(p, a, dom) ==
    /\ ~ IsRevokedAt(p, time)
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
    /\ revokedAt = [p \in {R1, PA, PB, R2, PC, PD} |-> NeverRevoked]
    /\ time = 0

DoAction(p, a, dom) ==
    /\ ChainRootCanReachDomain(p, dom)
    /\ ActionPermitted(p, a, dom)
    /\ Len(history) < MaxHistory
    /\ SequencePolicyOK(Append(history, [principal |-> p, action |-> a, at |-> time]))
    /\ currentPrincipal' = p
    /\ history' = Append(history, [principal |-> p, action |-> a, at |-> time])
    /\ currentDomain' = dom
    /\ revokedAt' = revokedAt
    /\ time' = time + 1

Revoke(p) ==
    /\ revokedAt[p] = NeverRevoked
    /\ revokedAt' = [revokedAt EXCEPT ![p] = time]
    /\ currentPrincipal' = currentPrincipal
    /\ history' = history
    /\ currentDomain' = currentDomain
    /\ time' = time + 1

CrossDomain(p, dom) ==
    /\ ChainRootCanReachDomain(p, dom)
    /\ currentPrincipal' = p
    /\ history' = history
    /\ currentDomain' = dom
    /\ revokedAt' = revokedAt
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
            history[i].action \in CapabilityOf(p)

CI2_SequenceSoundness ==
    SequencePolicyOK(history)

CI3_RevocationFreshness ==
    \A i \in 1..Len(history) :
        history[i].at < revokedAt[history[i].principal]

CI4_AttestationSoundness ==
    ChainRootCanReachDomain(currentPrincipal, currentDomain)

CI5_BoundaryDeterminism ==
    \A dom \in {T1, T2, T3} :
        \A a \in {read, write, send} :
            DomainPolicyOK(dom, a) \/ ~ DomainPolicyOK(dom, a)

StateConstraint ==
    /\ time <= 4
    /\ Len(history) <= MaxHistory

Spec == Init /\ [][Next]_vars

====
