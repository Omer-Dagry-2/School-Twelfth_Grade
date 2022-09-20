import random


class OTP:
    """ One Time Pad Generator """
    def __init__(self):
        self.old_seed = None
        self.seed = None
        self.otp_bytes = None

    def __iter__(self):
        return self

    def __next__(self):  # , seed):
        """ Calculates A One Time Pad In The Size Of 1 Byte """
        self.seed = random.randint(-999999999999999, 999999999999999)  # random number for the seed
        self.otp_bytes = bin((self.seed ** 2))[2:]  # & 0xff)[2:].rjust(8, "0")  # create the otp (in bytes)
        random_locations = []
        while len(random_locations) != 8:
            random_location = random.randint(0, len(self.otp_bytes) - 1)
            if random_location not in random_locations:
                random_locations.append(random_location)
        self.seed = ""
        for location in random_locations:
            self.seed += self.otp_bytes[location]
        # self.seed = seed
        # self.otp_bytes = bin((self.seed ** 2) & 0xff)[2:].rjust(8, "0")
        self.seed = int(self.seed[2:-2], 2)  # convert to int
        if self.seed != self.old_seed and self.seed != 0:
            self.old_seed = self.seed
            return self.seed
        else:
            return next(self)


def encrypt(msg):
    """
    Encrypts the param msg using one time pad for each letter
    :param msg: the msg to encrypt
    :type msg: str
    """
    encrypted_msg = ""
    keys = []
    otp_generator = OTP()
    for char in msg:
        key = next(otp_generator)
        encrypted_msg += chr(ord(char) ^ key)
        keys.append(key)
    return encrypted_msg, keys


def decrypt(encrypted_msg, keys):
    """
    Decrypts the param encrypted_msg using the param keys
    :param encrypted_msg: the encrypted msg
    :param keys: the keys that the encrypted_msg was encrypted with
    :type encrypted_msg: str
    :type keys: list
    """
    msg = ""
    for char, key in zip(encrypted_msg, keys):
        msg += chr(ord(char) ^ key)
    return msg


def main():
    msg = input("Please Enter The Data To Encrypt: ")
    print("Encrypting '%s'" % msg, end="")
    encrypted_msg, keys = encrypt(msg)
    print(", Result: '%s'" % encrypted_msg)
    print("Encryption Keys:", keys)
    #
    print("Decrypting '%s'" % encrypted_msg, end="")
    msg = decrypt(encrypted_msg, keys)
    print(", Result: '%s'" % msg)


if __name__ == '__main__':
    main()
