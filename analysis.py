import csv, os, json
import matplotlib as plt
import matplotlib.pyplot as plt
from statistics import mean, median
from datetime import datetime as dt, timedelta as delta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as WebDriverOptions
from selenium.webdriver.support.ui import WebDriverWait


def analysis():
    with open(ACTIVE_FILE, mode="r") as file:
        data = [i for i in csv.reader(file, delimiter=",")]

    proc = [
        {
            "quote": 2,
            "avg_filename": AVG_VENTA_FILE,
            "web_filename": WEB_VENTA_FILE,
            "graph_filename": "vta",
        },
        {
            "quote": 4,
            "avg_filename": AVG_COMPRA_FILE,
            "web_filename": WEB_COMPRA_FILE,
            "graph_filename": "compra",
        },
    ]
    for p in proc:
        # Current time
        time_date = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        # Loads latest quote datetime
        quote_time = data[-1][2]
        # Loads all the datapoints that correspond to latest quote datetime
        datapoints = {i[0]: float(i[p["quote"]]) for i in data if i[2] == quote_time}

        # Runs every time
        meantc = round(mean([datapoints[i] for i in datapoints.keys()]), 4)
        mediantc = round(median([datapoints[i] for i in datapoints.keys()]), 4)
        # Append Text File with new Average
        item = [f"{mediantc:.4f}", time_date]
        with open(p["avg_filename"], mode="a", newline="") as file:
            csv.writer(file, delimiter=",").writerow(item)
        # Create Text File for Web
        datax = [
            {
                "image": [i["image"] for i in active.fintechs if i["link"] == f][0],
                "name": f,
                "value": f"{datapoints[f]:0<6}",
            }
            for f in datapoints.keys()
        ]
        with open(web_filename, mode="w", newline="") as json_file:
            if quote == 2:  # Venta
                mejor = round(min([datapoints[i] for i in datapoints.keys()]), 4)
                details = [
                    i
                    for i in sorted(datax, key=lambda x: x["value"])
                    if i["value"] != "0.0000"
                ]
            else:  # Compra
                mejor = round(max([datapoints[i] for i in datapoints.keys()]), 4)
                details = [
                    i
                    for i in sorted(datax, key=lambda x: x["value"], reverse=True)
                    if i["value"] != "0.0000"
                ]
            # Append Averages, Best, Count of datapoints and Time/Date
            dump = {
                "head": {
                    "mediana": f"{mediantc:.4f}",
                    "mejor": f"{mejor:.4f}",
                    "promedio": f"{meantc:.4f}",
                    "consultas": f"{len(datapoints.keys())}",
                    "time": data[-1][2][-8:],
                    "date": data[-1][2][:10],
                }
            }  # tc, cantidad de fintechs, time, date
            # Append latest from each fintech
            dump.update({"details": details})
            json.dump(dump, json_file)
        # Intraday Graph
        with open(avg_filename, mode="r") as file:
            datax = [i for i in csv.reader(file, delimiter=",")]
        data_avg_today = [
            (float(i[0]), dt.strptime(i[1], "%Y-%m-%d %H:%M:%S"))
            for i in datax
            if dt.strptime(i[1], "%Y-%m-%d %H:%M:%S").date() == dt.today().date()
        ]
        datetime_midnight = (
            dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        )
        x = [(i[1].timestamp() - datetime_midnight) / 3600 for i in data_avg_today]
        y = [i[0] for i in data_avg_today]
        mid_axis_y = round((max(y) + min(y)) / 2, 2)
        min_axis_y, max_axis_y = mid_axis_y - 0.05, mid_axis_y + 0.05
        axis = (int(x[0]), 22, min_axis_y, max_axis_y)
        xt = (range(axis[0], axis[1]), range(axis[0], axis[1]))
        yt = [
            i / 1000 for i in range(int(axis[2] * 1000), int(axis[3] * 1000) + 10, 10)
        ]
        graph(x, y, xt, yt, axis=axis, filename=f"intraday-{graph_filename}.png")

        # Update only on first run of the day

        if (
            dt.now().hour <= 7 and dt.now().minute < 15
        ) or "DAILY-NOW" in active.switches:
            # Last 5 days Graph
            data_5days = [
                (float(i[0]), dt.strptime(i[1], "%Y-%m-%d %H:%M:%S"))
                for i in datax
                if delta(days=1)
                <= dt.today().date() - dt.strptime(i[1], "%Y-%m-%d %H:%M:%S").date()
                <= delta(days=5)
            ]
            x = [(i[1].timestamp() - datetime_midnight) / 3600 / 24 for i in data_5days]
            y = [i[0] for i in data_5days]
            mid_axis_y = round((max(y) + min(y)) / 2, 2)
            min_axis_y, max_axis_y = mid_axis_y - 0.075, mid_axis_y + 0.075
            axis = (-5, 0, min_axis_y, max_axis_y)
            days_week = ["Dom", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab"] * 2
            xt = (
                [days_week[i + dt.today().weekday() + 1] for i in range(-5, 1)],
                [i for i in range(-5, 1)],
            )
            yt = [
                round(i / 1000, 2)
                for i in range(int(axis[2] * 1000), int(axis[3] * 1000) + 10, 10)
            ]
            graph(x, y, xt, yt, axis=axis, filename=f"last5days-{graph_filename}.png")
            # Last 30 days Graph
            data_30days = [
                (float(i[0]), dt.strptime(i[1], "%Y-%m-%d %H:%M:%S"))
                for i in datax
                if delta(days=1)
                <= dt.today().date() - dt.strptime(i[1], "%Y-%m-%d %H:%M:%S").date()
                <= delta(days=30)
            ]
            x = [
                (i[1].timestamp() - datetime_midnight) / 3600 / 24 for i in data_30days
            ]
            y = [i[0] for i in data_30days]
            mid_axis_y = round((max(y) + min(y)) / 2, 2)
            min_axis_y, max_axis_y = mid_axis_y - 0.2, mid_axis_y + 0.2
            axis = (-5, 0, min_axis_y, max_axis_y)
            xt = ([i for i in range(-30, 1, 2)], [i for i in range(-30, 1, 2)])
            yt = [
                round(i / 1000, 2)
                for i in range(int(axis[2] * 1000), int(axis[3] * 1000) + 10, 20)
            ]
            graph(x, y, xt, yt, axis=axis, filename=f"last30days-{graph_filename}.png")

            # Backup data to Google Drive
            if "NOTEST" in active.switches and "NOBACK" not in active.switches:
                backup_to_gdrive()


def analysis2(fintechs):
    """Creates individual web files for each fintech and their corresponding graph. Also creates stats file."""
    with open(ACTIVE_FILE, mode="r") as file:
        data = [i for i in csv.reader(file, delimiter=",")]

    # Web file and graph for each online fintech
    for f in fintechs:
        if f["online"]:
            # Generate web file
            id = f"{f['id']:03d}"
            dpoints = [
                (i[4], i[2], i[3]) for i in data if i[0] == id
            ]  # Compra, Venta, Datetime
            if dpoints:
                info = {
                    "datos": {
                        "name": f["name"],
                        "url": f["url"],
                        "image": f["image"],
                        "contacto": f["contacto"],
                        "registro_SBS": f["registro_SBS"],
                        "bancos": f["bancos"],
                    }
                }
                # insert up to last 30 records
                cotizaciones = [
                    {
                        "compra": dpoints[-pos][0],
                        "venta": dpoints[-pos][1],
                        "time": dpoints[-pos][2][0:10],
                        "date": dpoints[-pos][2][11:],
                    }
                    for pos in range(min(len(dpoints), 30))
                ]
                info.update({"cotizaciones": cotizaciones})
                filename = "WEB_" + id + ".json"
                with open(filename, mode="w", encoding="utf-8", newline="") as outfile:
                    outfile.write(json.dumps(info))
                # Generate graphs
                midnight = (
                    dt.now()
                    .replace(hour=0, minute=0, second=0, microsecond=0)
                    .timestamp()
                )
                # Intraday Graph
                create_intraday_graph(dpoints, midnight, filename=f"{id}-intraday.png")
                if first_daily_run():
                    # Last 5 days Graph
                    create_7day_graph(dpoints, midnight, filename=f"{id}-last7days.png")
                    # Last 30 days Graph
                    create_30day_graph(dpoints, midnight, filename=f"{id}-last30days.png")

def create_intraday_graph(dpoints, midnight, filename):
    data_avg_today = [
        (float(i[0]), dt.strptime(i[2], "%Y-%m-%d %H:%M:%S"))
        for i in dpoints
        if dt.strptime(i[2], "%Y-%m-%d %H:%M:%S").date() == dt.today().date()
    ]

    x = [(i[1].timestamp() - midnight) / 3600 for i in data_avg_today]
    y = [i[0] for i in data_avg_today]
    if y:
        mid_axis_y = round((max(y) + min(y)) / 2, 2)
        min_axis_y, max_axis_y = mid_axis_y - 0.05, mid_axis_y + 0.05
        axis = (int(x[0]), 22, min_axis_y, max_axis_y)
        xt = (range(axis[0], axis[1]), range(axis[0], axis[1]))
        yt = [
            i / 1000 for i in range(int(axis[2] * 1000), int(axis[3] * 1000) + 10, 10)
        ]
        graph(x, y, xt, yt, axis=axis, filename=filename)


def create_7day_graph(dpoints, midnight, filename):
    data_7days = [
        (float(i[0]), dt.strptime(i[2], "%Y-%m-%d %H:%M:%S"))
        for i in dpoints
        if delta(days=1)
        <= dt.today().date() - dt.strptime(i[2], "%Y-%m-%d %H:%M:%S").date()
        <= delta(days=7)
    ]
    x = [(i[1].timestamp() - midnight) / 3600 / 24 for i in data_7days]
    y = [i[0] for i in data_7days]
    if y:
        mid_axis_y = round((max(y) + min(y)) / 2, 2)
        min_axis_y, max_axis_y = mid_axis_y - 0.075, mid_axis_y + 0.075
        axis = (-5, 0, min_axis_y, max_axis_y)
        days_week = ["Dom", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab"] * 2
        xt = (
            [days_week[i + dt.today().weekday() + 1] for i in range(-7, 1)],
            [i for i in range(-7, 1)],
        )
        yt = [
            round(i / 1000, 2)
            for i in range(int(axis[2] * 1000), int(axis[3] * 1000) + 10, 10)
        ]
        graph(x, y, xt, yt, axis=axis, filename=filename)


def create_30day_graph(dpoints, midnight, filename):
    data_30days = [
        (float(i[0]), dt.strptime(i[2], "%Y-%m-%d %H:%M:%S"))
        for i in dpoints
        if delta(days=1)
        <= dt.today().date() - dt.strptime(i[2], "%Y-%m-%d %H:%M:%S").date()
        <= delta(days=30)
    ]
    x = [(i[1].timestamp() - midnight) / 3600 / 24 for i in data_30days]
    y = [i[0] for i in data_30days]
    if y:
        mid_axis_y = round((max(y) + min(y)) / 2, 2)
        min_axis_y, max_axis_y = mid_axis_y - 0.2, mid_axis_y + 0.2
        axis = (-5, 0, min_axis_y, max_axis_y)
        xt = ([i for i in range(-30, 1, 2)], [i for i in range(-30, 1, 2)])
        yt = [
            round(i / 1000, 2)
            for i in range(int(axis[2] * 1000), int(axis[3] * 1000) + 10, 20)
        ]
        graph(x, y, xt, yt, axis=axis, filename=filename)


def stats():
    # Stats file
    meta = {"date": data[-1][2][:10], "time": data[-1][2][11:]}
    results = []
    times = sorted(set([i[2] for i in data]))
    for t in list(times)[-2:]:
        results.append(
            {t: [{i[0]: {"Compra": i[3], "Venta": i[1]} for i in data if t == i[2]}]}
        )
    final_json = {"meta": meta, "results": results}
    with open(STATS_FILE, mode="w") as outfile:
        outfile.write(json.dumps(final_json))


def graph(x, y, xt, yt, axis, filename):
    plt.rcParams["figure.figsize"] = (4, 2.5)
    plt.plot(x, y)
    ax = plt.gca()
    ax.set_facecolor("#F5F1F5")
    ax.spines["bottom"].set_color("#DFD8DF")
    ax.spines["top"].set_color("#DFD8DF")
    ax.spines["left"].set_color("white")
    ax.spines["right"].set_color("#DFD8DF")
    plt.tick_params(axis="both", length=0)
    plt.axis(axis)
    plt.xticks(xt[1], xt[0], color="#606060", fontsize=8)
    plt.yticks(yt, color="#606060", fontsize=8)
    plt.grid(color="#DFD8DF")
    plt.savefig(
        os.path.join("C:/pythonCode/DolarPeru_data/", filename),
        pad_inches=0,
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()


def first_daily_run():
    if dt.now().hour <= 7 and dt.now().minute < 15:
        return True


DATA_STRUCTURE_FILE = "data_structure.json"
ACTIVE_FILE = "TDC.txt"
AVG_VENTA_FILE = "AVG_Venta.txt"
AVG_COMPRA_FILE = "AVG_Compra.txt"
WEB_VENTA_FILE = "WEB_Venta.json"
WEB_COMPRA_FILE = "WEB_Compra.json"
STATS_FILE = "stats.json"


os.chdir(r"c:\pythonCode\DolarPeru_data")

with open(DATA_STRUCTURE_FILE, "r", encoding="utf-8") as file:
    fintechs = json.load(file)["fintechs"]

analysis2(fintechs)
