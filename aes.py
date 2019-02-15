import gzip

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

aes_bitsize = 128
aes_blocksize = int(aes_bitsize / 8)
aes_mode = AES.MODE_CBC


# AES doesnt specify how to pad variable length keys or initialization
# vectors.
# However, openSSL pads the key or value with trailing \0 bytes, so we
# do that, too, since we have to decrypt from openSSL.
def decrypt(data, key, iv):
    def pad(hex_str):
        padding = aes_blocksize - int(len(hex_str) / 2)
        return bytes.fromhex(hex_str + "00" * padding)

    aes = AES.new(pad(key), aes_mode, pad(iv))

    return unpad(aes.decrypt(bytes(data)), aes_blocksize)


def read_gzip(name):
    with gzip.open(name) as f:
        data = f.read()
    return data


def decrypt_file(aes_file, key, iv):
    try:
        return decrypt(read_gzip(aes_file), key, iv)
    except Exception as e:
        raise RuntimeError(f"Unable to decrypt file {aes_file}", e)
