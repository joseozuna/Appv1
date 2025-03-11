from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import hashlib


class CifradoAES:
    def __init__(self, clave_secreta="clave_predeterminada"):
        # Convertir la clave a bytes si es una cadena
        if isinstance(clave_secreta, str):
            clave_secreta = clave_secreta.encode()

        # Crear una clave de 32 bytes (256 bits) usando SHA-256
        self.clave = hashlib.sha256(clave_secreta).digest()

    def cifrar(self, datos):
        """
        Cifra datos usando AES-256 en modo CBC

        Args:
            datos: Datos a cifrar (str o bytes)

        Returns:
            str: Datos cifrados en formato base64 (IV + datos cifrados)
        """
        # Convertir a bytes si es una cadena
        if isinstance(datos, str):
            datos = datos.encode()

        # Generar un vector de inicialización aleatorio
        iv = get_random_bytes(AES.block_size)

        # Crear el objeto de cifrado
        cipher = AES.new(self.clave, AES.MODE_CBC, iv)

        # Cifrar los datos (se debe aplicar padding)
        datos_cifrados = cipher.encrypt(pad(datos, AES.block_size))

        # Concatenar IV + datos cifrados y codificar en base64
        resultado = base64.b64encode(iv + datos_cifrados).decode('utf-8')

        return resultado

    def descifrar(self, datos_cifrados):
        """
        Descifra datos cifrados con AES-256 en modo CBC

        Args:
            datos_cifrados: Datos cifrados en formato base64 (str)

        Returns:
            bytes o str: Datos descifrados (bytes para archivos, str para texto)
        """
        # Decodificar de base64
        datos_raw = base64.b64decode(datos_cifrados)

        # Separar el IV (los primeros 16 bytes) y los datos cifrados
        iv = datos_raw[:AES.block_size]
        datos_cifrados_raw = datos_raw[AES.block_size:]

        # Crear el objeto de cifrado
        cipher = AES.new(self.clave, AES.MODE_CBC, iv)

        # Descifrar los datos y eliminar el padding
        datos_descifrados = unpad(cipher.decrypt(datos_cifrados_raw), AES.block_size)

        return datos_descifrados

    def cifrar_texto(self, texto):
        """
        Cifra texto y devuelve una cadena
        """
        return self.cifrar(texto)

    def descifrar_texto(self, texto_cifrado):
        """
        Descifra texto y devuelve una cadena
        """
        datos_descifrados = self.descifrar(texto_cifrado)
        return datos_descifrados.decode('utf-8')

    def cifrar_archivo(self, ruta_archivo):
        """
        Cifra un archivo completo

        Args:
            ruta_archivo: Ruta al archivo a cifrar

        Returns:
            bytes: Datos cifrados en formato bytes
        """
        with open(ruta_archivo, 'rb') as f:
            datos = f.read()

        return self.cifrar(datos)

    def descifrar_archivo(self, datos_cifrados, ruta_salida):
        """
        Descifra datos y los guarda en un archivo

        Args:
            datos_cifrados: Datos cifrados en formato base64
            ruta_salida: Ruta donde guardar el archivo descifrado
        """
        datos_descifrados = self.descifrar(datos_cifrados)

        with open(ruta_salida, 'wb') as f:
            f.write(datos_descifrados)