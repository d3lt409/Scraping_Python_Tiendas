import smtplib,ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys
sys.path.append(".")
from src.security.security import PASSWORD,EMAIL

with open("recipents.txt","r") as re:
    RECIPENT = [val.strip() for val in re.read().split("\n") if len(val)>5]



def send_email(place_name:str, values:dict):
    subject = place_name.upper()
    with open("src/templates/send_email.html") as fp:
        body = fp.read()
    body = body.replace("{ place }", place_name)
    body = body.replace("{ cantidad }", str(values["Cantidad"]))
    body = body.replace("{ cantidad_elementos }", str(values["Cantidad elementos"]))
    body = body.replace("{ cantidad_total }", str(values["Cantidad"]+values["Cantidad elementos"]))
    sender_email = EMAIL
    password = PASSWORD
    print(password)

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(RECIPENT)
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "html"))

    text = message.as_string()

    # Log in to server using secure context and send email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, RECIPENT, text)


def erorr_msg(place_name:str,error):
    subject = f"ERROR {place_name.upper()}"
    body = f"""Estimados, buenos días,
    
    Se generó un error al tratar de generar los datos para la tienda {place_name}.
    El error:
        - {error}
    Correspondiente a esta fecha.\n\nCordial Saludo."""
    sender_email = EMAIL
    password = PASSWORD

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(RECIPENT)
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    text = message.as_string()

    # Log in to server using secure context and send email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, ",".join(RECIPENT), text)
        