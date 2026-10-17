import json
import numpy as np, pandas as pd
from xgboost import XGBRegressor
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split

Z = 10  # supuesto declarado
ALGS = ["RSA","ECDSA/ECC","SHA-1","MD5","DES","TLS<1.2","RC4","AES-256","ML-KEM"]
MIG = {"RSA":3,"ECDSA/ECC":3,"SHA-1":1,"MD5":1,"DES":1,"TLS<1.2":2,"RC4":1,"AES-256":1,"ML-KEM":1}
WEAK = {"SHA-1","MD5","DES","TLS<1.2","RC4"}
QUANT = {"RSA","ECDSA/ECC"}

def rule_label(alg, life, internet):
    mig = MIG[alg]
    if alg in WEAK: return 100 + life
    if alg in QUANT and life + mig - Z > 0: return (life + mig - Z) + 5 * internet
    return 0

rng = np.random.default_rng(42)
N = 2000
df = pd.DataFrame({
    "alg": rng.integers(0, len(ALGS), N),
    "data_life": rng.choice([1, 5, 10, 20, 30, 50], N),
    "internet": rng.integers(0, 2, N),
})
df["migration"] = df["alg"].map(lambda i: MIG[ALGS[i]])
df["label"] = [rule_label(ALGS[a], l, i) for a, l, i in zip(df.alg, df.data_life, df.internet)]

X = df[["alg", "data_life", "internet", "migration"]]
Xtr, Xte, ytr, yte = train_test_split(X, df["label"], test_size=0.2, random_state=0)
model = XGBRegressor(n_estimators=200, max_depth=4, learning_rate=0.1)
model.fit(Xtr, ytr)

rho = spearmanr(model.predict(Xte), yte).correlation
print(f"Spearman (test sintetico vs reglas): {rho:.3f}")
for name, imp in sorted(zip(X.columns, model.feature_importances_), key=lambda t: -t[1]):
    print(f"  importancia {name:<10} {imp:.3f}")

# Aplicar al Hospital Demo
rows = json.load(open("ranking.json"))
for r in rows:
    f = r["file"]
    internet = 1 if ("nginx" in f or "pacientes" in f) else 0
    feats = pd.DataFrame([{"alg": ALGS.index(r["algorithm"]), "data_life": r["data_life"],
                           "internet": internet, "migration": r["migration_years"]}])
    r["ml_score"] = float(model.predict(feats)[0])
rows.sort(key=lambda r: r["ml_score"], reverse=True)
json.dump(rows, open("ranking_ml.json", "w"), indent=2)
print()
for r in rows:
    print(f"{r['ml_score']:>7.1f}  {r['algorithm']:<10} {r['file'].split('/')[-1]}:{r['line']}")
