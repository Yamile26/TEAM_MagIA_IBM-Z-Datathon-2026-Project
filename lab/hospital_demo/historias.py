import hashlib
from Crypto.PublicKey import RSA
from Crypto.Cipher import DES

key = RSA.generate(2048)  # protege historias clinicas
def firmar(doc):
    return hashlib.sha1(doc).hexdigest()
cipher = DES.new(b"8bytekey", DES.MODE_ECB)
