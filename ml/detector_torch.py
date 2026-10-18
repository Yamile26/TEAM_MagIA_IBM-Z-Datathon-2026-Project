import re, random, pathlib, sys, zlib, json
sys.path.insert(0, "/home/ibm-user/shared")
import torch
from scan import RULES

# --- mismos datos que ml/detector.py (misma semilla y mismo orden) ---
random.seed(1)
names = ["x","data","doc","key","k","cfg","token","h","payload","obj"]
fam = {
 "sha1": ["{n} = hashlib.sha1({m}).hexdigest()", "{n} = hashlib.sha1()", "{n} = hashlib.new('sha1', {m})"],
 "md5":  ["{n} = hashlib.md5({m})", "{n} = hashlib.md5({m}).digest()", "{n} = hashlib.new('md5')"],
 "rsa":  ["{n} = RSA.generate({b})", "{n} = rsa.generate_private_key(public_exponent=65537, key_size={b})", "{n} = RSA.import_key({m})"],
 "des":  ["{n} = DES.new({m}, DES.MODE_ECB)", "{n} = DES.new({m}, DES.MODE_CBC)", "cipher = Cipher(algorithms.TripleDES({m}), modes.CBC({n}))"],
 "ecc":  ["{n} = ec.generate_private_key(ec.SECP256R1())", "{n} = ec.generate_private_key(ec.SECP384R1())", "{n} = ECC.generate(curve='P-256')"],
 "tls":  ["ssl_protocols TLSv1 TLSv1.1;", "ssl_protocols TLSv1.1 TLSv1.2;", "ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1)"],
 "rc4":  ["ssl_ciphers RC4:AES128-SHA;", "ssl_ciphers RC4-SHA:HIGH;", "{n} = ARC4.new({m})"],
}
neg = ["{n} = len({m})", "for {n} in range({b}):", "def procesar_{n}({m}):", "return {n} + {m}",
       "print('paciente', {n})", "{n} = json.loads({m})", "import os, sys", "listen 443;",
       "server_name {n}.hospital.pe;", "{n} = open({m}).read()", "if {n} is None: raise ValueError",
       "hashlib.sha256({m}).hexdigest()", "AES.new({m}, AES.MODE_GCM)", "{n} = {m}.strip().lower()"]

def make(tpls, n):
    return [random.choice(tpls).format(n=random.choice(names), m=random.choice(names),
            b=random.choice([512,1024,2048,4096])) for _ in range(n)]

pos_tr = [t for v in fam.values() for t in v[:2]]
pos_te = [v[2] for v in fam.values()]
Xtr = make(pos_tr, 600) + make(neg[:10], 600); ytr = [1]*600 + [0]*600
Xte = make(pos_te, 300) + make(neg[10:], 300); yte = [1]*300 + [0]*300

# --- caracteristicas: n-gramas de caracteres (2 a 4) con hashing, normalizados ---
DIM = 4096
def vec(lines):
    X = torch.zeros(len(lines), DIM)
    for r, line in enumerate(lines):
        s = " " + " ".join(line.lower().split()) + " "
        for n in (2, 3, 4):
            for i in range(len(s) - n + 1):
                X[r, zlib.crc32(s[i:i+n].encode()) % DIM] += 1
    return torch.nn.functional.normalize(X, dim=1)

Xt, Xe = vec(Xtr), vec(Xte)
yt = torch.tensor(ytr, dtype=torch.float32)

def train(seed):
    torch.manual_seed(seed)
    net = torch.nn.Sequential(torch.nn.Linear(DIM, 64), torch.nn.ReLU(),
                              torch.nn.Dropout(0.2), torch.nn.Linear(64, 1))
    opt = torch.optim.Adam(net.parameters(), lr=5e-3, weight_decay=1e-4)
    lossf = torch.nn.BCEWithLogitsLoss()
    for _ in range(40):
        net.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(perm), 64):
            b = perm[i:i+64]
            opt.zero_grad()
            lossf(net(Xt[b]).squeeze(1), yt[b]).backward()
            opt.step()
    net.eval()
    return net

def pr(y, p):
    tp = sum(1 for a, b in zip(y, p) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y, p) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y, p) if a == 1 and b == 0)
    return (tp / (tp + fp) if tp + fp else 0.0), (tp / (tp + fn) if tp + fn else 0.0)

rx = [int(any(re.search(r, l, re.I) for _, r, _, _ in RULES)) for l in Xte]
results = {"solo regex": [pr(yte, rx)]}
nets = [train(s) for s in range(5)]
for thr in (0.5, 0.75):
    solo, comb = [], []
    for net in nets:
        with torch.no_grad():
            p = torch.sigmoid(net(Xe).squeeze(1)).tolist()
        pt = [int(x >= thr) for x in p]
        solo.append(pr(yte, pt))
        comb.append(pr(yte, [int(a or b) for a, b in zip(rx, pt)]))
    results[f"solo PyTorch (umbral {thr})"] = solo
    results[f"regex + PyTorch (umbral {thr})"] = comb

try:  # referencia: scikit-learn con los mismos datos, si esta disponible en el contenedor
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    clf = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)),
                        LogisticRegression(max_iter=2000, C=10)).fit(Xtr, ytr)
    sk = list(clf.predict(Xte))
    results["solo scikit-learn"] = [pr(yte, sk)]
    results["regex + scikit-learn"] = [pr(yte, [int(a or b) for a, b in zip(rx, sk)])]
except Exception as e:
    print("scikit-learn no disponible en el contenedor:", e)

print("Banco de prueba: variantes de sintaxis NO vistas en entrenamiento")
print("(PyTorch: promedio de 5 semillas, entre parentesis minimo-maximo del recall)")
out = {}
for k, v in results.items():
    P = sum(a for a, _ in v) / len(v); R = sum(b for _, b in v) / len(v)
    rng = f"  ({min(b for _, b in v):.2f}-{max(b for _, b in v):.2f})" if len(v) > 1 else ""
    print(f"  {k:<30} precision={P:.2f} recall={R:.2f}{rng}")
    out[k] = {"precision": round(P, 3), "recall": round(R, 3)}

print("\nHospital Demo (red de la semilla 0, umbral 0.5):")
for f in sorted(pathlib.Path("/home/ibm-user/shared/hospital_demo").rglob("*")):
    if f.is_file():
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if line.strip():
                r = any(re.search(x, line, re.I) for _, x, _, _ in RULES)
                with torch.no_grad():
                    pr_t = torch.sigmoid(nets[0](vec([line])).squeeze(1)).item()
                if r or pr_t >= 0.5:
                    print(f"  {f.name}:{n}  regex={'si' if r else 'no'} torch={pr_t:.2f}  {line.strip()[:45]}")
out["torch_version"] = torch.__version__
json.dump(out, open("/home/ibm-user/shared/torch_results.json", "w"), indent=2)
