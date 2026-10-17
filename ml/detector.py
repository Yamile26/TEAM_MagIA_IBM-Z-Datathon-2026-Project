import re, random, pathlib, sys
sys.path.insert(0, "scanner")
from scan import RULES
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import precision_score, recall_score

random.seed(1)
names = ["x","data","doc","key","k","cfg","token","h","payload","obj"]
# 3 variantes por familia: las 2 primeras entrenan, la 3a (sintaxis nueva) solo prueba
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

clf = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4)),
                    LogisticRegression(max_iter=2000, C=10))
clf.fit(Xtr, ytr)
ml = list(clf.predict(Xte))
rx = [int(any(re.search(r, l, re.I) for _, r, _, _ in RULES)) for l in Xte]
both = [int(a or b) for a, b in zip(ml, rx)]

print("Banco de prueba: variantes de sintaxis NO vistas en entrenamiento")
for name, p in [("solo regex", rx), ("solo ML", ml), ("regex + ML", both)]:
    print(f"  {name:<11} precision={precision_score(yte,p):.2f} recall={recall_score(yte,p):.2f}")

print("\nHospital Demo, lineas marcadas por regex o ML:")
for f in sorted(pathlib.Path("lab/hospital_demo").rglob("*")):
    if f.is_file():
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if line.strip():
                r = any(re.search(x, line, re.I) for _, x, _, _ in RULES)
                m = clf.predict([line])[0] == 1
                if r or m:
                    print(f"  {f.name}:{n}  regex={'si' if r else 'no'} ml={'si' if m else 'no'}  {line.strip()[:50]}")
