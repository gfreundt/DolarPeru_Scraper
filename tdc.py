import os
import sys
import platform
import csv
import json
import time
import matplotlib.pyplot as plt
import matplotlib as mpl
from datetime import datetime as dt, timedelta as delta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as WebDriverOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from statistics import mean, median
import threading
from google.cloud import storage
import bench


# Switches:	NOTEST = work with production data
# 			DAILY-NOW = force once-a-day updates
# 			ANALYSIS-ONLY = skip scraping and only perform data analysis
# 			UPLOAD = upload to Google Cloud Storage


class Basics:
    def __init__(self):

        self.good, self.bad = 0, 0

        self.switches = [i.upper() for i in sys.argv]

        sys_root_path = self.which_system()
        sys_main_path = os.path.join(sys_root_path, "DolarPeru_Scraper")
        sys_data_path = os.path.join(sys_root_path, "DolarPeru_data")
        self.DATA_PATH = sys_data_path

        if "Linux" in platform.system():
            self.CHROMEDRIVER = os.path.join("/usr/bin", "chromedriver")
        elif "Windows" in platform.system():
            self.CHROMEDRIVER = os.path.join(sys_main_path, "chromedriver.exe")
        else:
            print("Cannot Determine System Type")
            quit()

        self.DATA_STRUCTURE_FILE = os.path.join(
            sys_main_path, "dataStructure.json")
        self.GCLOUD_KEYS = os.path.join(sys_root_path, "gcloud_keys.json")
        self.LAST_USE_FILE = os.path.join(sys_data_path, "last_use.txt")
        self.VAULT_FILE = os.path.join(sys_data_path, "historicQuotes.txt")
        self.ACTIVE_FILE = os.path.join(sys_data_path, "TDC.txt")
        self.AVG_FILE = os.path.join(sys_data_path, "historicMedians.txt")
        self.timestamp = int(dt.now().timestamp())
        self.results = []
        self.dashboard = []
        self.bench = bench.main("https://cuantoestaeldolar.pe")
        with open(self.DATA_STRUCTURE_FILE, "r", encoding="utf-8") as file:
            self.fintechs = json.load(file)["fintechs"]

    def which_system(self):
        if "NOTEST" in self.switches:
            systems = [
                {"name": "power", "root_path": r"D:\prodCode"},
                {"name": "laptop", "root_path": r"C:\prodCode"},
                {"name": "desktop", "root_path": "/home/gabfre/prodCode"},
                {"name": "gft-vps", "root_path": "/root/prodCode"}
            ]
        else:
            systems = [
                {"name": "power", "root_path": r"D:\pythonCode"},
                {"name": "laptop", "root_path": r"C:\pythonCode"},
                {"name": "desktop", "root_path": "/home/gabfre/pythonCode"},
                {"name": "gft-vps", "root_path": "/root/pythonCode"}
            ]

        for system in systems:
            if system["name"] in platform.node():
                return system["root_path"]
        return systems[-1]["root_path"]


def set_options():
    options = WebDriverOptions()
    options.add_argument("--window-size=1440,810")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--silent")
    options.add_argument("--disable-notifications")
    options.add_argument("--incognito")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return options


def get_source(fintech, options, k):
    print(f'Starting: {fintech["id"]} - {fintech["name"]}')
    driver = webdriver.Chrome(
        os.path.join(os.getcwd(), active.CHROMEDRIVER), options=options
    )
    attempts = 1
    while attempts <= 3:
        try:
            driver.get(fintech["url"])
            break
        except:
            print("First Level Exception", fintech["name"])
            attempts += 1
            time.sleep(2)
    info, attempts = [], 1
    for quote in ["compra", "venta"]:
        if fintech[quote]["click"]:
            driver.find_element_by_xpath(fintech[quote]["click_xpath"]).click()
        element_present = EC.visibility_of_element_located(
            (By.XPATH, fintech[quote]["xpath"])
        )
        while attempts <= 2:
            try:
                WebDriverWait(driver, 10).until(element_present)
                time.sleep(fintech["sleep"])
                info.append(
                    extract(
                        driver.find_element_by_xpath(
                            fintech[quote]["xpath"]).text,
                        fintech[quote],
                    )
                )
                break
            except:
                attempts += 1
    driver.quit()
    if info and info[0] != "" and sanity_check(info):
        active.results.append(
            {"ID": f'{fintech["id"]:03d}', "Compra": info[0], "Venta": info[1]}
        )
        active.dashboard.append(
            {"ID": k, "Status": "Add", "Fintech": fintech["name"]})
        active.good += 1
    else:
        ext = fintech["bench"]
        if ext:
            info = (active.bench[ext + "_compra"],
                    active.bench[ext + "_venta"])
            if sanity_check(info):
                active.results.append(
                    {"ID": f'{fintech["id"]:03d}',
                        "Compra": info[0], "Venta": info[1]}
                )
                active.dashboard.append(
                    {"ID": k, "Status": "Add", "Fintech": fintech["name"]}
                )
                active.good += 1
        else:
            active.dashboard.append(
                {"ID": k, "Status": "Skip", "Fintech": fintech["name"]}
            )
        active.bad += 1


def sanity_check(test):
    for i in test:
        if not i:
            return False
        if float(i) < 2.50 or float(i) > 9.50:
            return False
    return True


def clean(text):
    r = ""
    for digit in text.strip():
        if digit.isdigit() or digit == ".":
            r += digit
        else:
            break
    return r


def extract(source, fintech):
    init = 0
    text = source[init + fintech["extract_start"]
        : init + fintech["extract_end"]]
    return clean(text)


def save():
    with open(active.VAULT_FILE, mode="a", encoding="utf-8", newline="\n") as file:
        data = csv.writer(file, delimiter=",")
        for f in active.results:
            data.writerow(
                [f["ID"], f["Compra"], f["Venta"], active.timestamp])


def upload_to_bucket(
    bucket_path="data-bucket-gft",
):  # test bucket_path = 'data-bucket-gft-devops'
    client = storage.Client.from_service_account_json(
        json_credentials_path=active.GCLOUD_KEYS
    )
    bucket = client.get_bucket(bucket_path)
    for file in os.listdir(active.DATA_PATH):
        object_name_in_gcs_bucket = bucket.blob("/DolarPeru_data/" + file)
        object_name_in_gcs_bucket.cache_control = "no-store"
        object_name_in_gcs_bucket.upload_from_filename(
            os.path.join(active.DATA_PATH, file)
        )


def backup_to_gdrive():
    pass


def file_extract_recent(n):
    with open(active.VAULT_FILE, mode="r", encoding="utf-8", newline="\n") as file:
        data1 = [i for i in csv.reader(file, delimiter=",")]
        with open(
            active.ACTIVE_FILE, mode="w", encoding="utf-8", newline="\n"
        ) as file2:
            data2 = csv.writer(file2, delimiter=",")
            for lines in data1[-n:]:
                data2.writerow(lines)


def last_use():
    with open(active.LAST_USE_FILE, "w") as file:
        file.write(str(active.timestamp))


def main():
    if "ANALYSIS-ONLY" not in active.switches:
        options = set_options()
        all_threads = []
        for k, fintech in enumerate(active.fintechs):
            if fintech["online"]:  # and fintech['id'] == 10:
                new_thread = threading.Thread(
                    target=get_source, args=(fintech, options, k)
                )
                all_threads.append(new_thread)
                while (
                    threading.active_count() == 15
                ):  # Infinite loop to limit concurrent threads
                    time.sleep(1)
                new_thread.start()
        _ = [
            i.join() for i in all_threads
        ]  # Ensures all threads end before moving forward
        save()
        #TODO: file_extract_recent(9800)
        print(f"Good: {active.good} | Bad: {active.bad}")
        for d in sorted(active.dashboard, key=lambda i: i["ID"]):
            print(d)
    #TODO: analysis()
    if "UPLOAD" in active.switches:
        upload_to_bucket()


start = dt.now()
active = Basics()
main()
last_use()
print(f"Time: {dt.now()-start}.")
