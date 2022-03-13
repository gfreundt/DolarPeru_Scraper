import os
import yagmail


def send_gmail(sender, to_list, subject, body, attach):
    yag = yagmail.SMTP(sender)
    for to in to_list:
        yag.send(to=to, subject=subject, contents=body, attachments=attach)


def chrome_version():
    output = os.popen(
        'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
    ).read()
    output = "".join([i for i in output[74:78] if i.isdigit()])
    return int(output)


def chromedriver_version():
    output = os.popen("chromedriver.exe -v").read()
    output = "".join([i for i in output[13:16] if i.isdigit()])
    return int(output)


def alarm():
    sender = "gfreundt@gmail.com"
    send_to_list = ["gfreundt@losportales.com.pe", "gfreundt@gmail.com"]
    subject = "ALERT: CHROME VERSION MISMATCH"
    files_to_send = []
    text_to_send = "DolarPeru_Scraper"
    send_gmail(
        sender, send_to_list, subject=subject, body=text_to_send, attach=files_to_send
    )


chrome = chrome_version()
driver = chromedriver_version()
driver = 90 ## Only for testing!!

if chrome != driver:
    alarm()
