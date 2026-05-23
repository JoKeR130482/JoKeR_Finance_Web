from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import os


class EncryptionService:
    """Сервис шифрования AES-256-GCM"""
    
    def __init__(self, password_hash: str, salt: str = "joker-finance-salt"):
        """
        Инициализация сервиса шифрования
        
        :param password_hash: Хеш пароля пользователя (Argon2)
        :param salt: Соль для деривации ключа
        """
        self.salt = salt.encode()
        self.key = self._derive_key(password_hash)
        self.aesgcm = AESGCM(self.key)
    
    def _derive_key(self, password_hash: str) -> bytes:
        """Деривация 256-битного ключа из хеша пароля"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password_hash.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """
        Шифрование строки
        
        :param plaintext: Исходная строка
        :return: Base64-encoded зашифрованная строка (nonce + ciphertext + tag)
        """
        nonce = os.urandom(12)  # 96-bit nonce для GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        # nonce (12) + ciphertext + tag (16)
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Дешифрование строки
        
        :param encrypted_data: Base64-encoded зашифрованная строка
        :return: Расшифрованная строка
        """
        try:
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            nonce = data[:12]
            ciphertext = data[12:]
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


def get_encryption_service(password_hash: str, salt: str = "joker-finance-salt") -> EncryptionService:
    """Фабричная функция для создания сервиса шифрования"""
    return EncryptionService(password_hash, salt)
