import base64

from Crypto.Cipher import AES

from .cache import memoized


class Crypt(object):
    default_secret = 'sixteenlengthstr'

    def __init__(self, secret=None):
        self.secret = secret or self.default_secret
        self.aes = AES.new(secret, AES.MODE_ECB)

    @memoized
    def encrypt(self, val):
        val = unicode(val).encode('utf-8')
        return base64.urlsafe_b64encode(self.aes.encrypt(val.ljust(
            ((len(val) - 1) / 16 + 1) * 16)))

    @memoized
    def decrypt(self, val):
        return self.aes.decrypt(base64.urlsafe_b64decode(str(val))).decode(
            'utf-8').strip()


_crypt = Crypt()

encrypt = _crypt.encrypt
decrypt = _crypt.decrypt
