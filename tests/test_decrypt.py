#!/usr/bin/env python
import daco2ego

def test_decrypt():
    key = "a1a2a3a4a5a6a7a8a9aa"
    iv  = "b1b2b3b4b5b6b7b8b9bb"
    file = "test_data.enc.gz"
    plaintext = daco2ego.decrypt_file(file, key, iv)
    expected = None
    with open("test_data","rb") as f:
         expected = f.read()
    assert expected is not None
    #print(f"plaintext='{plaintext}'")
    #print(f"expected='{expected}'")
    assert plaintext == expected 

if __name__ == "__main__":
    test_decrypt()
