# erase
import csv, json, os, shutil
from datetime import datetime as dt


def fromprod():
    for f in ("AVG_Venta.txt", "AVG_Compra.txt", "TDC_Vault.txt"):
        shutil.copyfile(
            os.path.join("\prodCode", "DolarPeru_data", f),
            os.path.join("\pythonCode", "DolarPeru_data", f),
        )


def vault():
    with open("TDC_Vault.txt", "r", encoding="utf-8") as file:
        data = [i for i in csv.reader(file)]

    with open("dataStructure.json", "r", encoding="utf-8") as file:
        fintechs = json.load(file)["fintechs"]

    ind = {i["link"]: f'{i["id"]:03d}' for i in fintechs}
    final = []
    for f in data:
        if f[0] == "https://cuantoestaeldolar.pe/":
            continue
        record = [
            ind[f[0]],
            f[3],
            f[1],
            dt.strptime(f[2], "%Y-%m-%d %H:%M:%S").timestamp()
        ]
        final.append(record)

    print(f"Records: {len(final)}")

    with open("historicQuotes.txt", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        _ = [writer.writerow(i) for i in final]

    with open("recentQuotes.txt", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        _ = [writer.writerow(i) for i in final[-100000:]]


def avg(file1="AVG_Venta.txt", file2="AVG_Compra.txt"):
    with open(file1, "r", encoding="utf-8") as file:
        venta = [i for i in csv.reader(file)]
    with open(file2, "r", encoding="utf-8") as file:
        compra = [i for i in csv.reader(file)]
    final = []
    for line1 in venta:
        for line2 in compra:
            if line1[1] == line2[1]:
                final.append(
                    [
                        "000",
                        line2[0],
                        line1[0],
                        dt.strptime(line1[1], "%Y-%m-%d %H:%M:%S").timestamp(),
                    ]
                )
                break

    with open("historicMedians.txt", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        _ = [writer.writerow(i) for i in final]


os.chdir("d:/pythonCode/DolarPeru_data")
fromprod()
vault()
avg()
