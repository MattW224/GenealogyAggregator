# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 22:45:59 2023

@author: mitch
"""
import csv
from unidecode import unidecode
from CoordinateGeneratorMethods import catalog_generator
import sys
import os
# Removed ' CA': ' Canada' and ' AU': ' Australia' from below
country_dict = {' UK': ' United Kingdom', ' MX': ' Mexico', ' ES': ' Spain', ' NL': ' Netherlands', 
                ' NZ': ' New Zealand', ' IS': ' Iceland',
                ' DZ': ' Algeria', ' LV': ' Latvia', ' GL' : ' Greenland', ' DE': ' Germany',
                ' AT': ' Austria', ' FR': ' France', ' ID': ' Indonesia', ' IE': ' Ireland',
                ' IT': ' Italy', ' PRT': ' Portugal', ' AR': ' Argentina', ' AZ': ' Azerbaijan',
                ' BS': ' Bahamas', ' BE': ' Belgium', ' BR': ' Brazil', ' CN': ' China', ' HR': ' Croatia',
                ' CZ': ' Czechia', ' DK': ' Denmark', ' EG': ' Egypt', ' FI': ' Finland', ' JM': ' Jamaica',
                ' JP': ' Japan', ' KZ': ' Kazakhstan', ' KG': ' Kyrgyzstan', ' MA': ' Morocco',
                ' NO': ' Norway', ' RO': ' Romania', ' RS': ' Serbia', ' ZA': ' South Africa',
                ' SR': ' Suriname', ' TJ': ' Tajikistan', ' TN': ' Tunisia', ' TM': ' Turkmenistan',
                ' UA': ' Ukraine', ' UZ': ' Uzbekistan'}

chronicling_america_state_dict =  {' Fla' : ' FL', ' Minn' : ' MN', ' Miss' : ' MS',
                                   ' Ariz' : ' AZ', ' Colo' : ' CO', ' Wis' : ' WI',
                                   ' Ala' : ' AL', ' Neb' : ' NE', ' Mont' : ' MT',
                                   ' Wash' : ' WA', ' Tenn' : ' TN', ' Calif' : ' CA',
                                   ' Conn' : ' CT', ' Nev' : ' NV', ' Ark' : ' AR',
                                   ' Mich' : ' MI', ' Ill' : ' IL', ' Tex' : ' TX',
                                   ' Kan' : ' KS', ' Cal' : ' CA', ' Wyo' : ' WY', ' Okla' : ' OK'}

australia_dict = {'NSW' : 'New South Wales', 'NT' : 'Northern Territory', 'QLD' : 'Queensland',
                  'SA' : 'South Australia', 'TAS' : 'Tasmania', 'VIC' : 'Victoria', 'WA' : 'Western Australia'}

def reduce_clutter(town_list):
    state_abrv = { "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ",
                "Arkansas": "AR", "California": "CA", "Colorado": "CO",
                "Connecticut": "CT", "Delaware": "DE", "Florida": "FL",
                "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL",
                "Indiana": "IN", "Iowa": "IA", "Kansas": "KS", "Kentucky": "KY",
                "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
                "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
                "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
                "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
                "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
                "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
                "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
                "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
                "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
                "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC", 
                "Nova Scotia" : "NS", "New Brunswick" : "NB", "Quebec" : "QB",
                "Ontario" : "ON", "Manitoba" : "MB", "Saskatchewan" : "SK",
                "Alberta" : "AB", "British Columbia" : "BC", "Yukon" : "YK",
                "Northwest Territories" : "NT"}
                
                #"New South Wales" : "NSW",
                #"Northern Territory" : "NT", "Queensland" : "QLD", "South Australia" : "SA",
                #"Tasmania" : "TAS", "Victoria" : "VIC", "Western Australia" : "WA"}
    
    i = 0
    for town in town_list:
        delimit = town.split(',')
        if delimit[-1][1:] in state_abrv:
            new_town = delimit[0] + ', ' + state_abrv.get(delimit[-1][1:])
            town_list[i] = new_town
        
        i += 1
        
    return town_list
    
    
mylist = []

scraped_name = 'the_great_data_pull_reduced.csv'
catalog_name = 'town_catalog.csv'

print("Opening scraped data file...")

with open(scraped_name, 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    paper_list = [rows for rows in reader]
    
    
town_list = [x[3] for x in paper_list[1:]]
database_list = [x[5] for x in paper_list[1:]]

print("Modifying %s town names..." % len(town_list))

i = -1
county_index_list = []                              # Records indices for entries in format of "County, ST".
for town in town_list:
    new_town = town
    i += 1                                          # Would need to increment in every if statement, can't add on bottom.
    
    if database_list[i] == 'Newspapers.com':
        delimit = town.split(',')
        if delimit[-1] == ' New Zealand':
            new_town = delimit[0] + ', New Zealand'
        #if delimit[-1] == ' Australia':
         #   new_town = delimit[0] + ', Australia'
        if delimit[-1] == ' Canada':
            new_town = delimit[0] + ',' + delimit[1]
        if (delimit[-1] == ' England' or delimit[-1] == ' Wales' or delimit[-1] == ' Scotland') and delimit[0] != "St. Ives":
            new_town = delimit[0] + ', United Kingdom'
        mylist.append(unidecode(new_town))
        continue
    
    
    if database_list[i] == 'GenealogyBank.com':
        delimit = town.split(",")
        if len(delimit[-1]) > 2:
            new_town = delimit[0] + ',' + delimit[-1]
        if delimit[0] == 'County':
            county_index_list.append(i)
        mylist.append(new_town)
        continue
        
    if database_list[i] == 'ChroniclingAmerica.loc.gov':
        new_town = town.replace('.', '').replace('[','').replace(']', '').replace('-', ' ')
        delimit = new_town.split(",")
        if len(delimit) == 3:
           new_town = delimit[0] + ',' + delimit[2]
        if delimit[-1] in chronicling_america_state_dict:
            new_town = delimit[0] + ',' + chronicling_america_state_dict[delimit[-1]]
        mylist.append(new_town)
        continue
           
    if database_list[i] == 'NewspaperArchive.com':
        delimit = town.split(",")
        if delimit[-1] == ' US':
            new_town = delimit[0] + ',' + delimit[1]
        if delimit[-1] in country_dict:
            new_town = delimit[0] + ',' + country_dict[delimit[-1]]
        if len(delimit) == 3 and delimit[-1] == ' CA':
            new_town = delimit[0] + ',' + delimit[1]
        if len(delimit) == 3 and delimit[-1] == ' AU':
            if delimit[1][1:] in australia_dict:
                new_town = delimit[0] + ', ' + australia_dict.get(delimit[1][1:])
            else:
                new_town = delimit[0] + ',' + delimit[1]
        mylist.append(unidecode(new_town))
        continue
    
    if database_list[i] == 'NYSHistoricNewspapers.org':
        new_town = town.replace('.', '').replace('[','').replace(']', '').replace('-', ' ')
        delimit = new_town.split(',')
        if len(delimit) > 2:
            new_town = delimit[0] + ',' + delimit[2]
        if len(delimit) == 1:
            newdelimit = delimit[0].split(' ')
            newdelimit[-1] = ', ' + newdelimit[-1]
            new_town = ''.join(newdelimit)
        
        mylist.append(new_town)
        continue

# Removes entries that are in format "County, ST" from genealogybank. I tried deleting
# in the above loop, but deleting entries above messed up the indexing.
print("Deleting %s 'County, ST' entries from GenealogyBank..." % len(county_index_list))
for index in sorted(county_index_list, reverse=True):
    del mylist[index]
    del paper_list[index + 1]


#modified_town_list = [x[1] for x in mylist]
reduced_list = reduce_clutter(mylist)
reduced_list.insert(0, 'modified_town_name')

for i in range(len(reduced_list)):
    if len(paper_list[i]) == 6:
        paper_list[i].append(reduced_list[i])


no_duplicate_list = [x for x in [*set(reduced_list[1:])]]

variant_town_list = catalog_generator(no_duplicate_list)

old_variants = [x[0] for x in variant_town_list]
new_variants = [x[1] for x in variant_town_list]



with open(catalog_name, 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    towncatalog = [rows for rows in reader]
    
town_catalog = [col[0] for col in towncatalog]
lat_catalog_list = [col[1] for col in towncatalog]
long_catalog_list = [col[2] for col in towncatalog]

lat_list = []
long_list = []

for i in range(1, len(reduced_list)):
    
    # Writes the modified name from error_towns_corrections.csv to the modified name on scraped_data.csv.
    if reduced_list[i] in old_variants:
        index = old_variants.index(reduced_list[i])
        paper_list[i][6] = new_variants[index]
    
    
    if reduced_list[i] in town_catalog:
        index = town_catalog.index(reduced_list[i])
        lat_list.append(lat_catalog_list[index])
        long_list.append(long_catalog_list[index])
    else:
        print(str(reduced_list[i]) + " never got added to the catalog. Something went wrong.")
        sys.exit(1)

for i in range(1, len(reduced_list)):
    if len(paper_list[i]) == 7:
        paper_list[i].append(lat_list[i - 1])
        paper_list[i].append(long_list[i - 1])

if len(paper_list[0]) == 7:
    paper_list[0].append('latitude')
    paper_list[0].append('longitude')

with open(scraped_name, 'w', encoding='UTF8', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerows(paper_list)
    
# Replaces the corrections file with some other name. If the old corrections file is
# present when new towns are added, this would cause an error.
path = 'error_towns_corrections.csv'
if os.path.exists(path):
    os.replace('error_towns_corrections.csv','error_towns_old_corrections.csv')
    
# Deletes error_towns.csv file when the code has successfully updated the catalog.
# Prevents an overwriting error from being flagged if more towns are added. See WikiData_Search().
path = 'error_towns.csv'
if os.path.exists(path):
    os.remove(path)









