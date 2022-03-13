import os

def chrome_version():
    output = os.popen('reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version').read()
    output = "".join([i for i in output[74:78] if i.isdigit()])
    return int(output)

def chromedriver_version():
    output = os.popen('chromedriver.exe -v').read()
    output = "".join([i for i in output[13:16] if i.isdigit()])
    return int(output)

def alarm():
    print("alarm!")

chrome = chrome_version()
driver = chromedriver_version()

if chrome != driver:
    alarm()


