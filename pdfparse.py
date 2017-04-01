# python 3 script to parse the final result of the Tweede Kamerverkiezingen 2017 into csv from the pdf at
# https://www.kiesraad.nl/adviezen-en-publicaties/rapporten/2017/3/proces-verbaal-zitting-kiesraad-uitslag-tweede-kamerverkiezing-2017/getekend-proces-verbaal-zitting-bekendmaking-uitslag-tweede-kamer-22-03-2017
# usage: python pdfparse.py <input pdf> <output csv>
# requirements: pdfquery
# warning: uses a few GB ram when parsing the pdf for the first time
# license: apache v2

from sys import argv, stdout
from pdfquery import PDFQuery
from pdfquery.cache import FileCache
import csv
import re

pdf = PDFQuery(argv[1], parse_tree_cacher=FileCache("/tmp/"))
pdf.load()
# pdf.tree.write(argv[2], pretty_print=True)

def get(p):
        if len(p) != 1:
                return None
        else:
                return p[0]

f = open(argv[2], "wt", newline="")
kiescsv = csv.writer(f)
kiescsv.writerow(["partijnummer", "partij", "volgnummer", "naam", "kieskring", "stemmen"])

kieskringen = {}
for i in [20, 22, 64, 66, 114, 116, 118, 120, 122, 124, 126, 128, 130, 150, 152, 244, 246]:
        kieskringen[i] = [1, 2, 3, 4, 5, 6, 7]
        kieskringen[i+1] = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
# SP
kieskringen[68] = kieskringen[69] = [1, 2, 3, 4]
kieskringen[70] = kieskringen[71] = [5, 6, 7, 8]
kieskringen[72] = kieskringen[73] = [9, 10, 11]
kieskringen[74] = kieskringen[75] = [12, 13, 14, 15, 20]
kieskringen[76] = kieskringen[77] = [16, 17, 18, 19]
# CDA
kieskringen[80] = kieskringen[81] = [2, 5]
kieskringen[86] = kieskringen[87] = [6, 7]
# 50PLUS
kieskringen[134] = kieskringen[135] = [2, 3]
kieskringen[140] = kieskringen[141] = [6, 7]
kieskringen[144] = kieskringen[145] = [9, 10, 11]
kieskringen[146] = kieskringen[147] = [12, 13, 14, 15, 20]
kieskringen[148] = kieskringen[149] = [16, 17, 18, 19]
# nieuwe wegen
kieskringen[248] = [1, 2, 3, 4, 5, 6, 7]
kieskringen[249] = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20] # no 19
# burger beweging & vrijzinnige partij & geenpeil & piratenpartij
for i in [252, 254, 256, 258, 260]:
        kieskringen[i] = [1, 2, 3, 4, 5, 6, 7]
        kieskringen[i+1] = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19] # no 20
# artikel 1
kieskringen[262] = [1, 4, 5, 6, 7, 8, 9]
kieskringen[263] = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
# niet stemmers
kieskringen[264] = [1, 4, 5, 6, 7, 8, 9]
kieskringen[265] = [10, 11, 12, 13, 14, 15, 17, 18, 19]
# libertarische partij
kieskringen[266] = [1, 2, 3, 5, 6, 7, 8]
kieskringen[267] = [9, 12, 13, 14, 15, 16, 17, 18, 19]
# liberaal in de kamer
kieskringen[268] = [1, 2, 3, 4, 5, 6, 7]
kieskringen[269] = [9, 10, 11, 12, 13, 14, 16, 17, 18]
# jezus leeft
kieskringen[270] = [5, 6, 7, 8, 14, 15, 17]
kieskringen[271] = []
# stemnl
kieskringen[272] = [7, 13]
kieskringen[273] = [6, 8, 14, 16, 17, 18]
# vdp
kieskringen[278] = [11, 12]


partijnummers = {
        "VVD": 1,
        "Partij van de Arbeid (P.v.d.A.)": 2,
        "PVV (Partij voor de Vrijheid)": 3,
        "SP (Socialistische Partij)": 4,
        "CDA": 5,
        "Democraten 66 (D66)": 6,
        "ChristenUnie": 7,
        "GROENLINKS": 8,
        "Staatkundig Gereformeerde Partij (SGP)": 9,
        "Partij voor de Dieren": 10,
        "50PLUS": 11,
        "OndernemersPartij": 12,
        "VNL (VoorNederland)": 13,
        "DENK": 14,
        "NIEUWE WEGEN": 15,
        "Forum voor Democratie": 16,
        "De Burger Beweging": 17,
        "Vrijzinnige Partij": 18,
        "GeenPeil": 19,
        "Piratenpartij": 20,
        "Artikel 1": 21,
        "Niet Stemmers": 22,
        "Libertarische Partij (LP)": 23,
        "Lokaal in de Kamer": 24,
        "JEZUS LEEFT": 25,
        "StemNL": 26,
        "MenS en Spirit / Basisinkomen Partij / V-R": 27,
        "Vrije Democratische Partij (VDP)": 28,
}

pages = pdf.pq('LTPage')
for i, page in enumerate(pages, 1):
        page_pq = pdf.get_pyquery(page)
        es = page_pq('LTTextLineHorizontal')
        if not any(e.text in ["Aanduiding politieke groepering: ", "Aanduiding politieke groepering ", "Aanduiding van de groepering: "] for e in es):
                continue
        if any("met voorkeurstemmen gekozen" in e.text for e in es if e.text is not None):
                continue
        if any(e.text == "Lijstengroepnummer: " for e in es):
                continue
        last_y = None
        lines = []
        line = []
        for e in sorted(es, key=lambda e: (-float(e.get("y1")), float(e.get("x0")))):
                if e.text is None or e.text.strip() in ["-", ""]:
                        continue
                y = float(e.get("y1"))
                if last_y and not abs(last_y - y) < 1:
                        lines.append(line)
                        line = []
                t = e.text.strip()
                while True:
                        m = re.fullmatch(r"(\d+) (.*)", t)
                        if m is None:
                                break
                        line.append(m.group(1))
                        t = m.group(2)
                line.append(t)
                last_y = y
        lines.append(line)

        kieskring = None
        n = 0
        while True:
                if n >= len(lines):
                        print("UNHANDLED")
                        break
                line = lines[n]
                if line[0] in ["Aanduiding politieke groepering:", "Aanduiding van de groepering:", "Aanduiding politieke groepering"]:
                        assert len(line) == 2
                        partij = line[1]
                        partijnummer = partijnummers[partij]
                if line[0] == "Kieskring:":
                        assert len(line) == 2
                        kieskring = [int(line[1])]
                if line[-1] == "stemmen":
                        n += 1
                        continue
                if (line[0] == "1" and line[1] not in ["2", "3", "4"]) or line[0] in ["40", "41"]:
                        has_names = re.match(r"\D", line[1])
                        if kieskring is None:
                                kieskring = kieskringen[i]
                        if has_names:
                                volgnummers = {}
                        volgnummer_prev = None
                        for line in lines[n:]:
                                try:
                                        volgnummer = int(line[0])
                                except ValueError:
                                        break
                                if (volgnummer_prev is not None) and (volgnummer != volgnummer_prev + 1):
                                        break
                                if has_names:
                                        naam = line[1]
                                        volgnummers[volgnummer] = naam
                                        r = 2
                                else:
                                        try:
                                                naam = volgnummers[volgnummer]
                                        except KeyError:
                                                print("UNHANDLED NAME "+str(volgnummer))
                                                naam = "*******"
                                        r = 1
                                stemmen = [s for s in line[r:] if s != "."]
                                for s, k in zip(stemmen, kieskring):
                                        kiescsv.writerow([partijnummer, partij, volgnummer, naam, k, s])
                                volgnummer_prev = volgnummer
                        break
                n += 1

        print((i, partij, kieskring))

        from pprint import pprint
        pprint(lines)
        print("\n"+"-"*80+str(i))

# hack because pdf parsing sucks
kiescsv.writerow([32, "Vrije Democratische Partij (VDP)", 1, "Gökalp, B. (m)", 11, 128])
kiescsv.writerow([32, "Vrije Democratische Partij (VDP)", 1, "Gökalp, B. (m)", 12, 49])
