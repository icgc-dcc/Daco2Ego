#!/usr/bin/env python
from aes import decrypt_file

def test_decrypt_file():
    key = "a1a2a3a4a5a6a7a8a9aa"
    iv  = "b1b2b3b4b5b6b7b8b9bb"
    file = "tests/test_data.enc.gz"
    plaintext = decrypt_file(file, key, iv)
    expected = None
    with open("tests/daco.csv","rb") as f:
         expected = f.read()
    assert expected is not None
    #print(f"plaintext='{plaintext}'")
    #print(f"expected='{expected}'")
    assert plaintext == expected 
if __name__ == "__main__":
    test_decrypt_file()
