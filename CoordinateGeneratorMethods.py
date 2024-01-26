# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 22:43:02 2023

@author: mitch
"""
import csv
import time
import requests
import sys
import os

# Can't counter search 'WA' : 'Western Australia' since WA is already Washington.
# Similar issue with NT, Northwest Territories (CA) and Northern Territory (AU)
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
               'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia', 'NS' : 'Nova Scotia',
               'NB' : 'New Brunswick', 'QB' : 'Quebec', 'ON' : 'Ontario', 'MB' : 'Manitoba',
               'SK' : 'Saskatchewan', 'AB' : 'Alberta', 'BC' : 'British Columbia', 'YK' : 'Yukon'}

               #'NSW' : 'New South Wales', 'NT' : 'Northern Territory', 'QLD' : 'Queensland',
               #'SA' : 'South Australia', 'TAS' : 'Tasmania', 'VIC' : 'Victoria'}

useragent = 'Personal User Client (mitchell446@yahoo.com; Wikipedia username Mitchell316) Requests/2.31.0'

catalog_name = 'town_catalog.csv'

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

def WikiData_Search(town_list, town_catalog): 

    coords_counter = 0          # No. towns found in local database
    wiki_counter = 0            # No. towns not found in local database
    error_counter = 0           # No. towns not found in local database or WikiData
    wiki_list = []              # List of towns that are sent to WikiData for coordinates

    
    # Determines if the scraped town is in the local town_catalog.csv file.
    for i in range(len(town_list)):
        if town_list[i] not in town_catalog:
            wiki_list.append(town_list[i])
            wiki_counter += 1
        else:
            coords_counter += 1
    
    print(str(coords_counter) + ' towns recognized in local database.')
    print(str(wiki_counter) + ' towns to search. Starting in three seconds:')
    
    # Sends empty data if no towns are needed to search on WikiData.
    if wiki_counter == 0:
        print("All towns are found in the town_catalog.csv")
        return [], [], []
        #sys.exit(1)
    
    time.sleep(3)
    print(u'\u2500' * 50)
    

    newtown_list = []
    latitude_list = []
    longitude_list = []
    error_town_list = []
    
    
    for i in range(len(wiki_list)):
        
        time.sleep(1)           # As per WikiData policy, cannot exceed 60 requests per 60 seconds.
        
        try:
    
            latitude, longitude = SQLsearch(wiki_list[i]) 
            
            newtown_list.append(wiki_list[i])
            latitude_list.append(latitude)
            longitude_list.append(longitude)
            print(latitude, longitude)
            
        except:
            try:
                # Tries to search "Town, State" instead of "Town, ST".
                delimit = wiki_list[i].split(', ')
                delimit[-1] = state_abrv[delimit[-1]]
                modified_name = ', '.join(delimit)
                latitude, longitude = SQLsearch(modified_name)
                
                newtown_list.append(wiki_list[i])
                latitude_list.append(latitude)
                longitude_list.append(longitude)
                print(latitude, longitude)
                
                
            except:
                print("at index: " + str(i) + "   No data found for " + wiki_list[i])
                newtown_list.append(wiki_list[i])
                error_counter += 1
                latitude_list.append("ERROR")
                longitude_list.append("ERROR")
                error_town_list.append(wiki_list[i])
    

    print(u'\u2500' * 50)

    header = ['bad_town_name', 'latitude', 'longitude', 'variant_town_name']
    
    error_town_list_nested = [[x] for x in error_town_list]
    
    # Stops program if error_towns.csv already exists. If the corrections were not yet complete,
    # the current progress would have been overwritten.
    path = 'error_towns.csv'
    if not os.path.exists(path):
        with open('error_towns.csv', 'w', encoding='UTF8', newline='') as f:
            csvwriter = csv.writer(f)
            csvwriter.writerow(header)
            csvwriter.writerows(error_town_list_nested)
    else:
        print("error_towns.csv already exists. Fill in the towns and rename error_towns_corrections.csv.")
        sys.exit(1)
    
    print('error_towns.csv has been created. Add corrections here.')
    
    print(str(error_counter) + " towns have no result on WikiData.") 
    
    
    return newtown_list, latitude_list, longitude_list

def catalog_generator(town_list):

    with open(catalog_name, 'r', encoding="utf8") as csv_file:
        reader = csv.reader(csv_file)
        towncatalog = [rows for rows in reader]

    town_catalog = [col[0] for col in towncatalog]

    # If the corrections file has been created, no WikiData searches are done.
    # The towns which were previously found in WikiData are saved in temp_list_file.csv
    # to prevent searching those towns again.
    path = 'error_towns_corrections.csv'
    if os.path.exists(path):
        with open('temp_list_file.csv', 'r', encoding="utf8") as f:
            reader = csv.reader(f)
            tempfiles = [rows for rows in reader]
            
        newtown_list = [x[0] for x in tempfiles]
        latitude_list = [x[1] for x in tempfiles]
        longitude_list = [x[2] for x in tempfiles]
     
    # If the corrections file has not been created, the towns are searched in WikiData.
    # Towns not found are written to error_towns.csv for manual corrections.
    else:        
        newtown_list, latitude_list, longitude_list = WikiData_Search(town_list, town_catalog)
        
        # Checks to see if the returned lists have any data. If no data is present,
        # the function returns an empty array. The CoordinateGenerator.py file does the
        # remaining work.
        if not newtown_list and not latitude_list and not longitude_list:
            return []
        
        temp_list = [list(e) for e in zip(newtown_list, latitude_list, longitude_list)]

        # In order to prevent WikiData queries from running after the corrections file has
        # been created, the above lists need to be saved and read from afterwards. This
        # temporary file is meaningless otherwise and can be deleted/overwritten.
        with open('temp_list_file.csv', 'w', encoding='UTF8', newline='') as f:
            csvwriter = csv.writer(f)
            csvwriter.writerows(temp_list)
            

     
    final_towns_list, latitude_list, longitude_list, variant_town_list = remove_error_towns(newtown_list, latitude_list, longitude_list, towncatalog)

    final_list = [list(d) for d in zip(final_towns_list, latitude_list, longitude_list)]

    # Prevents against rerunning the script and continuing to append the catalog.
    if final_list[0][0] not in town_catalog:
        with open(catalog_name, 'a', encoding='UTF8', newline='') as f:
            csvwriter = csv.writer(f)
            csvwriter.writerows(final_list)
        
    return variant_town_list


# Run after the corrections have been manually made.
def remove_error_towns(town_list, lat_list, long_list, towncatalog):
    
    # First tries to open the corrections file, quits if no file is detected.
    try:
        with open('error_towns_corrections.csv', 'r', encoding='UTF8', newline='') as f:
            reader = csv.reader(f)
            errortowns = [row for row in reader][1:]
    except:
        print("ERROR: Corrections are missing. When the manual corrections are done, rename the file to 'error_towns_corrections.csv'")
        sys.exit(1)
    
    town_catalog = [x[0] for x in towncatalog]
    catalog_lat = [x[1] for x in towncatalog]
    catalog_long = [x[2] for x in towncatalog]
    
    error_towns = [col[0] for col in errortowns]

    error_towns_errorcheck(errortowns)  # checks for errors in the error_towns_corrections.csv file.

    # Adds the coordinates or re-searches the new town depending on what option was filled out per town.
    variant_town_list = []
    for i in range(len(town_list)):
        if lat_list[i] == 'ERROR':
            if town_list[i] in error_towns:
                index = error_towns.index(town_list[i])
                if not errortowns[index][3]:

                    lat_list[i] = errortowns[index][1]
                    long_list[i] = errortowns[index][2]
                else:
                    try:
                        variant_town = errortowns[index][3]
                        variant_town_list.append([town_list[i], variant_town])
                        if variant_town in town_catalog:
                            print("Found new name at index " + str(index) + " in local database: " + str(variant_town))
                            catalog_index = town_catalog.index(variant_town)
                            latitude = catalog_lat[catalog_index]
                            longitude = catalog_long[catalog_index]
                        else:
                            print("searching new name at index " + str(index) + " on Wikidata: " + str(variant_town))
                            latitude, longitude = SQLsearch(variant_town)
                            time.sleep(1)
                        
                        
                        lat_list[i] = latitude
                        long_list[i] = longitude
                        
                    except:
                        print("The modified town name " + variant_town + " does not match any WikiData towns. Rerun when changed.")
                        sys.exit(1)
            else:
                print(str(town_list[i]) + " is missing from error_towns_corrections.csv. Complete entry and rerun script.")
                sys.exit(1)
            
    return town_list, lat_list, long_list, variant_town_list



# Checks for errors in the error_towns_corrections.csv file.
def error_towns_errorcheck(errortowns):
    error_lat = [col[1] for col in errortowns]
    error_long = [col[2] for col in errortowns]
    error_variant = [col[3] for col in errortowns]
    
    
    for i in range(len(errortowns)):
        
        # condition_list stores whether the coords or variant town name exist.
        # If the list does not match either just coords (T, T, F) or just one 
        # one variant town (F, F, T) then the program is stopped.
        
        condition_list = []
        
        if error_lat[i]:
            condition_list.append(True)
        else:
            condition_list.append(False)
            
        if error_long[i]:
            condition_list.append(True)
        else:
            condition_list.append(False)
            
        if error_variant[i]:
            condition_list.append(True)
        else:
            condition_list.append(False)
            
        
        if condition_list != [True, True, False] and condition_list != [False, False, True]:
            print("error_towns_corrections.csv has improper formating at index: " + str(i))            
            sys.exit(1)

    
    
    return None



