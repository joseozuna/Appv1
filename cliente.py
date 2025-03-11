import emoji
import socket
import threading
import os
import customtkinter as ctk
from tkinter import filedialog, simpledialog
import base64

# Importar nuestro módulo de cifrado
from cifrado import CifradoAES


class WhatsAppCliente:
    def __init__(self, root):
        self.root = root
        self.root.title(" Chat App(Cifrado)")
        self.root.geometry("800x600")

        # Configuración de CustomTkinter
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # Interfaz de login
        self.mostrar_login()

        # Variables
        self.sock = None
        self.usuario = None
        self.cifrado = None  # Inicializamos el cifrado como None

    def mostrar_login(self):
        # Limpiamos la ventana
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame de login
        frame_login = ctk.CTkFrame(self.root)
        frame_login.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(frame_login, text="Chat Seguro", font=("Segoe UI Emoji", 24)).pack(pady=12, padx=10)

        # Entrada para el nombre de usuario
        ctk.CTkLabel(frame_login, text="Nombre de usuario:").pack(pady=(20, 0))
        self.entry_usuario = ctk.CTkEntry(frame_login, width=200)
        self.entry_usuario.pack(pady=10)

        # Entrada para la clave de cifrado
        ctk.CTkLabel(frame_login, text="Clave de cifrado:").pack(pady=(10, 0))
        self.entry_clave = ctk.CTkEntry(frame_login, width=200, show="*")
        self.entry_clave.pack(pady=10)
        self.entry_clave.insert(0, "clave_predeterminada")  # Clave por defecto

        # Botón para conectar
        ctk.CTkButton(
            frame_login,
            text="Conectar",
            command=self.conectar_servidor,
            fg_color="#128C7E",  # Color de WhatsApp
            hover_color="#075E54"
        ).pack(pady=12)

    def conectar_servidor(self):
        self.usuario = self.entry_usuario.get()
        clave_cifrado = self.entry_clave.get()

        if not self.usuario:
            return

        try:
            # Inicializar el objeto de cifrado con la clave proporcionada
            self.cifrado = CifradoAES(clave_cifrado)

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('localhost', 9999))
            self.sock.send(self.usuario.encode())

            # Si la conexión es exitosa, mostramos la interfaz de chat
            self.crear_interfaz()

            # Hilo de recepción
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
        except Exception as e:
            error_label = ctk.CTkLabel(self.root, text=f"Error de conexión: {e}", text_color="red")
            error_label.pack(pady=10)
            self.root.after(3000, error_label.destroy)

    def crear_interfaz(self):
        # Limpiar la ventana primero
        for widget in self.root.winfo_children():
            widget.destroy()

        # Marco principal que contiene todo
        self.marco_principal = ctk.CTkFrame(self.root)
        self.marco_principal.pack(fill="both", expand=True, padx=10, pady=10)

        # Marco izquierdo para contactos
        marco_izquierdo = ctk.CTkFrame(self.marco_principal, width=200)
        marco_izquierdo.pack(side="left", fill="y", padx=(0, 10))
        marco_izquierdo.pack_propagate(False)

        ctk.CTkLabel(
            marco_izquierdo,
            text="Contactos",
            font=("Segoe UI Emoji", 20)
        ).pack(pady=(10, 5))

        # Indicador de cifrado
        self.lbl_cifrado = ctk.CTkLabel(
            marco_izquierdo,
            text="🔒 Cifrado AES",
            text_color="#128C7E",
            font=("Segoe UI", 14, "bold")
        )
        self.lbl_cifrado.pack(pady=5)

        # Lista de contactos
        self.frame_contactos = ctk.CTkScrollableFrame(marco_izquierdo)
        self.frame_contactos.pack(fill="both", expand=True, padx=5, pady=5)

        self.botones_contactos = []  # Almacenar referencias a los botones de contactos

        # Marco derecho para chat
        marco_derecho = ctk.CTkFrame(self.marco_principal)
        marco_derecho.pack(side="right", fill="both", expand=True)

        # Área de chat
        self.frame_chat = ctk.CTkFrame(marco_derecho)
        self.frame_chat.pack(fill="both", expand=True, padx=5, pady=(5, 10))

        self.txt_chat = ctk.CTkTextbox(
            self.frame_chat,
            wrap="word",
            font=("Roboto", 16)  # Tamaño 16 en lugar del default (14)
        )
        self.txt_chat.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_chat.configure(state="disabled")

        # Entrada de mensajes
        marco_inferior = ctk.CTkFrame(marco_derecho)
        marco_inferior.pack(fill="x", pady=(0, 5))

        self.entry_mensaje = ctk.CTkEntry(marco_inferior, placeholder_text="Escribe un mensaje...")
        self.entry_mensaje.pack(side="left", fill="x", expand=True, padx=(5, 10), pady=5)
        self.entry_mensaje.bind("<Return>", self.enviar_mensaje)

        # Botones
        btn_archivo = ctk.CTkButton(
            marco_inferior,
            text="📎",
            width=40,
            command=self.enviar_archivo,
            fg_color="#128C7E",
            hover_color="#075E54"
        )
        btn_archivo.pack(side="left", padx=(0, 5), pady=5)

        btn_grupo = ctk.CTkButton(
            marco_inferior,
            text="Grupo",
            width=80,
            command=lambda: self.enviar_mensaje(grupo=True),
            fg_color="#128C7E",
            hover_color="#075E54"
        )
        btn_grupo.pack(side="left", padx=(0, 5), pady=5)

        # Botón para cambiar clave de cifrado
        btn_cambiar_clave = ctk.CTkButton(
            marco_inferior,
            text="🔑",
            width=40,
            command=self.cambiar_clave_cifrado,
            fg_color="#128C7E",
            hover_color="#075E54"
        )
        btn_cambiar_clave.pack(side="left", padx=(0, 5), pady=5)

        # Etiqueta de estado
        self.lbl_estado = ctk.CTkLabel(marco_derecho, text="Conectado como: " + self.usuario)
        self.lbl_estado.pack(anchor="w", padx=5)

    def cambiar_clave_cifrado(self):
        """Permite cambiar la clave de cifrado durante la sesión"""
        nueva_clave = simpledialog.askstring("Cambiar Clave", "Ingresa la nueva clave de cifrado:", show='*')
        if nueva_clave:
            self.cifrado = CifradoAES(nueva_clave)
            self.mostrar_mensaje("[Sistema]: Clave de cifrado actualizada")

    def actualizar_contactos(self, contactos):
        """Actualiza la lista de contactos conectados."""
        # Limpiar botones existentes
        for widget in self.frame_contactos.winfo_children():
            widget.destroy()

        self.botones_contactos = []

        # Crear un botón para cada contacto
        for contacto in contactos:
            if contacto != self.usuario:  # No mostramos nuestro propio usuario
                btn = ctk.CTkButton(
                    self.frame_contactos,
                    text=contacto,
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    anchor="w",
                    command=lambda c=contacto: self.seleccionar_contacto(c)
                )
                btn.pack(fill="x", padx=5, pady=2)
                self.botones_contactos.append((contacto, btn))

        # Agregar botón para grupo
        btn_grupo = ctk.CTkButton(
            self.frame_contactos,
            text="💬 Grupo",
            fg_color="#128C7E",
            hover_color="#075E54",
            command=lambda: self.seleccionar_contacto("GRUPO")
        )
        btn_grupo.pack(fill="x", padx=5, pady=(10, 2))
        self.botones_contactos.append(("GRUPO", btn_grupo))

        # Seleccionar el primer contacto o grupo por defecto
        if self.botones_contactos:
            self.seleccionar_contacto(self.botones_contactos[0][0])

    def seleccionar_contacto(self, contacto):
        """Selecciona un contacto y lo marca visualmente."""
        self.contacto_seleccionado = contacto

        # Actualizar visual de los botones
        for c, btn in self.botones_contactos:
            if c == contacto:
                btn.configure(fg_color=("#3a7ebf", "#1f538d"))
            else:
                btn.configure(fg_color="transparent")

    def enviar_mensaje(self, event=None, grupo=False):
        """Envía un mensaje cifrado al destinatario seleccionado o al grupo."""
        mensaje = self.entry_mensaje.get()
        if not mensaje:
            return

        # Convertir códigos de emojis (ej: ":smile:") a caracteres Unicode
        mensaje_con_emojis = emoji.emojize(mensaje, language="alias")

        # Cifrar el mensaje antes de enviarlo
        mensaje_cifrado = self.cifrado.cifrar_texto(mensaje_con_emojis)

        destino = 'GRUPO' if grupo else getattr(self, 'contacto_seleccionado', None)

        if destino:
            if destino == 'GRUPO':
                self.sock.send(f"GRUPO::{mensaje_cifrado}".encode())
            else:
                self.sock.send(f"MENSAJE:{destino}:{mensaje_cifrado}".encode())

            # Mostrar el mensaje en nuestra propia ventana (sin cifrar para nosotros)
            if destino == 'GRUPO':
                self.mostrar_mensaje(f"[TÚ] a [GRUPO]: {mensaje_con_emojis}")
            else:
                self.mostrar_mensaje(f"[TÚ] a {destino}: {mensaje_con_emojis}")

            self.entry_mensaje.delete(0, "end")

    def mostrar_mensaje(self, mensaje):
        """Muestra un mensaje en el área de chat."""
        self.txt_chat.configure(state="normal")
        self.txt_chat.insert("end", mensaje + '\n')
        self.txt_chat.configure(state="disabled")
        self.txt_chat.see("end")

    def enviar_archivo(self):
        """Envía un archivo cifrado al destinatario seleccionado."""
        archivo = filedialog.askopenfilename()
        if not archivo:
            return

        destino = getattr(self, 'contacto_seleccionado', None)
        if not destino:
            self.mostrar_mensaje("[Sistema]: Selecciona un contacto primero")
            return

        nombre = os.path.basename(archivo)

        try:
            # Leer el archivo y cifrarlo
            with open(archivo, 'rb') as f:
                contenido = f.read()

            # Cifrar el contenido completo
            contenido_cifrado = self.cifrado.cifrar(contenido)
            contenido_bytes = contenido_cifrado.encode('utf-8')  # Convertir a bytes para enviar

            # Enviar información del archivo cifrado
            if destino == 'GRUPO':
                self.sock.send(f"ARCHIVO:GRUPO:{nombre};{len(contenido_bytes)}".encode())
            else:
                self.sock.send(f"ARCHIVO:{destino}:{nombre};{len(contenido_bytes)}".encode())

            # Enviar el contenido cifrado
            self.sock.sendall(contenido_bytes)

            # Mostrar confirmación
            if destino == 'GRUPO':
                self.mostrar_mensaje(f"[Sistema]: Archivo '{nombre}' (cifrado) enviado al grupo")
            else:
                self.mostrar_mensaje(f"[Sistema]: Archivo '{nombre}' (cifrado) enviado a {destino}")

        except Exception as e:
            self.mostrar_mensaje(f"[Error]: No se pudo enviar el archivo: {e}")

    def recibir_archivo(self, data):
        """Recibe un archivo cifrado, lo descifra y lo guarda."""
        partes = data.split(':')
        if len(partes) < 4:
            self.mostrar_mensaje("[Error]: Formato de archivo incorrecto")
            return

        _, remitente, nombre, tamano = partes

        # Crear la carpeta si no existe
        carpeta_destino = "archivos_recibidos"
        os.makedirs(carpeta_destino, exist_ok=True)

        # Ruta completa del archivo
        ruta_guardado = os.path.join(carpeta_destino, nombre)

        try:
            # Recibir el archivo cifrado completo
            bytes_restantes = int(tamano)
            contenido_cifrado = bytearray()

            while bytes_restantes > 0:
                chunk = self.sock.recv(min(1024, bytes_restantes))
                if not chunk:
                    break
                contenido_cifrado.extend(chunk)
                bytes_restantes -= len(chunk)

            # Convertir de bytes a string para descifrarlo
            contenido_cifrado_str = contenido_cifrado.decode('utf-8')

            # Descifrar el contenido
            contenido_descifrado = self.cifrado.descifrar(contenido_cifrado_str)

            # Guardar el archivo descifrado
            with open(ruta_guardado, 'wb') as f:
                f.write(contenido_descifrado)

            self.mostrar_mensaje(
                f"[Sistema]: Archivo recibido y descifrado de {remitente}: {os.path.basename(ruta_guardado)}")
        except Exception as e:
            self.mostrar_mensaje(f"[Error]: No se pudo procesar el archivo cifrado: {e}")

    def recibir_mensajes(self):
        """Recibe mensajes del servidor en un hilo separado."""
        while True:
            try:
                data = self.sock.recv(1024).decode()

                if not data:
                    break

                if data.startswith('LISTA:'):
                    contactos = data.split(':')[1].split(',')
                    self.actualizar_contactos(contactos)
                elif data.startswith('ARCHIVO:'):
                    self.recibir_archivo(data)
                elif data.startswith('[PRIVADO]') or data.startswith('[GRUPO]'):
                    # Procesar mensajes cifrados
                    try:
                        # Formato esperado: "[TIPO] remitente: mensaje_cifrado"
                        partes = data.split(':', 1)
                        if len(partes) == 2:
                            prefijo = partes[0]  # "[PRIVADO] remitente" o "[GRUPO] remitente"
                            mensaje_cifrado = partes[1].strip()

                            # Descifrar el mensaje
                            mensaje_descifrado = self.cifrado.descifrar_texto(mensaje_cifrado)

                            # Mostrar el mensaje descifrado
                            self.mostrar_mensaje(f"{prefijo}: {mensaje_descifrado}")
                        else:
                            # Si no podemos separar correctamente, mostramos el mensaje tal cual
                            self.mostrar_mensaje(data)
                    except Exception as e:
                        # En caso de error (posiblemente clave incorrecta), mostrar mensaje cifrado
                        self.mostrar_mensaje(f"{data} [cifrado - no se pudo descifrar]")
                else:
                    self.mostrar_mensaje(data)
            except Exception as e:
                self.mostrar_mensaje(f"[Error]: Conexión perdida: {e}")
                break

        # Si salimos del bucle, la conexión se perdió
        self.mostrar_login()


if __name__ == "__main__":
    root = ctk.CTk()
    app = WhatsAppCliente(root)
    root.mainloop()