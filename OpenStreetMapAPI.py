# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 16:21:59 2023

@author: mitch
"""
import overpass
import csv
import time

with open('Errortownstest.csv', 'r', encoding="utf-8-sig") as csv_file:
    reader = csv.reader(csv_file)
    mylist = [rows[0] for rows in reader]
    

for i in range(len(mylist)):
    delimit = mylist[i].split(", ")
    mylist[i] = [delimit[0], delimit[-1]]
    

    
#print(mylist)
api = overpass.API()

print("starting")

for i in range(len(mylist)):
    time.sleep(0.25)
    
    print(mylist[i])
    get_string = 'node["name"="%s"]["place"]["gnis:ST_alpha"="%s"]' % (mylist[i][0], mylist[i][1])
    
    
    
    response = api.get(get_string, responseformat="csv(name,::lat,::lon)")

    print(response)