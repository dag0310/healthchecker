import os
import datetime
import configparser
import smtplib
import ssl
from email.message import EmailMessage


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

config_parts = []
config_parts.append(config['general']['error_log_filename_prefix'])
has_date_format = 'error_log_filename_date_format' in config['general'] and config['general']['error_log_filename_date_format'] != ''
if has_date_format:
    config_parts.append(datetime.date.today().strftime(config['general']['error_log_filename_date_format']))
config_parts.append(config['general']['error_log_filename_suffix'])

error_log_filepath = config['general']['error_log_path'] + "".join(config_parts)

log_text = 'No log text available.'
message = 'Healthy'
is_healthy = True
try:
    with open(error_log_filepath) as file:
        log_text = file.read()
        allowlist_passed = True
        for log_text_line in log_text.split("\n"):
            if log_text_line.strip() == '':
                continue
            if 'allowlist' not in config['general']:
                allowlist_passed = False
                break
            line_safe = False
            for allowlist_string in config['general']['allowlist'].split("\n"):
                if allowlist_string in log_text_line:
                    line_safe = True
                    break
            if not line_safe:
                allowlist_passed = False
                break
        if not allowlist_passed:
            message = 'Error found in line: ' + log_text_line
            is_healthy = False
except FileNotFoundError as error:
    if has_date_format:
        pass  # Healthy
    else:
        message = 'FileNotFoundError: ' + str(error)
        is_healthy = False
except IOError as error:
    message = 'IOError: ' + str(error)
    is_healthy = False
except Exception as error:
    message = 'Exception: ' + str(error)
    is_healthy = False

with open(os.path.join(os.path.dirname(__file__), 'history.log'), 'a') as file:
    line = datetime.datetime.now().isoformat() + " " + message
    print(line)
    file.write(line + "\n")

if is_healthy:
    quit()

to_email = config['email']['to_email']
msg = EmailMessage()
msg['Subject'] = "[" + config['email']['subject_prefix'] + "] " + message
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
