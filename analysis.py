import csv
import os
import json
import matplotlib as plt
import matplotlib.pyplot as plt
from statistics import mean, median
from datetime import datetime as dt
from tqdm import tqdm


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
    with open(MEDIAN_FILE, mode="a", newline="") as csv_file:
        csv.writer(csv_file, delimiter=",").writerow(median_file_record)
    with open(WEB_MAIN_FILE, mode="w", newline="") as json_file:
        json.dump(web_data, json_file, indent=2)

    # Generate graphs
    midnight = dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    with open(MEDIAN_FILE, mode="r") as file:
        dpoints = [i for i in csv.reader(file, delimiter=",")]

    for proc in process:
        points = [
            (i[proc["quote"]], i[3]) for i in dpoints
        ]  # select compra/venta and timestamp
        create_intraday_graph(
            points, midnight, filename=f"graph000-{proc['quote_type']}-intraday.png"
        )
        if first_daily_run():
            # Last 7 days Graph
            create_7day_graph(
                points, midnight, filename=f"graph000-{proc['quote_type']}-7days.png"
            )
            # Last 90 days Graph
            create_100day_graph(
                points, midnight, filename=f"graph000-{proc['quote_type']}-100days.png"
            )

        # Backup data to Google Drive
        # if "NOTEST" in active.switches and "NOBACK" not in active.switches:
        # backup_to_gdrive()


def analysis2(fintechs, data):
    """
    Creates individual web files for each fintech and its corresponding graph.
    """
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
                # insert up to last 50 records
                vigente = [
                    {
                        "compra": dpoints[-1][1],
                        "venta": dpoints[-1][2],
                        "timestamp": dpoints[-1][3],
                    }
                ]
                historicas = [
                    {
                        "compra": dpoints[-pos][1],
                        "venta": dpoints[-pos][2],
                        "timestamp": dpoints[-pos][3],
                    }
                    for pos in range(2, min(len(dpoints), 50))
                ]

                info.update(
                    {"cotizaciones": {"vigente": vigente, "historicas": historicas}}
                )
                filename = "web" + id + ".json"
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

                    create_intraday_graph(
                        points,
                        midnight,
                        filename=f"graph{id}-{proc['quote_type']}-intraday.png",
                    )
                    if first_daily_run():
                        create_7day_graph(
                            points,
                            midnight,
                            filename=f"graph{id}-{proc['quote_type']}-7days.png",
                        )
                        create_100day_graph(
                            points,
                            midnight,
                            filename=f"graph{id}-{proc['quote_type']}-100days.png",
                        )


def analysis3(fintechs, data):
    """
    Creates stats file.
    """
    TS_COUNT = 20
    meta = {
        "timestamp": int(dt.now().timestamp()),
        "time": dt.strftime(dt.now(), "%H:%M:%S"),
        "date": dt.strftime(dt.now(), "%Y-%m-%d"),
    }

    # create list of last 100 timestamps (newer to older)
    ts_list = list(
        sorted(set([i[-1] for i in data]), reverse=True))[-TS_COUNT:]
    activity = {"scraper_count": TS_COUNT}
    scraper = []
    for fintech in fintechs:
        id = f'{fintech["id"]:03d}'
        ts_fintech = [i[-1] for i in data if i[0] == id]
        latest = ["K" if i in ts_fintech else "E" for i in ts_list]
        success = (latest.count("K")) / TS_COUNT

        scraper.append(
            {
                "id": id,
                "name": fintech["name"],
                "success": success,
                "latest": latest,
            }
        )
    final_json = {"meta": meta, "activity": activity,
                  "scraper_results": scraper}

    with open(STATS_FILE, mode="w") as outfile:
        outfile.write(json.dumps(final_json, indent=4))


def create_intraday_graph(dpoints, midnight, filename):
    data = [(float(i[0]), float(i[1]))
            for i in dpoints if float(i[1]) > midnight]
    x = [(i[1] - midnight) / 3600 for i in data]
    y = [i[0] for i in data]
    if y:
        min_axis_y = round(min(y) - 0.05, 2)
        max_axis_y = round(max(y) + 0.05, 2)
        xticks = (range(7, 21), range(7, 21))
        yticks = [
            i / 1000 for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 10)
        ]
        graph(x, y, xticks, yticks, filename=filename, rotation=0)


def create_7day_graph(dpoints, midnight, filename):
    data = [
        (float(i[0]), float(i[1]))
        for i in dpoints
        if (midnight - 24 * 3600 * 7) <= float(i[1]) <= midnight
    ]
    x = [(i[1] - midnight) / 3600 / 24 for i in data]
    y = [i[0] for i in data]
    if y:
        min_axis_y = round(min(y) - 0.05, 2)
        max_axis_y = round(max(y) + 0.05, 2)
        days_week = ["Dom", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab"] * 2
        xt = (
            [days_week[i + dt.today().weekday() + 1] for i in range(-7, 1)],
            [i for i in range(-7, 1)],
        )
        yt = [
            round(i / 1000, 2)
            for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 10)
        ]
        graph(x, y, xt, yt, filename=filename, rotation=0)


def create_100day_graph(dpoints, midnight, filename):
    data = [
        (float(i[0]), float(i[1]))
        for i in dpoints
        if (midnight - 24 * 3600 * 100) <= float(i[1]) <= midnight
    ]

    x = [(i[1] - midnight) / 3600 / 24 for i in data]
    y = [i[0] for i in data]

    if y:
        min_axis_y = round(min(y) - 0.05, 2)
        max_axis_y = round(max(y) + 0.05, 2)
        xticks = ([i for i in range(-100, 1, 10)],
                  [i for i in range(-100, 1, 10)])
        yticks = [
            round(i / 1000, 2)
            for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 20)
        ]
        graph(x, y, xticks, yticks, filename=filename, rotation=90)


def graph(x, y, xt, yt, filename, rotation):
    plt.rcParams["figure.figsize"] = (4, 2.5)
    plt.plot(x, y)
    ax = plt.gca()
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
        os.path.join("D:/pythonCode/DolarPeru_data/", filename),
        pad_inches=0,
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()


def first_daily_run():
    return True  # ONLY FOR TESTING
    if dt.now().hour <= 7 and dt.now().minute < 15:
        return True


DATA_STRUCTURE_FILE = "dataStructure.json"
ACTIVE_FILE = "recentQuotes.txt"
MEDIAN_FILE = "historicMedians.txt"
WEB_MAIN_FILE = "web000.json"
STATS_FILE = "stats.json"


os.chdir(r"D:\pythonCode\DolarPeru_data")

with open(ACTIVE_FILE, mode="r") as file:
    data = [i for i in csv.reader(file, delimiter=",")]
with open(DATA_STRUCTURE_FILE, "r", encoding="utf-8") as file:
    fintechs = json.load(file)["fintechs"]

# analysis1(fintechs, data)
# analysis2(fintechs, data)
analysis3(fintechs, data)
