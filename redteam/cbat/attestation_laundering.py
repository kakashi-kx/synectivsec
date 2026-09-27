#!/usr/bin/env python3
"""CBAT violation -> CI4 counterexample. Guard-level attestation reach weakened."""
import os, re, subprocess, sys, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDTEAM_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(REDTEAM_DIR)
TLA_SRC = os.path.join(ROOT_DIR, "tla", "Composition.tla")
TLA_CFG = os.path.join(ROOT_DIR, "tla", "Composition.cfg")
GEN_DIR = os.path.join(REDTEAM_DIR, "generated", "cbat")
TLA_JAR = os.environ.get("TLA_JAR", os.path.expanduser("~/tla/tla2tools.jar"))

def load():
    with open(TLA_SRC) as f:
        return f.read()

def weaken(src):
    # Insert Guard_ChainReach right after ChainRootCanReachDomain definition.
    strict_def = re.compile(
        r"(ChainRootCanReachDomain\(p, dom\) ==\s*\n\s*\\/ RootDomainOf\(p\) = dom\s*\n\s*\\/ Attests\(RootDomainOf\(p\), dom\)\s*\n\s*\\/ \\E mid \\in \{T1, T2, T3\} :\s*\n\s*/\\ Attests\(RootDomainOf\(p\), mid\)\s*\n\s*/\\ Attests\(mid, dom\))",
        re.MULTILINE)
    src, n1 = strict_def.subn(
        r"\1\n\nGuard_ChainReach(p, dom) == TRUE",
        src)
    if n1 == 0:
        print("ERROR: ChainRootCanReachDomain not found"); sys.exit(2)

    # Replace DoAction's ChainRootCanReachDomain guard with Guard_ChainReach
    doaction_pat = re.compile(
        r"(DoAction\(p, a, dom\) ==\s*\n\s*)/\\ ChainRootCanReachDomain\(p, dom\)",
        re.MULTILINE)
    src, n2 = doaction_pat.subn(
        r"\1/\\ Guard_ChainReach(p, dom)",
        src)
    if n2 == 0:
        print("ERROR: DoAction ChainRootCanReachDomain guard not found"); sys.exit(2)

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
    print(f"[CBAT] wrote {out_tla}")
    print(f"[CBAT] attack: guard-level attestation reach disabled")
    print(f"[CBAT] expected: CI4_AttestationSoundness violated")
    r = run(out_tla, out_cfg)
    o = r.stdout + r.stderr
    if "CI4_AttestationSoundness is violated" in o:
        print("[CBAT] ATTACK SUCCEEDED - CI4 violated")
        print(o[:600]); sys.exit(0)
    if "No error has been found" in o:
        print("[CBAT] ATTACK FAILED - CI4 held"); sys.exit(1)
    print("[CBAT] unexpected:"); print(o[-1500:]); sys.exit(2)

if __name__ == "__main__":
    main()
