import json, subprocess, time

REC = {
 "RSA": "Migrar a TLS hibrido X25519MLKEM768 y firmas ML-DSA-65",
 "ECDSA/ECC": "Migrar a TLS hibrido X25519MLKEM768 y firmas ML-DSA-65",
 "SHA-1": "Reemplazar por SHA-256 o superior",
 "MD5": "Reemplazar por SHA-256 o superior",
 "DES": "Reemplazar por AES-256-GCM",
 "TLS<1.2": "Permitir solo TLS 1.3",
 "RC4": "Reemplazar por AES-256-GCM",
}
rank = json.load(open("ranking_ml.json"))
plan = [{"prioridad": i + 1, "algoritmo": r["algorithm"],
         "ubicacion": f"{r['file'].split('/')[-1]}:{r['line']}",
         "score": round(r["ml_score"], 1), "accion": REC.get(r["algorithm"], "Revisar")}
        for i, r in enumerate(rank)]

candidates = [
    {"nombre": "candidato de prueba del validador (invalido)", "groups": "GRUPO_INEXISTENTE"},
    {"nombre": "TLS 1.3 hibrido", "groups": "X25519MLKEM768:X25519"},
]

def validate(groups):
    srv = subprocess.Popen(["openssl", "s_server", "-accept", "4434", "-cert", "tls/srv.crt",
        "-key", "tls/srv.key", "-www", "-tls1_3", "-groups", groups],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    try:
        out = subprocess.run(["openssl", "s_client", "-connect", "localhost:4434", "-tls1_3",
            "-groups", "X25519MLKEM768"], input=b"", capture_output=True, timeout=10)
        return b"Negotiated TLS1.3 group: X25519MLKEM768" in out.stdout + out.stderr
    except Exception:
        return False
    finally:
        srv.kill(); srv.wait()

chosen = None
for c in candidates:
    ok = validate(c["groups"])
    print(f"{'VALIDA ' if ok else 'RECHAZADA'}  {c['nombre']}  groups={c['groups']}")
    if ok and not chosen:
        chosen = c
if not chosen:
    print("Ningun candidato paso: se usa la plantilla por defecto")

json.dump({"plan": plan, "config_validada": chosen}, open("plan.json", "w"), indent=2)
print("\nPlan priorizado:")
for p in plan:
    print(f"  {p['prioridad']}. [{p['score']:>6}] {p['algoritmo']:<10} {p['ubicacion']:<20} -> {p['accion']}")
