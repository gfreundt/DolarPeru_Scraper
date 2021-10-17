import csv
import os
import sys
import json
import platform
from threading import local
import matplotlib as plt
import matplotlib.pyplot as plt
from statistics import mean, median
from datetime import datetime as dt
from tqdm import tqdm
from google.cloud import storage


class Definitions:

    def __init__(self):
        self.ROOT_FOLDER = self.select_root_folder()
        self.WORK_FOLDER = os.path.join(self.ROOT_FOLDER, "DolarPeru_Scraper")
        self.DATA_FOLDER = os.path.join(self.ROOT_FOLDER, "DolarPeru_data")
        self.GRAPH_FOLDER = os.path.join(self.DATA_FOLDER, "graphs")
        self.WEBFILE_FOLDER = os.path.join(self.DATA_FOLDER, "webfiles")

        self.DATA_STRUCTURE_FILE = os.path.join(
            self.WORK_FOLDER, "dataStructure.json")
        self.ACTIVE_FILE = os.path.join(self.DATA_FOLDER, "recentQuotes.txt")
        self.MEDIAN_FILE = os.path.join(
            self.DATA_FOLDER, "historicMedians.txt")
        self.WEB_MAIN_FILE = os.path.join(
            self.WEBFILE_FOLDER, "webfile-000.json")
        self.STATS_FILE = os.path.join(self.DATA_FOLDER, "stats.json")
        self.GCLOUD_KEYS = os.path.join(self.ROOT_FOLDER, "gcloud_keys.json")

        self.FIRST_DAILY_RUN = self.first_daily_run()

    def select_root_folder(self):
        '''
        Select path acoording to System running, then select development or production
        '''
        options = {"POWER": ("D:/pythonCode", ""),
                   "LAPTOP": ("C:/pythonCode", "C:/prodCode"),
                   "TABLET": ("C:/pythonCode", "")}
        selection = [options[i]
                     for i in options if i in platform.node().upper()][0]
        if "NOTEST" in sys.argv:
            return selection[1]
        else:
            return selection[0]

    def first_daily_run(self):
        '''
        Check if date in file is different from today's and return True
        '''
        # return True  # ONLY FOR TESTING

        filename = os.path.join(self.WORK_FOLDER, 'first-daily-run.txt')
        with open(filename, mode='r') as file:
            fdr = file.readline()
        current = ts_to_str(dt.now().timestamp(), format="date")
        if fdr != current:
            with open(filename, mode='w') as outfile:
                outfile.write(current)
                print("First Daily Run")
            return True
        else:
            return False


def load_data_from_files():
    with open(active.DATA_STRUCTURE_FILE, "r", encoding="utf-8") as file:
        fintechs = json.load(file)["fintechs"]
    with open(active.ACTIVE_FILE, mode="r") as file:
        data = [i for i in csv.reader(file, delimiter=",")]
    with open(active.MEDIAN_FILE, "r", encoding="utf-8") as file:
        historic = [i for i in csv.reader(file, delimiter=",")]
    return fintechs, data, historic


def analysis1(fintechs, data):
    """
    Creates files with latest quote of each fintech for main pages Compra and Venta. Creates graphs
    """
    # Current time
    time_date = round(dt.now().timestamp(), 0)
    process = [
        {
            "quote": 1,
            "quote_type": "compra",
        },
        {
            "quote": 2,
            "quote_type": "venta",
        },
    ]
    median_file_record = ["000"]  # Useless data to maintain structure
    web_data = {}
    for proc in process:
        # Loads latest quote timestamp
        last_timestamp = data[-1][3]
        # Loads all the datapoints that correspond to latest quote timestamp
        datapoints = {
            i[0]: float(i[proc["quote"]]) for i in data if i[3] == last_timestamp
        }
        # Calculate head data
        meantc = round(mean(datapoints.values()), 4)
        mediantc = round(median(datapoints.values()), 4)
        mejor = (
            round(max(datapoints.values()), 4)
            if proc["quote"] == 1
            else round(min(datapoints.values()), 4)
        )
        # Calculate band edges
        band_min = mediantc * 0.995
        band_max = mediantc * 1.005
        # Create record with new Medians
        median_file_record.append(f"{mediantc:.4f}")
        # Create data for JSON file to be read by Web App

        # Part 1: Add Averages, Best, Count of datapoints and Time/Date
        dump = {
            "head": {
                "mediana": f"{mediantc:.4f}",
                "mejor": f"{mejor:.4f}",
                "promedio": f"{meantc:.4f}",
                "consultas": len(datapoints),
                "fecha": dt.fromtimestamp(float(last_timestamp)).strftime("%d-%m-%Y"),
                "hora": dt.fromtimestamp(float(last_timestamp)).strftime("%H:%M:%S"),
                "timestamp": last_timestamp,
            }
        }
        # Part 2: Add latest quote from all available Fintechs inside band
        details = [
            {
                "image": [i["image"] for i in fintechs if i["id"] == int(f)][0],
                "id": f,
                "value": f"{datapoints[f]:0<6}",
            }
            for f in datapoints.keys()
            if band_min <= datapoints[f] <= band_max
        ]
        details = [
            i
            for i in sorted(
                details, key=lambda x: x["value"], reverse=(proc["quote"] == 1)
            )
            if i["value"] != "0.0000"
        ]
        dump.update({"incluidos": details})
        # Part 3: Add latest quote from all available Fintechs outside band
        details = [
            {
                "image": [i["image"] for i in fintechs if i["id"] == int(f)][0],
                "id": f,
                "value": f"{datapoints[f]:0<6}",
            }
            for f in datapoints.keys()
            if not (band_min <= datapoints[f] <= band_max)
        ]
        dump.update({"excluidos": details})
        web_data.update({proc["quote_type"]: dump})

    median_file_record.append(time_date)

    # Save files
    with open(active.MEDIAN_FILE, mode="a", newline="") as csv_file:
        csv.writer(csv_file, delimiter=",").writerow(median_file_record)
    with open(active.WEB_MAIN_FILE, mode="w", newline="") as json_file:
        json.dump(web_data, json_file, indent=2)

    # Generate graphs
    midnight = dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    with open(active.MEDIAN_FILE, mode="r") as file:
        dpoints = [i for i in csv.reader(file, delimiter=",")]

    for proc in process:
        points = [
            (i[proc["quote"]], i[3]) for i in dpoints
        ]  # select compra/venta and timestamp
        create_intraday_graph(
            points, 0, midnight, filename=f"graph-000-{proc['quote_type']}-intraday.png"
        )
        if active.FIRST_DAILY_RUN:
            # Last 7 days Graph
            create_7day_graph(
                points, 0, midnight, filename=f"graph-000-{proc['quote_type']}-7days.png"
            )
            # Last 100 days Graph
            create_100day_graph(
                points, 0, midnight, filename=f"graph-000-{proc['quote_type']}-100days.png"
            )


def analysis2(fintechs, data, historic):
    """
    Creates individual web file for each fintech and corresponding graph.
    """
    for file in os.listdir(active.GRAPH_FOLDER):
        if active.FIRST_DAILY_RUN or "intraday" in file:
            os.remove(os.path.join(active.GRAPH_FOLDER, file))
    midnight = dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    for f in tqdm(fintechs):
        if f["online"]:
            # Generate web file
            id = f"{f['id']:03d}"
            dpoints = [i for i in data if i[0] == id]
            if dpoints:
                info = {
                    "datos": {
                        "id": id,
                        "name": f["name"],
                        "link": f["link"],
                        "image": f["image"],
                        "contacto": f["contacto"],
                        "registro_SBS": f["registro_SBS"],
                        "bancos": f["bancos"],
                        "RUC": f["RUC"],
                        "App_iOS": f["App_iOS"],
                        "App_Android": f["App_Android"],
                    }
                }
                # Insert most recent quote
                vigente = [
                    {
                        "compra": dpoints[-1][1],
                        "venta": dpoints[-1][2],
                        "hora": ts_to_str(ts=dpoints[-1][3], format="time"),
                        "fecha": ts_to_str(ts=dpoints[-1][3], format="date"),
                        "timestamp": dpoints[-1][3],
                    }
                ]
                # insert up to last 50 records
                historicas = [
                    {
                        "compra": dpoints[-pos][1],
                        "venta": dpoints[-pos][2],
                        "hora": ts_to_str(ts=dpoints[-pos][3], format="time"),
                        "fecha": ts_to_str(ts=dpoints[-pos][3], format="date"),
                        "timestamp": dpoints[-pos][3],
                    }
                    for pos in range(2, min(len(dpoints), 50))
                ]

                info.update(
                    {"cotizaciones": {"vigente": vigente, "historicas": historicas}}
                )
                filename = os.path.join(
                    active.WEBFILE_FOLDER, "webfile-" + id + ".json")
                with open(filename, mode="w", newline="") as json_file:
                    json.dump(info, json_file, indent=2)
                # Generate graphs
                process = [
                    {
                        "quote": 1,
                        "quote_type": "compra",
                    },
                    {
                        "quote": 2,
                        "quote_type": "venta",
                    },
                ]
                for proc in process:
                    points = [
                        (i[proc["quote"]], i[3]) for i in dpoints
                    ]  # select compra/venta and timestamp
                    mpoints = [
                        (i[proc["quote"]], i[3]) for i in historic
                    ]
                    create_intraday_graph(
                        points,
                        mpoints,
                        midnight,
                        filename=f"graph-{id}-{proc['quote_type']}-intraday.png"
                    )
                    if active.FIRST_DAILY_RUN:
                        create_7day_graph(
                            points,
                            mpoints,
                            midnight,
                            filename=f"graph-{id}-{proc['quote_type']}-7days.png"
                        )
                        create_100day_graph(
                            points,
                            mpoints,
                            midnight,
                            filename=f"graph-{id}-{proc['quote_type']}-100days.png"
                        )


def analysis3(fintechs, data):
    """
    Creates file with run statistics.
    """
    OK_SYMBOL = u'\u220e'
    TS_COUNT = 100
    ts = dt.now().timestamp()
    meta = {
        "timestamp": int(ts),
        "time": ts_to_str(ts=ts, format="time"),
        "date": ts_to_str(ts=ts, format="date"),
    }

    # create list of last 100 timestamps (newer to older)
    ts_list = list(
        sorted(set([i[-1] for i in data])))[-TS_COUNT:]
    activity = {"scraper_count": TS_COUNT, "scraper_headings": ts_list}
    scraper = []
    for fintech in fintechs:
        id = f'{fintech["id"]:03d}'
        ts_fintech = [i[-1] for i in data if i[0] == id]
        latest = [OK_SYMBOL if i in ts_fintech else " " for i in ts_list[::-1]]
        rate = latest.count(OK_SYMBOL) / TS_COUNT
        success = f'{rate:.0%}'

        scraper.append(
            {
                "id": id,
                "name": fintech["name"],
                "success": success,
                "color": "bad" if rate < 0.8 else "good",
                "latest": latest,
            }
        )
    final_json = {"meta": meta, "activity": activity,
                  "scraper_results": scraper}

    with open(active.STATS_FILE, mode="w") as outfile:
        outfile.write(json.dumps(final_json, indent=4))


def create_intraday_graph(dpoints, mpoints, midnight, filename):
    # Fintech data points that meet criteria
    data = [(float(i[0]), float(i[1]))
            for i in dpoints if float(i[1]) > midnight]
    x = [(i[1] - midnight) / 3600 for i in data]
    y = [i[0] for i in data]
    # Median data points that meet criteria
    if mpoints:
        data = [(float(i[0]), float(i[1]))
                for i in mpoints if float(i[1]) > midnight]
        x1 = [(i[1] - midnight) / 3600 for i in data]
        y1 = [i[0] for i in data]
    else:
        x1, y1 = 0, 0

    if y:
        min_axis_y = round(min(y) - 0.02, 2)
        max_axis_y = round(max(y) + 0.03, 2)
        xticks = (range(7, 21), range(7, 21))
        yticks = [
            i / 1000 for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 10)
        ]
        graph(x, y, x1, y1, xticks, yticks, filename=filename, rotation=0)


def create_7day_graph(dpoints, mpoints, midnight, filename):
    # Fintech data points that meet criteria
    data = [
        (float(i[0]), float(i[1]))
        for i in dpoints
        if (midnight - 24 * 3600 * 7) <= float(i[1]) <= midnight
    ]
    x = [(i[1] - midnight) / 3600 / 24 for i in data]
    y = [i[0] for i in data]
    # Median data points that meet criteria
    if mpoints:
        data = [
            (float(i[0]), float(i[1]))
            for i in mpoints
            if (midnight - 24 * 3600 * 7) <= float(i[1]) <= midnight
        ]
        y1 = [i[0] for i in data]
        x1 = [(i[1] - midnight) / 3600 / 24 for i in data]
    else:
        x1, y1 = 0, 0

    if y:
        min_axis_y = round(min(y) - 0.02, 2)
        max_axis_y = round(max(y) + 0.03, 2)
        days_week = ["Dom", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab"] * 2
        xt = (
            [days_week[i + dt.today().weekday() + 1] for i in range(-7, 1)],
            [i for i in range(-7, 1)],
        )
        yt = [
            round(i / 1000, 2)
            for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 10)
        ]
        graph(x, y, x1, y1, xt, yt, filename=filename, rotation=0)


def create_100day_graph(dpoints, mpoints, midnight, filename):
    # Fintech data points that meet criteria
    data = [
        (float(i[0]), float(i[1]))
        for i in dpoints
        if (midnight - 24 * 3600 * 100) <= float(i[1]) <= midnight
    ]
    x = [(i[1] - midnight) / 3600 / 24 for i in data]
    y = [i[0] for i in data]
    # Median data points that meet criteria
    if mpoints:
        data = [
            (float(i[0]), float(i[1]))
            for i in mpoints
            if (midnight - 24 * 3600 * 100) <= float(i[1]) <= midnight
        ]
        x1 = [(i[1] - midnight) / 3600 / 24 for i in data]
        y1 = [i[0] for i in data]
    else:
        x1, y1 = 0, 0

    if y:
        min_axis_y = round(min(y) - 0.04, 2)
        max_axis_y = round(max(y) + 0.05, 2)
        xticks = ([i for i in range(-100, 1, 10)],
                  [i for i in range(-100, 1, 10)])
        yticks = [
            round(i / 1000, 2)
            for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 20)
        ]
        graph(x, y, x1, y1, xticks, yticks, filename=filename, rotation=90)


def graph(x, y, x1, y1, xt, yt, filename, rotation):
    plt.rcParams["figure.figsize"] = (4, 2.5)
    ax = plt.gca()
    if y1:
        plt.plot(x1, y1, color="aquamarine", label="Mediana del Mercado")
        ax.legend(loc="lower right")
    plt.plot(x, y)
    ax.set_facecolor("#F5F1F5")
    ax.spines["bottom"].set_color("#DFD8DF")
    ax.spines["top"].set_color("#DFD8DF")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("#DFD8DF")
    plt.tick_params(axis="both", length=0)
    plt.xticks(xt[1], xt[0], color="#606060", fontsize=8, rotation=rotation)
    plt.yticks(yt, color="#606060", fontsize=8)
    plt.grid(color="#DFD8DF")
    plt.savefig(
        os.path.join(active.GRAPH_FOLDER, filename),
        pad_inches=0,
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()


def ts_to_str(ts, format):
    ts = float(ts)
    if format == "time":
        return dt.strftime(dt.fromtimestamp(ts), "%H:%M:%S")
    elif format == "date":
        return dt.strftime(dt.fromtimestamp(ts), "%Y-%m-%d")


def upload_to_gcloud_bucket():
    print("Upload to Bucket")
    bucket_path = "data-bucket-gft"  # test bucket_path = 'data-bucket-gft-devops'
    client = storage.Client.from_service_account_json(
        json_credentials_path=active.GCLOUD_KEYS
    )
    bucket = client.get_bucket(bucket_path)

    local_paths = [os.path.join(i, j) for i in (
        active.DATA_FOLDER, active.WEBFILE_FOLDER, active.GRAPH_FOLDER) for j in os.listdir(i) if os.path.isfile(os.path.join(i, j)) if not "txt" in j]

    # Only update intraday graphs and web json files if not first run
    local_paths = [
        i for i in local_paths if not "days" in i] if not active.FIRST_DAILY_RUN else local_paths

    for local_path in local_paths:
        gcloud_path = local_path[13:].replace("\\", "/")
        object_name_in_gcs_bucket = bucket.blob(gcloud_path)
        object_name_in_gcs_bucket.cache_control = "no-store"
        object_name_in_gcs_bucket.upload_from_filename(local_path)


def backup_to_gdrive():
    print("Backup to GDrive")
    local_paths = [os.path.join(i, j) for i in (
        active.DATA_FOLDER, active.WEBFILE_FOLDER, active.GRAPH_FOLDER) for j in os.listdir(i) if os.path.isfile(os.path.join(i, j)) if "txt" in j]
    # TODO: finish!


def main(UPLOAD):
    global active
    active = Definitions()
    fintechs, data, historic = load_data_from_files()
    analysis2(fintechs, data, historic)
    analysis1(fintechs, data)
    analysis3(fintechs, data)
    if UPLOAD:
        upload_to_gcloud_bucket()
        backup_to_gdrive()


if __name__ == "__main__":
    main(UPLOAD=False)
