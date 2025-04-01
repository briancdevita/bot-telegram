import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from jinja2 import Template
import json 
from config import EMAIL_CONFIG


with open ('config.json', 'r') as config_file:
    config = json.load(config_file)


def send_email(to_email, reservation_data):
  sender = EMAIL_CONFIG['user']
  password = EMAIL_CONFIG['password']

  msg = MIMEMultipart()

  msg['From'] = sender
  msg['To'] = to_email
  msg['Subject'] = 'Reservation Confirmation'
    
  with open("index.html", "r", encoding="utf-8") as file:
    template = Template(file.read())


    html_content = template.render(
        contact_name=reservation_data['contact'],
        reservation_data=reservation_data['id'],
        service=reservation_data['service'],
        date=reservation_data['date'],
        time=reservation_data['time'],  
        
    )

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
        print('Email sent')
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

