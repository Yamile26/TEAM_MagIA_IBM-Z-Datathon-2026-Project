import json
findings = json.load(open("findings.json"))
components = []
for i, f in enumerate(findings, 1):
    components.append({
        "type": "cryptographic-asset",
        "bom-ref": f"asset-{i}",
        "name": f["algorithm"],
        "cryptoProperties": {"assetType": "algorithm"},
        "properties": [
            {"name": "quantum_vulnerable", "value": str(f["quantum_vulnerable"])},
            {"name": "weak_today", "value": str(f["weak_today"])},
        ],
        "evidence": {"occurrences": [{"location": f["file"], "line": f["line"]}]},
    })
cbom = {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
        "metadata": {"component": {"type": "application", "name": "Hospital Regional Demo"}},
        "components": components}
json.dump(cbom, open("cbom.json", "w"), indent=2)
print(f"CBOM listo: {len(components)} activos criptograficos -> cbom.json")
