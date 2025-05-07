import utilities

import hashlib
import zlib
import base64
import urllib.parse
from pathlib import Path
from Crypto.Hash import RIPEMD160


def generate_hashes(data):
    # Dictionary to store all hash results
    hashes = {
        'MD5': hashlib.md5(data.encode()).hexdigest(),
        'SHA1': hashlib.sha1(data.encode()).hexdigest(),
        'SHA256': hashlib.sha256(data.encode()).hexdigest(),
        'SHA224': hashlib.sha224(data.encode()).hexdigest(),
        'SHA384': hashlib.sha384(data.encode()).hexdigest(),
        'SHA512': hashlib.sha512(data.encode()).hexdigest(),
        'SHA3-224': hashlib.sha3_224(data.encode()).hexdigest(),
        'SHA3-256': hashlib.sha3_256(data.encode()).hexdigest(),
        'SHA3-384': hashlib.sha3_384(data.encode()).hexdigest(),
        'SHA3-512': hashlib.sha3_512(data.encode()).hexdigest(),
    }
    # RIPEMD-160 using pycryptodome
    h = RIPEMD160.new()
    h.update(data.encode())
    hashes['RIPEMD-160'] = h.hexdigest()
    return hashes

def generate_encodings(data):
    # Dictionary to store all encoding results
    encoded_data = {
        'Base16': base64.b16encode(data.encode()).decode(),
        'Base32': base64.b32encode(data.encode()).decode(),
        'Base64': base64.b64encode(data.encode()).decode(),
        'URL encoding': urllib.parse.quote(data),
        'Entity encoding': urllib.parse.quote_plus(data),
        'Deflate': base64.b64encode(zlib.compress(data.encode())).decode(),
        'Zlib': base64.b64encode(zlib.compress(data.encode(), level=9)).decode(),
        'Gzip': base64.b64encode(zlib.compress(data.encode(), level=9)).decode()
    }
    return encoded_data

def main():
    input = {
        "fname" :  "Jenna",
        "lname" : "distefano",
        "gender": "female",
        "DOB" : "11/01/1994",
        "email": "jennadistef94@gmail.com",
        "safePass": "Js123456!!",
        "password": "Js123456",
        "address" : "838 Broadway, New York, NY 10003, USA",
        "phoneNumber" : "934100094",
        "cardnumber": "377935351010675",
        "card_number2": "5171690451823249",
        "SSN" : "882529187"
    }

    algos = {}
    for key, value in input.items():
        algos[key] = {}
        algos[key]['raw_data'] = value

        # hashes
        hashes = generate_hashes(value)
        for hash_type, hash_value in hashes.items():
            algos[key][hash_type] = hash_value
        # encodings
        encodings = generate_encodings(value)
        for encoding_type, encoding_value in encodings.items():
            algos[key][encoding_type] = encoding_value

    hashes_path = Path('analyze/data/algos.json')
    utilities.write_json(hashes_path, algos)
        

if __name__ == "__main__":
    main()
