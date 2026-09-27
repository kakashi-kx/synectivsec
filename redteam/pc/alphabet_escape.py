#!/usr/bin/env python3
"""PC violation -> CI2 counterexample. Guard-level sequence policy weakened."""
import os, re, subprocess, sys, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDTEAM_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(REDTEAM_DIR)
TLA_SRC = os.path.join(ROOT_DIR, "tla", "Composition.tla")
TLA_CFG = os.path.join(ROOT_DIR, "tla", "Composition.cfg")
GEN_DIR = os.path.join(REDTEAM_DIR, "generated", "pc")
TLA_JAR = os.environ.get("TLA_JAR", os.path.expanduser("~/tla/tla2tools.jar"))

def load():
    with open(TLA_SRC) as f:
        return f.read()

def weaken(src):
    # 1. Insert a guard helper right after SequencePolicyOK definition.
    #    The guard is what DoAction will use; the strict helper stays for CI2.
    strict_def = re.compile(
        r"(SequencePolicyOK\(h\) ==\s*\n\s*\\A i \\in 1\.\.\(Len\(h\) - 1\) :\s*\n\s*~ \(h\[i\]\.action = send /\\ h\[i\+1\]\.action = send\))",
        re.MULTILINE)
    src, n1 = strict_def.subn(
        r"\1\n\nGuard_SequencePolicy(h) == TRUE",  # weakened guard
        src)
    if n1 == 0:
        print("ERROR: SequencePolicyOK not found"); sys.exit(2)

    # 2. Replace DoAction's reference to SequencePolicyOK with Guard_SequencePolicy
    #    but ONLY the one inside DoAction. We do this by matching the full DoAction block.
    doaction_pat = re.compile(
        r"(DoAction\(p, a, dom\) ==\s*\n(?:.*\n)*?\s*)/\\ SequencePolicyOK\(Append\(history, \[principal \|-> p, action \|-> a, at \|-> time\]\)\)",
        re.MULTILINE)
    src, n2 = doaction_pat.subn(
        r"\1/\\ Guard_SequencePolicy(Append(history, [principal |-> p, action |-> a, at |-> time]))",
        src)
    if n2 == 0:
        print("ERROR: DoAction SequencePolicyOK guard not found"); sys.exit(2)

    return src

def run(tla, cfg):
    return subprocess.run(
        ["java", "-Xmx2g", "-XX:+UseParallelGC", "-jar", TLA_JAR,
         "-workers", "4", "-config", cfg, tla],
        capture_output=True, text=True, timeout=600)

def main():
    shutil.rmtree(GEN_DIR, ignore_errors=True)
    os.makedirs(GEN_DIR, exist_ok=True)
    out_tla = os.path.join(GEN_DIR, "Composition.tla")
    out_cfg = os.path.join(GEN_DIR, "Composition.cfg")
    with open(out_tla, "w") as f:
        f.write(weaken(load()))
    shutil.copy(TLA_CFG, out_cfg)
    print(f"[PC] wrote {out_tla}")
    print(f"[PC] attack: guard-level sequence policy disabled")
    print(f"[PC] expected: CI2_SequenceSoundness violated")
    r = run(out_tla, out_cfg)
    o = r.stdout + r.stderr
    if "CI2_SequenceSoundness is violated" in o:
        print("[PC] ATTACK SUCCEEDED - CI2 violated")
        print(o[:600]); sys.exit(0)
    if "No error has been found" in o:
        print("[PC] ATTACK FAILED - CI2 held"); sys.exit(1)
    print("[PC] unexpected:"); print(o[-1500:]); sys.exit(2)

if __name__ == "__main__":
    main()
