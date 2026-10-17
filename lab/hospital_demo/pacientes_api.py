import hashlib
from cryptography.hazmat.primitives.asymmetric import ec, rsa

priv = ec.generate_private_key(ec.SECP256R1())
rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
token = hashlib.md5(b"sesion").hexdigest()
