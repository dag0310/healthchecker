import os
import datetime
import configparser
import smtplib
import ssl
from email.message import EmailMessage


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

log_text = 'No log text available.'
message = None
is_healthy = None
try:
    with open("/data/web/e49159/log/php_error.log") as file:
        log_text = file.read()
        whitelist_passed = True
        for log_text_line in log_text.split("\n"):
            if log_text_line.strip() == '':
                continue
            if 'whitelist' not in config['general']:
                whitelist_passed = False
                break
            line_safe = False
            for whitelist_string in config['general']['whitelist'].split("\n"):
                if whitelist_string in log_text_line:
                    line_safe = True
                    break
            if not line_safe:
                whitelist_passed = False
                break
        if not whitelist_passed:
            message = 'PHP errors found.'
except FileNotFoundError as error:
    message = 'FileNotFoundError: ' + str(error)
except IOError as error:
    message = 'IOError: ' + str(error)
except Exception as error:
    message = 'Exception: ' + str(error)

if message is None:
    is_healthy = True
    message = 'Healthy'
else:
    is_healthy = False

with open(os.path.join(os.path.dirname(__file__), 'history.log'), 'a') as file:
    line = datetime.datetime.now().isoformat() + " " + message
    print(line)
    file.write(line + "\n")

if is_healthy:
    quit()

to_email = config['email']['to_email']
msg = EmailMessage()
msg['Subject'] = message
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
