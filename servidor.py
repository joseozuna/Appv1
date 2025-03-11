import socket
import threading
import datetime


class Servidor:
    def __init__(self):
        self.clientes = {}  # Diccionario para almacenar {nombre_usuario: socket}
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', 9999))
        self.server.listen(5)
        print("\n" + "="*80)
        print("🔒 Servidor Chat (con soporte de cifrado) iniciado en 0.0.0.0:9999")
        print("="*80)
        print("⚠️  MONITOR DE TRÁFICO CIFRADO - SOLO PARA DEMOSTRACIÓN")
        print("="*80)
        print("Esperando conexiones...")
        self.iniciar()

    def timestamp(self):
        """Retorna un timestamp para los mensajes de consola"""
        return datetime.datetime.now().strftime("%H:%M:%S")

    def manejar_cliente(self, cliente, addr):
        """Maneja la conexión con un cliente."""
        usuario = None
        try:
            # Recibir nombre de usuario
            usuario = cliente.recv(1024).decode()
            print(f"\n[{self.timestamp()}] 👤 Nuevo usuario conectado: {usuario} desde {addr}")

            # Registrar cliente
            self.clientes[usuario] = cliente
            self.actualizar_lista()

            # Ciclo principal de recepción de mensajes
            while True:
                try:
                    # Aumentamos el tamaño del buffer para mensajes cifrados
                    data = cliente.recv(4096).decode()
                    if not data:
                        break

                    # Procesar según el tipo de mensaje
                    if ':' in data:
                        partes = data.split(':', 2)
                        tipo = partes[0]

                        if tipo == 'MENSAJE' and len(partes) >= 3:
                            destino = partes[1]
                            mensaje_cifrado = partes[2]
                            print(f"\n[{self.timestamp()}] 📨 MENSAJE PRIVADO CIFRADO")
                            print(f"   De: {usuario} → Para: {destino}")
                            print(f"   Contenido cifrado: {mensaje_cifrado}")
                            print(f"   (El servidor no puede descifrar el contenido)")
                            self.enviar_mensaje_privado(usuario, destino, mensaje_cifrado)

                        elif tipo == 'GRUPO' and len(partes) >= 2:
                            mensaje_cifrado = partes[1]
                            print(f"\n[{self.timestamp()}] 📢 MENSAJE GRUPAL CIFRADO")
                            print(f"   De: {usuario} → Para: TODOS")
                            print(f"   Contenido cifrado: {mensaje_cifrado}")
                            print(f"   (El servidor no puede descifrar el contenido)")
                            self.enviar_mensaje_grupo(usuario, mensaje_cifrado)

                        elif tipo == 'ARCHIVO' and len(partes) >= 3:
                            destino = partes[1]
                            info = partes[2]
                            if ';' in info:
                                nombre, tamano = info.split(';')
                                print(f"\n[{self.timestamp()}] 📎 ARCHIVO CIFRADO")
                                print(f"   De: {usuario} → Para: {destino}")
                                print(f"   Nombre: {nombre}, Tamaño: {tamano} bytes")
                                print(f"   (El servidor no puede descifrar el contenido)")
                                self.reenviar_archivo(usuario, destino, nombre, int(tamano), cliente)

                except socket.error:
                    break
                except Exception as e:
                    print(f"\n[{self.timestamp()}] ❌ Error procesando mensaje de {usuario}: {e}")

        except Exception as e:
            print(f"\n[{self.timestamp()}] ❌ Error en la conexión con {addr}: {e}")
        finally:
            # Limpiar cuando el cliente se desconecta
            if usuario in self.clientes:
                print(f"\n[{self.timestamp()}] 👋 Usuario desconectado: {usuario}")
                del self.clientes[usuario]
                cliente.close()
                self.actualizar_lista()

    def enviar_mensaje_privado(self, remitente, destino, mensaje):
        """Envía un mensaje privado de un usuario a otro."""
        if destino in self.clientes:
            try:
                # Aumentamos el tamaño del buffer para mensajes cifrados
                self.clientes[destino].send(f"[PRIVADO] {remitente}: {mensaje}".encode())
                print(f"   ✅ Mensaje reenviado exitosamente a {destino}")
            except Exception as e:
                print(f"\n[{self.timestamp()}] ❌ Error enviando mensaje a {destino}: {e}")
                del self.clientes[destino]
                self.actualizar_lista()

    def enviar_mensaje_grupo(self, remitente, mensaje):
        """Envía un mensaje a todos los usuarios excepto al remitente."""
        receptores = []
        for usuario, cliente in list(self.clientes.items()):
            if usuario != remitente:
                try:
                    # Aumentamos el tamaño del buffer para mensajes cifrados
                    cliente.send(f"[GRUPO] {remitente}: {mensaje}".encode())
                    receptores.append(usuario)
                except Exception as e:
                    print(f"\n[{self.timestamp()}] ❌ Error enviando mensaje de grupo a {usuario}: {e}")
                    del self.clientes[usuario]
                    self.actualizar_lista()
        
        if receptores:
            print(f"   ✅ Mensaje reenviado a {len(receptores)} usuarios: {', '.join(receptores)}")
        else:
            print(f"   ⚠️ No hay otros usuarios conectados para recibir el mensaje")

    def reenviar_archivo(self, remitente, destino, nombre, tamano, cliente_origen):
        """Reenvía un archivo cifrado de un usuario a otro o al grupo."""
        if destino == "GRUPO":
            # Enviar a todos excepto al remitente
            receptores = []
            for usuario, cliente in list(self.clientes.items()):
                if usuario != remitente:
                    try:
                        # Enviar encabezado
                        header = f"ARCHIVO:{remitente}:{nombre}:{tamano}".encode()
                        cliente.send(header)

                        # Leer y reenviar datos cifrados
                        bytes_restantes = tamano
                        buffer = bytearray()

                        while bytes_restantes > 0:
                            # Leer solo si el buffer está vacío
                            if not buffer:
                                chunk = cliente_origen.recv(min(4096, bytes_restantes))
                                if not chunk:
                                    break
                                buffer.extend(chunk)

                            # Enviar desde el buffer
                            bytes_enviados = cliente.send(buffer)
                            buffer = buffer[bytes_enviados:]
                            bytes_restantes -= bytes_enviados
                        
                        receptores.append(usuario)

                    except Exception as e:
                        print(f"\n[{self.timestamp()}] ❌ Error enviando archivo cifrado a {usuario}: {e}")
                        del self.clientes[usuario]
                        self.actualizar_lista()
            
            if receptores:
                print(f"   ✅ Archivo reenviado a {len(receptores)} usuarios: {', '.join(receptores)}")
            else:
                print(f"   ⚠️ No hay otros usuarios conectados para recibir el archivo")
                
        elif destino in self.clientes:
            try:
                # Enviar encabezado
                header = f"ARCHIVO:{remitente}:{nombre}:{tamano}".encode()
                self.clientes[destino].send(header)

                # Leer y reenviar datos cifrados
                bytes_restantes = tamano
                while bytes_restantes > 0:
                    chunk = cliente_origen.recv(min(4096, bytes_restantes))
                    if not chunk:
                        break
                    self.clientes[destino].send(chunk)
                    bytes_restantes -= len(chunk)

                print(f"   ✅ Archivo reenviado exitosamente a {destino}")
            except Exception as e:
                print(f"\n[{self.timestamp()}] ❌ Error enviando archivo cifrado a {destino}: {e}")
                del self.clientes[destino]
                self.actualizar_lista()

    def actualizar_lista(self):
        """Actualiza la lista de contactos conectados en todos los clientes."""
        lista = ','.join(self.clientes.keys())
        print(f"\n[{self.timestamp()}] 📋 Actualizando lista de contactos: {lista}")

        for usuario, cliente in list(self.clientes.items()):
            try:
                cliente.send(f"LISTA:{lista}".encode())
            except Exception as e:
                print(f"\n[{self.timestamp()}] ❌ Error actualizando lista para {usuario}: {e}")
                del self.clientes[usuario]
                # No llamamos a actualizar_lista de nuevo para evitar recursión

    def iniciar(self):
        """Inicia el servidor y acepta conexiones."""
        while True:
            try:
                cliente, addr = self.server.accept()
                threading.Thread(target=self.manejar_cliente, args=(cliente, addr)).start()
            except Exception as e:
                print(f"\n[{self.timestamp()}] ❌ Error aceptando conexión: {e}")


if __name__ == "__main__":
    Servidor()