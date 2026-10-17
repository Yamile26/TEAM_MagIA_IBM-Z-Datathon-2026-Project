#!/bin/bash
cd ~/pasaporte-cuantico/passport
[ -f key.pem ] || { openssl genpkey -algorithm ML-DSA-65 -out key.pem; openssl pkey -in key.pem -pubout -out pub.pem; }
python3 ../passport/make_passport.py 2>/dev/null || (cd .. && python3 passport/make_passport.py)
openssl pkeyutl -sign -inkey key.pem -rawin -in passport.json -out passport.sig
echo "--- Verificando pasaporte ORIGINAL ---"
openssl pkeyutl -verify -pubin -inkey pub.pem -rawin -in passport.json -sigfile passport.sig
echo "--- Alterando UN caracter ---"
cp passport.json passport_alterado.json
sed -i '0,/Hospital/s//Hospitaz/' passport_alterado.json
openssl pkeyutl -verify -pubin -inkey pub.pem -rawin -in passport_alterado.json -sigfile passport.sig || echo ">>> FIRMA INVALIDA: pasaporte alterado detectado"
