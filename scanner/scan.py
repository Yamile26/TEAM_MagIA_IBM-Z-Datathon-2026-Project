import re, sys, json, pathlib

# (nombre, regex, vulnerable a cuantica?, debil hoy?)
RULES = [
    ("RSA",    r"RSA\.generate|rsa\.generate_private_key", True,  False),
    ("ECDSA/ECC", r"ec\.generate_private_key|SECP\d+", True,  False),
    ("SHA-1",  r"sha1",  False, True),
    ("MD5",    r"md5",   False, True),
    ("DES",    r"DES\.new", False, True),
    ("TLS<1.2", r"TLSv1(\.1)?\b(?!\.)|TLSv1\.1", False, True),
    ("RC4",    r"RC4", False, True),
]

def scan(root):
    findings = []
    for p in pathlib.Path(root).rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".conf", ".js", ".java"}:
            continue
        for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            for name, rx, quantum, weak in RULES:
                if re.search(rx, line, re.I):
                    findings.append({
                        "file": str(p), "line": n, "algorithm": name,
                        "quantum_vulnerable": quantum, "weak_today": weak,
                        "snippet": line.strip(),
                    })
    return findings

if __name__ == "__main__":
    out = scan(sys.argv[1])
    json.dump(out, open("findings.json", "w"), indent=2)
    for f in out:
        print(f"{f['file']}:{f['line']}  {f['algorithm']}")
    print(f"\nTotal: {len(out)} hallazgos -> findings.json")
