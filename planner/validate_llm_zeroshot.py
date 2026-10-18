import json, os, re, subprocess, time
PORT = 4435
d = json.load(open(os.path.expanduser("~/shared/proposals_zeroshot.json")))
FALLBACK, cache = "X25519MLKEM768:X25519", {}

def validate(g):
    if g in cache:
        return cache[g]
    ok = False
    if re.fullmatch(r"[A-Za-z0-9_:\-]{1,80}", g):  # la salida del LLM no es confiable
        s = subprocess.Popen(["openssl", "s_server", "-accept", str(PORT), "-cert", "tls/srv.crt",
            "-key", "tls/srv.key", "-www", "-tls1_3", "-groups", g],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.2)
        try:
            o = subprocess.run(["openssl", "s_client", "-connect", f"localhost:{PORT}", "-tls1_3",
                "-groups", "X25519MLKEM768"], input=b"", capture_output=True, timeout=10)
            ok = b"Negotiated TLS1.3 group: X25519MLKEM768" in o.stdout + o.stderr
        except Exception:
            pass
        finally:
            s.kill(); s.wait()
    cache[g] = ok
    return ok

first = anyk = total = 0
final = {}
for a in d["assets"]:
    for i, rep in enumerate(a["repeats"]):
        res = [validate(c) for c in rep]
        total += 1; first += res[0]; anyk += any(res)
        if i == 0:
            c = next((x for x, r in zip(rep, res) if r), None)
            final[a["location"]] = (c, "granite") if c else (FALLBACK, "plantilla")

print(f"Propuestas de {d['model']}, {total} pruebas:")
print(f"  validas al primer intento: {first}/{total} ({100*first/total:.0f}%)")
print(f"  validas en <=3 intentos  : {anyk}/{total} ({100*anyk/total:.0f}%)")
print(f"  necesitaron plantilla    : {total-anyk}/{total}")
for k, (g, src) in final.items():
    print(f"  {k:<20} {g}  (fuente: {src})")
s = d["summary"]
print("\nResumen del LLM", "(cifras verificadas):" if s["numbers_ok"] else "(RECHAZADO, cifras no presentes en los datos):")
print(" ", s["text"])
json.dump({"total": total, "primer_intento": first, "hasta_3": anyk,
           "config_final": {k: {"groups": g, "fuente": src} for k, (g, src) in final.items()},
           "resumen": s}, open("plan_llm_zeroshot.json", "w"), indent=2, ensure_ascii=False)
