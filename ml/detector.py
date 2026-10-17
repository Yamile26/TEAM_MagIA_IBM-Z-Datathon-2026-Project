import random, pathlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.metrics import precision_score, recall_score

random.seed(1)
names = ["x","data","doc","key","k","cfg","token","h","payload","obj"]
pos_t = ["{n} = hashlib.sha1({m}).hexdigest()", "{n} = hashlib.md5({m})",
         "{n} = RSA.generate({b})", "{n} = rsa.generate_private_key(public_exponent=65537, key_size={b})",
         "{n} = DES.new({m}, DES.MODE_ECB)", "{n} = ec.generate_private_key(ec.SECP256R1())",
         "ssl_protocols TLSv1 TLSv1.1;", "ssl_ciphers RC4:AES128-SHA;",
         "{n} = hashlib.new('sha1', {m})", "{n} = hashlib.new('md5')",
         "ALGO = 'RSA'  # {m}", "cipher = Cipher(algorithms.TripleDES({m}), modes.CBC({n}))"]
neg_t = ["{n} = len({m})", "for {n} in range({b}):", "def procesar_{n}({m}):", "return {n} + {m}",
         "print('paciente', {n})", "{n} = json.loads({m})", "import os, sys", "listen 443;",
         "server_name {n}.hospital.pe;", "{n} = open({m}).read()", "if {n} is None: raise ValueError",
         "hashlib.sha256({m}).hexdigest()", "AES.new({m}, AES.MODE_GCM)", "{n} = {m}.strip().lower()"]

def make(tpls, n):
    return [random.choice(tpls).format(n=random.choice(names), m=random.choice(names),
            b=random.choice([512,1024,2048,4096])) for _ in range(n)]

def split_by_template(tpls, k_test):
    random.shuffle(tpls); return tpls[k_test:], tpls[:k_test]

pos_tr, pos_te = split_by_template(pos_t[:], 4)
neg_tr, neg_te = split_by_template(neg_t[:], 4)
Xtr = make(pos_tr, 400) + make(neg_tr, 400); ytr = [1]*400 + [0]*400
Xte = make(pos_te, 200) + make(neg_te, 200); yte = [1]*200 + [0]*200

clf = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4)),
                    LogisticRegression(max_iter=1000))
clf.fit(Xtr, ytr)
pred = clf.predict(Xte)
print(f"Banco con plantillas NO vistas en entrenamiento: "
      f"precision={precision_score(yte,pred):.2f} recall={recall_score(yte,pred):.2f}")

print("\nLineas del Hospital Demo que el modelo marca como cripto:")
for p in pathlib.Path("lab/hospital_demo").rglob("*"):
    if p.is_file():
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if line.strip() and clf.predict([line])[0] == 1:
                print(f"  {p.name}:{n}  {line.strip()}")
