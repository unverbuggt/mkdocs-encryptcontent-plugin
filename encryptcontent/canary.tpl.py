import json
import base64
from Crypto.Hash import SHA512
from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa
from urllib.request import urlopen

publickey = """{{ public_key }}"""

signature_url = '{{ signature_url }}'

urls_to_verify = {{ urls_to_verify }}

def __verify_url__(url, signature, verifier):
    h = SHA512.new()
    with urlopen(url) as response:
        h.update(response.read())
    try:
        verifier.verify(h, signature)
        return True
    except ValueError:
        return False

verifier = eddsa.new(ECC.import_key(publickey), 'rfc8032')

print("NOTE: Checking of generated pages while 'mkdocs serve' will fail, because they are modified with the livereload script")

try:
    with urlopen(signature_url) as response:
        signatures = json.loads(response.read())
        for url in urls_to_verify:
            if url not in signatures.keys():
                print(url + ": MISSING!") # signature_url modified or just need to recreate canary script?
            else:
                if __verify_url__(url, base64.b64decode(signatures[url]), verifier):
                    print(url + ": ok")
                else:
                    print(url + ": FAILED!") # file modified!
except:
    print("Couldn't download signatures!")