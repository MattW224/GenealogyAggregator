# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 23:34:15 2023

@author: mitch
"""

import csv
import time
import requests

state_abrv  =  {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
               'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
               'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
               'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
               'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
               'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
               'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
               'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
               'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
               'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
               'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
               'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
               'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'}


with open('town_catalog.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    town_catalog = [rows[0] for rows in reader]
    
with open('NameAdjuster_Result.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    town_list = [rows[0] for rows in reader]
    
    

counter = 0
count2 = 0
wiki_list = []
for i in range(len(town_list)):
    if town_list[i] not in town_catalog:
        #print(town_list[i])
        wiki_list.append(town_list[i])
        counter += 1
        #if town_list[i].endswith('KS'):
         #   #print(town_list[i])
          #  count2 += 1
            
print(str(counter) + ' Towns to Search. Starting in three seconds:')
time.sleep(3)

useragent = 'Personal User Client (mitchell446@yahoo.com; Wikipedia username Mitchell316) Requests/2.31.0'

def fetch_wikidata(params):
    url = 'https://www.wikidata.org/w/api.php'
    try:
        return requests.get(url, params=params, headers = {'User-Agent' : useragent})
    except:
        return 'There was and error'
    
def getWikidata(query):
    endpointUrl = 'https://query.wikidata.org/sparql'

    # The endpoint defaults to returning XML, so the Accept: header is required
    r = requests.get(endpointUrl, params={'query' : query}, headers={'Accept' : 'application/sparql-results+json',
                                                                     'User-Agent' : useragent})

    if r.status_code == 429:
        print(int(r.headers["Retry-After"]))
        time.sleep(int(r.headers["Retry-After"]))
        
    data = r.json()
    statements = data['results']['bindings']
    return statements

def SQLsearch(wiki_town):
    params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'search': wiki_town,
            'language': 'en'
        }
     
    
    data = fetch_wikidata(params).json()
    Q = data['search'][0]['title']
    SQLquery = '''
    SELECT ?coords ?coordsLabel
     WHERE {
            wd:%s wdt:P625 ?coords;
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
    }''' % Q
     
    
    researchers = getWikidata(SQLquery)
    coords = researchers[0]['coords']['value'][6:-1]
    latitude = coords.split(" ")[1]
    longitude = coords.split(" ")[0]
    
    return latitude, longitude



#town_list = ['Walworth, New York', 'New York, New York', 'Melbourne, Florida', 'fake town, Iowa', 'Stow, OH', 'Lancaster, MA', 'Nokomis, CA']
latitude_list = []
longitude_list = []

for i in range(len(wiki_list)):
    
    time.sleep(1)
    
    try:        

        latitude, longitude = SQLsearch(wiki_list[i]) 
        
        latitude_list.append(latitude)
        longitude_list.append(longitude)
        print(latitude, longitude)
        
    except:
        try:
            delimit = wiki_list[i].split(', ')
            delimit[-1] = state_abrv[delimit[-1]]
            modified_name = ', '.join(delimit)
            latitude, longitude = SQLsearch(modified_name)
            
            latitude_list.append(latitude)
            longitude_list.append(longitude)
            print(latitude, longitude)
            
            
        except:
            print("at index: " + str(i) + "   No data found for " + wiki_list[i])
            latitude_list.append("ERROR")
            longitude_list.append("ERROR")


final_list = [list(a) for a in zip(wiki_list, latitude_list, longitude_list)]


with open('CatalogComparer_wikidata.csv', 'w', encoding='UTF8', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerows(final_list)
