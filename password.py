"""
File to work with passwords, encrypt and decrypt them,
create a key and an encrypted password
"""
from cryptography.fernet import Fernet


def generate_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)


def load_key() -> bytes:
    """
    Loads the key from the current directory named `secret.key`
    """
    return open("secret.key", "rb").read()


def encrypt_password(password: str, key: bytes) -> bytes:
    """
    Encrypts the password using the given key
    """
    f = Fernet(key)
    encrypted_password = f.encrypt(password.encode())
    return encrypted_password


def decrypt_password(encrypted_password: bytes, key: bytes) -> str:
    """
    Decrypts the encrypted password using the given key
    """
    f = Fernet(key)
    decrypted_password = f.decrypt(encrypted_password).decode()
    return decrypted_password


if __name__ == "__main__":
    generate_key()
    key = load_key()
    password = ""  # Enter your password
    encrypted_password = encrypt_password(password, key)
    print(f"Encrypted password: {encrypted_password}")
    with open("bot_data/encrypted_password.txt", "wb") as file:
        file.write(encrypted_password)
    decrypted_password = decrypt_password(encrypted_password, key)
    print(f"Decrypted password: {decrypted_password}")
