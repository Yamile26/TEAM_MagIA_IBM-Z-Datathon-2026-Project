import json
Z = 10  # anios hasta amenaza cuantica relevante: SUPUESTO configurable, no prediccion
DATA_LIFE = [("historias", 30), ("pacientes", 20), ("nginx", 5)]
MIGRATION = {"RSA": 3, "ECDSA/ECC": 3, "SHA-1": 1, "MD5": 1,
             "DES": 1, "TLS<1.2": 2, "RC4": 1}

def data_life(path):
    for key, years in DATA_LIFE:
        if key in path:
            return years
    return 5

rows = []
for f in json.load(open("findings.json")):
    x, y = data_life(f["file"]), MIGRATION.get(f["algorithm"], 2)
    mosca = x + y - Z
    if f["weak_today"]:
        urgency, why = 100 + x, "roto o debil HOY"
    elif f["quantum_vulnerable"] and mosca > 0:
        urgency, why = mosca, f"Mosca: {x}+{y} > {Z}"
    else:
        urgency, why = 0, "sin urgencia con estos supuestos"
    rows.append({**f, "data_life": x, "migration_years": y,
                 "urgency": urgency, "reason": why})
rows.sort(key=lambda r: r["urgency"], reverse=True)
json.dump(rows, open("ranking.json", "w"), indent=2)
for r in rows:
    print(f"{r['urgency']:>4}  {r['algorithm']:<10} {r['file'].split('/')[-1]}:{r['line']}  ({r['reason']})")
