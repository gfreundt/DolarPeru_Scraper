import csv, os, json
import matplotlib as plt
import matplotlib.pyplot as plt
from statistics import mean, median
from datetime import datetime as dt, timedelta as delta


def analysis1(fintechs, data):
    """
    Creates files with latest quote of each fintech for main pages Compra and Venta. Creates graphs
    """
    # Current time
    time_date = dt.now().timestamp()
    process = [
        {
            "quote": 1,
            "quote_type": "venta",
            "avg_filename": AVG_COMPRA_FILE,
            "web_filename": WEB_COMPRA_FILE,
        },
        {
            "quote": 2,
            "quote_type": "compra",
            "avg_filename": AVG_VENTA_FILE,
            "web_filename": WEB_VENTA_FILE,
        },
    ]
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
        # Append "AVG" Text File with new Median
        item = [f"{mediantc:.4f}", time_date]
        with open(proc["avg_filename"], mode="a", newline="") as file:
            csv.writer(file, delimiter=",").writerow(item)
        # Create JSON File for web app
        # Part 1: Add Averages, Best, Count of datapoints and Time/Date
        dump = {
            "head": {
                "mediana": f"{mediantc:.4f}",
                "mejor": f"{mejor:.4f}",
                "promedio": f"{meantc:.4f}",
                "consultas": len(datapoints),
                "timestamp": last_timestamp,
            }
        }
        # Part 2: Add latest quote from all available Fintechs
        details = [
            {
                "image": [i["image"] for i in fintechs if i["id"] == int(f)][0],
                "name": f,
                "value": f"{datapoints[f]:0<6}",
            }
            for f in datapoints.keys() 
        ]
        details = [
            i
            for i in sorted(
                details, key=lambda x: x["value"], reverse=(proc["quote"] == 1)
            )
            if i["value"] != "0.0000"
        ]
        dump.update({"details": details})
        web_data.update({proc['quote_type']:dump})
        '''
        # Generate graphs
        with open(proc["avg_filename"], mode="r") as file:
            dpoints = [i for i in csv.reader(file, delimiter=",")]
        midnight = (
            dt.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        )
        # Intraday Graph
        create_intraday_graph(
            dpoints, midnight, filename=f"{proc['quote_type']}-intraday.png"
        )
        if first_daily_run():
            # Last 7 days Graph
            create_7day_graph(
                dpoints, midnight, filename=f"{proc['quote_type']}-last7days.png"
            )
            # Last 30 days Graph
            create_90day_graph(
                dpoints, midnight, filename=f"{proc['quote_type']}-last90days.png"
            )
        '''
    # Save file
    with open('WEB_000.json', mode="w", newline="") as json_file:
        json.dump(web_data, json_file, indent=2)

        # Backup data to Google Drive
        # if "NOTEST" in active.switches and "NOBACK" not in active.switches:
        # backup_to_gdrive()


def analysis2(fintechs, data):
    """
    Creates individual web files for each fintech and its corresponding graph. Creates stats file.
    """
    for f in fintechs:
        if f["online"]:
            # Generate web file
            id = f"{f['id']:03d}"
            print(id)
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
                    create_90day_graph(
                        dpoints, midnight, filename=f"{id}-last30days.png"
                    )

    # Create stats file
    meta = {"date": data[-1][3][:10], "time": data[-1][3][11:]}
    results = []
    times = sorted(set([i[2] for i in data]))
    for t in list(times)[-2:]:
        results.append(
            {t: [{i[0]: {"Compra": i[3], "Venta": i[1]} for i in data if t == i[2]}]}
        )
    final_json = {"meta": meta, "results": results}
    with open(STATS_FILE, mode="w") as outfile:
        outfile.write(json.dumps(final_json))


def create_intraday_graph(dpoints, midnight, filename):
    data_avg_today = [
        (float(i[0]), dt.strptime(i[1], "%Y-%m-%d %H:%M:%S"))
        for i in dpoints
        if dt.strptime(i[1], "%Y-%m-%d %H:%M:%S").date() == dt.today().date()
    ]

    x = [(i[1].timestamp() - midnight) / 3600 for i in data_avg_today]
    y = [i[0] for i in data_avg_today]
    if y:
        min_axis_y = round(min(y) - 0.05, 2)
        max_axis_y = round(max(y) + 0.05, 2)
        xticks = (range(7, 21), range(7, 21))
        yticks = [
            i / 1000 for i in range(int(min_axis_y * 1000), int(max_axis_y * 1000), 10)
        ]
        graph(x, y, xticks, yticks, filename=filename, rotation=0)


def create_7day_graph(dpoints, midnight, filename):
    data_7days = [
        (float(i[0]), dt.strptime(i[1], "%Y-%m-%d %H:%M:%S"))
        for i in dpoints
        if delta(days=1)
        <= dt.today().date() - dt.strptime(i[1], "%Y-%m-%d %H:%M:%S").date()
        <= delta(days=7)
    ]

    x = [(i[1].timestamp() - midnight) / 3600 / 24 for i in data_7days]
    y = [i[0] for i in data_7days]
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


def create_90day_graph(dpoints, midnight, filename):
    data = [
        (float(i[0]), dt.strptime(i[1], "%Y-%m-%d %H:%M:%S"))
        for i in dpoints
        if delta(days=1)
        <= dt.today().date() - dt.strptime(i[1], "%Y-%m-%d %H:%M:%S").date()
        <= delta(days=90)
    ]
    x = [(i[1].timestamp() - midnight) / 3600 / 24 for i in data]
    y = [i[0] for i in data]
    
    if y:
        min_axis_y = round(min(y) - 0.05, 2)
        max_axis_y = round(max(y) + 0.05, 2)
        xticks = ([i for i in range(-90, 1, 10)], [i for i in range(-90, 1, 10)])
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
        os.path.join("C:/pythonCode/DolarPeru_data/", filename),
        pad_inches=0,
        bbox_inches="tight",
        transparent=True,
    )
    plt.close()


def first_daily_run():
    return True
    # ONLY FOR TESTING
    if dt.now().hour <= 7 and dt.now().minute < 15:
        return True


DATA_STRUCTURE_FILE = "data_structure.json"
ACTIVE_FILE = "TDC.txt"
AVG_VENTA_FILE = "AVG_Venta.txt"
AVG_COMPRA_FILE = "AVG_Compra.txt"
WEB_VENTA_FILE = "WEB_Venta.json"
WEB_COMPRA_FILE = "WEB_Compra.json"
STATS_FILE = "stats.json"


os.chdir(r"C:\pythonCode\DolarPeru_data")

with open(ACTIVE_FILE, mode="r") as file:
    data = [i for i in csv.reader(file, delimiter=",")]
with open(DATA_STRUCTURE_FILE, "r", encoding="utf-8") as file:
    fintechs = json.load(file)["fintechs"]

analysis1(fintechs, data)
# analysis2(fintechs, data)
