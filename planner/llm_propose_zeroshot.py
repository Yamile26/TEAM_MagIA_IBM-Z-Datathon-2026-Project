import json, os, re, time
from llama_cpp import Llama

SHARED = "/home/ibm-user/shared"
MODEL = "/home/ibm-user/granite-4.0-h-350m-base-be.f16.gguf"
REPEATS, CANDS, TEMP = 10, 3, 0.7

rows = json.load(open(f"{SHARED}/ranking_ml.json"))
# Solo metadatos: nunca codigo ni snippets
meta = [{"algorithm": r["algorithm"], "location": f"{os.path.basename(r['file'])}:{r['line']}",
         "data_life": r["data_life"], "quantum": r["quantum_vulnerable"], "weak": r["weak_today"]}
        for r in rows]

llm = Llama(model_path=MODEL, n_ctx=2048, n_threads=os.cpu_count() or 2, verbose=False)

def gen(prompt, max_tokens, temp, stop):
    o = llm(prompt, max_tokens=max_tokens, temperature=temp, stop=stop)
    return o["choices"][0]["text"].strip()

HEAD = ("Choose the TLS 1.3 key exchange groups so the server is safe against future quantum computers. Answer with one line.\n\n")

t0 = time.time()
assets = []
for m in meta:
    if not m["quantum"]:
        continue
    kind = "RSA key" if m["algorithm"] == "RSA" else "ECDSA key"
    prompt = HEAD + f"Asset: {kind}, data kept {m['data_life']} years, internet-facing\nGROUPS:"
    reps = [[gen(prompt, 24, TEMP, ["\n"]) for _ in range(CANDS)] for _ in range(REPEATS)]
    assets.append({"algorithm": m["algorithm"], "location": m["location"], "repeats": reps})
    print(m["location"], "listo", flush=True)

weak = [m for m in meta if m["weak"]]
q = [m for m in meta if m["quantum"]]
facts = (f"{len(meta)} cryptographic findings in total. {len(weak)} are broken today "
         f"({', '.join(sorted({m['algorithm'] for m in weak}))}). {len(q)} rely on RSA or ECDSA, "
         f"which quantum computers are expected to break. "
         f"Most urgent: {meta[0]['algorithm']} in {meta[0]['location']}.")
sp = ("Write a two-sentence executive summary for a hospital IT director. "
      f"Use only the facts given.\n\nFacts: {facts}\nSummary:")
text = gen(sp, 90, 0.2, ["\n\n", "Facts:"])
numbers_ok = set(re.findall(r"\d+", text)) <= set(re.findall(r"\d+", facts))

json.dump({"model": os.path.basename(MODEL), "seconds": round(time.time() - t0, 1),
           "assets": assets, "summary": {"facts": facts, "text": text, "numbers_ok": numbers_ok}},
          open(f"{SHARED}/proposals_zeroshot.json", "w"), indent=2, ensure_ascii=False)
print("proposals.json listo en", round(time.time() - t0), "s")
