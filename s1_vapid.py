# (A) REQUIRED MODULES
import base64
import ecdsa 

# (B) GENERATE KEYS
# CREDITS : https://gist.github.com/cjies/cc014d55976db80f610cd94ccb2ab21e
pri = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
pub = pri.get_verifying_key()
keys = {
  "private" : base64.urlsafe_b64encode(pri.to_string()).decode("utf-8").strip("="),
  "public" : base64.urlsafe_b64encode(b"\x04" + pub.to_string()).decode("utf-8").strip("=")
}
print(keys)


##{'private': 'dxD4LuZXtbd5QE3iCYYeiwQlUqkzDqhTXJT-0UDx5RA', 'public': 'BHaAQF-EhBIAA7Wyd7qUgcQl7y0CdJnVR3Cb4myoOnTfv-6_e4ZqFOvDwBgquwvgPeZivYXDCPBJoIFENcI8gxI'}