import os
import datetime
import configparser
import smtplib
import ssl
from email.message import EmailMessage

today_str = datetime.date.today().strftime("%Y%m%d")
php_error_log_file_name = "php_error.log." + today_str
php_error_log_path = "/data/web/e49159/log/" + php_error_log_file_name
history_log_path = os.path.join(os.path.dirname(__file__), 'history.log')

log_text = 'No log text available'
error_message = None
is_healthy = True
try:
    with open(php_error_log_path) as file:
        log_text = file.read()
        if log_text != '':
            is_healthy = False
            error_message = 'PHP errors found'
except FileNotFoundError as error:
    error_message = error
except IOError as error:
    error_message = error
except Exception as error:
    error_message = error

with open(history_log_path, 'a') as file:
    line = datetime.datetime.now().isoformat() + " " + php_error_log_file_name + " Error: " + str(error_message)
    print(line)
    file.write(line + "\n")

if is_healthy:
    quit()

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

to_email = config['email']['admin_email']
msg = EmailMessage()
msg['Subject'] = str(error_message) + ": " + php_error_log_file_name
msg['From'] = config['email']['from_name'] + " <" + config['email']['from_email'] + ">"
msg['To'] = to_email
msg.set_content(log_text)
try:
    context = ssl.create_default_context()
    with smtplib.SMTP(config['email']['smtp_host'], config['email']['smtp_port']) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(config['email']['smtp_user'], config['email']['smtp_pass'])
        server.send_message(msg)
        print('Email sent to "' + to_email + '"')
except Exception as error:
    print(error)
    print('Email could NOT be sent to "' + to_email + '"')
