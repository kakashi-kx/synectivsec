#!/usr/bin/env python3
"""RS violation -> CI3 counterexample. Guard-level revocation check removed."""
import os, re, subprocess, sys, shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REDTEAM_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(REDTEAM_DIR)
TLA_SRC = os.path.join(ROOT_DIR, "tla", "Composition.tla")
TLA_CFG = os.path.join(ROOT_DIR, "tla", "Composition.cfg")
GEN_DIR = os.path.join(REDTEAM_DIR, "generated", "rs")
TLA_JAR = os.environ.get("TLA_JAR", os.path.expanduser("~/tla/tla2tools.jar"))

def load():
    with open(TLA_SRC) as f:
        return f.read()

def weaken(src):
    # Insert Guard_ActionPermitted right after ActionPermitted definition.
    strict_def = re.compile(
        r"(ActionPermitted\(p, a, dom\) ==\s*\n\s*/\\ ~ IsRevokedAt\(p, time\)\s*\n\s*/\\ a \\in CapabilityOf\(p\)\s*\n\s*/\\ DomainPolicyOK\(dom, a\))",
        re.MULTILINE)
    src, n1 = strict_def.subn(
        r"\1\n\nGuard_ActionPermitted(p, a, dom) ==\n    /\\ a \\in CapabilityOf(p)\n    /\\ DomainPolicyOK(dom, a)",
        src)
    if n1 == 0:
        print("ERROR: ActionPermitted not found"); sys.exit(2)

    # Replace DoAction's ActionPermitted guard with Guard_ActionPermitted
    doaction_pat = re.compile(
        r"(DoAction\(p, a, dom\) ==\s*\n\s*/\\ ChainRootCanReachDomain\(p, dom\)\s*\n\s*)/\\ ActionPermitted\(p, a, dom\)",
        re.MULTILINE)
    src, n2 = doaction_pat.subn(
        r"\1/\\ Guard_ActionPermitted(p, a, dom)",
        src)
    if n2 == 0:
        print("ERROR: DoAction ActionPermitted guard not found"); sys.exit(2)

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
    print(f"[RS] wrote {out_tla}")
    print(f"[RS] attack: guard-level revocation check removed")
    print(f"[RS] expected: CI3_RevocationFreshness violated")
    r = run(out_tla, out_cfg)
    o = r.stdout + r.stderr
    if "CI3_RevocationFreshness is violated" in o:
        print("[RS] ATTACK SUCCEEDED - CI3 violated")
        print(o[:600]); sys.exit(0)
    if "No error has been found" in o:
        print("[RS] ATTACK FAILED - CI3 held"); sys.exit(1)
    print("[RS] unexpected:"); print(o[-1500:]); sys.exit(2)

if __name__ == "__main__":
    main()
