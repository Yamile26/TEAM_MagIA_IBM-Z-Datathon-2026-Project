#!/bin/bash
cd ~/pasaporte-cuantico && source .venv/bin/activate
export PATH=$HOME/openssl35/bin:$PATH LD_LIBRARY_PATH=$HOME/openssl35/lib64:$HOME/openssl35/lib
scene(){ sleep 4; clear; echo "=== $1 ==="; echo; }
pkill -f "s_server -accept 4433" 2>/dev/null
scene "1. Plataforma"; uname -m; openssl version; openssl list -kem-algorithms | grep -i ml-kem
scene "2. Escaner -> CBOM -> ranking"; python3 scanner/scan.py lab/hospital_demo; python3 cbom/make_cbom.py; python3 risk/mosca.py
scene "3. Modelo XGBoost"; python3 ml/train_risk.py
scene "4. Plan con Granite (resultados guardados) + validador"; python3 -c "import json;d=json.load(open('plan_llm.json'));print('Granite: validas al 1er intento',d['primer_intento'],'de',d['total'],'| tras validar',d['hasta_3'],'de',d['total'])"; python3 planner/plan.py
scene "5. TLS clasico vs hibrido"
(cd tls && openssl s_server -accept 4433 -cert srv.crt -key srv.key -www -tls1_3 -groups X25519MLKEM768:X25519 >/dev/null 2>&1 &) ; sleep 2
echo | openssl s_client -connect localhost:4433 -tls1_3 -groups X25519 2>&1 | grep -E "Temp Key|group"
echo | openssl s_client -connect localhost:4433 -tls1_3 -groups X25519MLKEM768 2>&1 | grep -E "Temp Key|group"
pkill -f "s_server -accept 4433"
scene "6. Pasaporte firmado (ML-DSA-65)"; bash passport/sign.sh
scene "7. Contenedores"; podman ps; docker ps
