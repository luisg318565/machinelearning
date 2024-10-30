#importamos las librerías necesarias
import requests
from fpdf import FPDF
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Función de verificación de la URL
def verificar_url(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# URL base del servidor de mapas
url2 = "https://www.medellin.gov.co/servidormapas/rest/services/Hosted"

# Función para listar los servicios dentro de la carpeta "Hosted"
def listar_servicios(url):
    try:
        response = requests.get(f"{url}?f=json")
        response.raise_for_status()
        data = response.json()
        if 'services' in data:
            for service in data['services']:
                print(f"Servicio: {service['name']} ({service['type']})")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con el servidor: {e}")
        return None

# Llamar a la función para listar servicios y verificar existencia
data = listar_servicios(url2)
nombres_buscados = [
    "Hosted/CartografiaBase_BN_VectorTile",
    "Hosted/CartografiaBase_VectorTile",
    "Hosted/CartografiaBase_ZER_VectorTile",
    "Hosted/Puntos_Criticos_Accidentalidad_VectorTile",
    "Hosted/VM_Policia_CartografiaBase_VectorTile"
]
verif = []

# Verificar si existen los servicios especificados
if data and 'services' in data:
    for nombre in nombres_buscados:
        existe = any(service['name'] == nombre for service in data['services'])
        verif.append(existe)
        print(f"El servicio con nombre '{nombre}' {'existe' if existe else 'no existe'} en los datos.")
else:
    print("No se pudo obtener la lista de servicios.")

# Clase personalizada que extiende FPDF para agregar fondo y encabezado
class PDFConFondo(FPDF):
    def header(self):
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.set_font("Arial", "I", 10)
        self.cell(0, 10, f"Reporte generado el: {fecha_hora_actual}", 0, 1, "R")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

# Generación del PDF con el estado de los servicios
pdf = PDFConFondo()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Verificar estado del servicio principal
rest = "https://www.medellin.gov.co/servidormapas/rest/services"
rest_valid = verificar_url(rest)
pdf.set_font("Arial", "", 12)
pdf.ln(10)
pdf.cell(200, 10, f"El servicio REST principal está {'arriba' if rest_valid else 'caído'}.", ln=True, align="L")

# Verificar estado de los servicios consultados
pdf.ln(10)
pdf.set_font("Arial", "B", 12)
pdf.cell(200, 10, "Estado de los servicios consultados:", ln=True, align="L")

pdf.set_font("Arial", "", 12)
for i, nombre in enumerate(nombres_buscados):
    estado = "Funcional" if verif[i] else "Caído"
    pdf.cell(200, 10, f"{nombre}: {estado}", ln=True, align="L")

# Guardar el PDF
fecha_hora_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
nombre_archivo = f"reporte_servicios_{fecha_hora_actual}.pdf"
ruta_reporte = r"D:\reportes"
reporte_path = os.path.join(ruta_reporte, nombre_archivo)
pdf.output(reporte_path)
print(f"El reporte ha sido generado y guardado como {nombre_archivo}")

# Envío del PDF por correo electrónico
def enviar_correo(destinatario, asunto, cuerpo, archivo_adjunto):
    remitente = "correo@gmail.com"
    contraseña = "mr"  # Contraseña de aplicación

    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Adjuntar el archivo PDF
    with open(archivo_adjunto, "rb") as adjunto:
        mime_base = MIMEBase('application', 'octet-stream')
        mime_base.set_payload(adjunto.read())
        encoders.encode_base64(mime_base)
        mime_base.add_header('Content-Disposition', f"attachment; filename={os.path.basename(archivo_adjunto)}")
        mensaje.attach(mime_base)

    # Enviar correo
    with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
        servidor.starttls()
        servidor.login(remitente, contraseña)
        servidor.sendmail(remitente, destinatario, mensaje.as_string())

correos = ["email@gmail.com", "email2@yahoo.es"]
asunto = "Reporte de Estado de Servicios"
if rest_valid and all(verif):
    asunto = "Reporte: El servidor de mapas y los servicios están funcionando correctamente"
cuerpo = "Adjunto se encuentra el reporte generado."

# Enviar a todos los correos
for correo in correos:
    enviar_correo(correo, asunto, cuerpo, reporte_path)
    print(f"Reporte enviado exitosamente a {correo}")

print("El reporte ha sido enviado por correo electrónico.")