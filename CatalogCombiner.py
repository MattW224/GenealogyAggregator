# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 21:46:30 2023

@author: mitch
"""

import csv
    
with open('CatalogCSV/uscities.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    uslist = [rows for rows in reader]
    
ustownlist = [col[3] + ', ' + col[1] for col in uslist]
uslatlist = [col[5] for col in uslist]
uslonglist = [col[6] for col in uslist]
    
    
with open('CatalogCSV/worldcities.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    worldlist = [rows for rows in reader]
    
worldtownlist = [col[1] + ', ' + col[4] for col in worldlist]
worldlatlist = [col[2] for col in worldlist]
worldlonglist = [col[3] for col in worldlist]
    
with open('CatalogCSV/aucities.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    aulist = [rows for rows in reader]

autownlist = [col[1] + ', Australia' for col in aulist]
aulatlist = [col[13] for col in aulist]
aulonglist = [col[14] for col in aulist]

with open('CatalogCSV/cacities.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    calist = [rows for rows in reader]

catownlist = [col[1] + ', Canada' for col in calist]
calatlist = [col[4] for col in calist]
calonglist = [col[5] for col in calist]

with open('CatalogCSV/uscounties.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    countylist = [rows for rows in reader]

countytownlist = [col[2] + ', ' + col[4] for col in countylist]
countylatlist = [col[6] for col in countylist]
countylonglist = [col[7] for col in countylist]

with open('CatalogCSV/kansascities.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    kansaslist = [rows for rows in reader]

kansastownlist = [col[5] + ', KS' for col in kansaslist]
kansaslatlist = [col[15] for col in kansaslist]
kansaslonglist = [col[16] for col in kansaslist]


townlist = ustownlist + worldtownlist + autownlist + catownlist + countytownlist + kansastownlist
latlist = uslatlist + worldlatlist + aulatlist + calatlist + countylatlist + kansaslatlist
longlist = uslonglist + worldlonglist + aulonglist + calonglist + countylonglist + kansaslonglist

finallist = [list(a) for a in zip(townlist, latlist, longlist)]

with open('town_catalog.csv', 'w', encoding='UTF8', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerows(finallist)