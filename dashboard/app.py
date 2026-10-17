import json, os
from flask import Flask
app = Flask(__name__)
BASE = os.environ.get("DATA_DIR", os.path.expanduser("~/pasaporte-cuantico"))

def load(p):
    try: return json.load(open(os.path.join(BASE, p)))
    except Exception: return None

@app.route("/")
def index():
    rank = load("ranking_ml.json") or []
    pas = load("passport/passport.json") or {}
    rows = "".join(
        f"<tr><td>{r['ml_score']:.1f}</td><td>{r['algorithm']}</td>"
        f"<td>{r['file'].split('/')[-1]}:{r['line']}</td><td>{r['reason']}</td></tr>"
        for r in rank)
    return f"""<html><body style="font-family:sans-serif;max-width:900px;margin:30px auto">
    <h1>Pasaporte Cuántico</h1>
    <h2>Nivel de preparación: {pas.get('readiness_level','?')} / 5</h2>
    <p><i>{pas.get('note','')}</i></p>
    <p>Firma: {pas.get('signature_algorithm','')} | Emitido: {pas.get('issued','')}</p>
    <h3>Ranking de urgencia (XGBoost)</h3>
    <table border=1 cellpadding=6><tr><th>Score</th><th>Algoritmo</th><th>Ubicación</th><th>Motivo (reglas)</th></tr>{rows}</table>
    </body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
