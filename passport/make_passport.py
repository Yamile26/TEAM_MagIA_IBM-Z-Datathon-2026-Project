import json, os, datetime

has_cbom = os.path.exists("cbom.json")
has_plan = os.path.exists("ranking.json")
has_migration = os.path.exists("migration_verified.flag")  # lo crearemos al migrar TLS

level = 1
if has_cbom: level = 2
if has_cbom and has_plan: level = 3
if level == 3 and has_migration: level = 4

ranking = json.load(open("ranking.json")) if has_plan else []
passport = {
    "institution": "Hospital Regional Demo (ficticio)",
    "readiness_level": level,
    "note": "Nivel definido por el equipo, no es certificacion legal ni estandar oficial",
    "assets_found": len(ranking),
    "top_urgent": [{"algorithm": r["algorithm"], "file": r["file"], "urgency": r["urgency"]} for r in ranking[:3]],
    "issued": datetime.datetime.now(datetime.UTC).isoformat(),
    "signature_algorithm": "ML-DSA-65",
}
json.dump(passport, open("passport/passport.json", "w"), indent=2)
print("Pasaporte nivel", level)
