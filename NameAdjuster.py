# -*- coding: utf-8 -*-
"""
Created on Thu Jul 20 21:59:27 2023

@author: Owner
"""
import csv
from unidecode import unidecode

country_dict = {' UK': ' United Kingdom', ' MX': ' Mexico', ' ES': ' Spain', ' NL': ' Netherlands', 
                ' NZ': ' New Zealand', ' AU': ' Australia', ' CA': ' Canada', ' IS': ' Iceland',
                ' DZ': ' Algeria', ' LV': ' Latvia', ' GL' : ' Greenland', ' DE': ' Germany',
                ' AT': ' Austria', ' FR': ' France', ' ID': ' Indonesia', ' IE': ' Ireland',
                ' IT': ' Italy', ' PRT': ' Portugal'}


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
                "Wisconsin": "WI", "Wyoming": "WY", "District of Columbia": "DC"}
    
    i = 0
    for town in town_list:
        delimit = town.split(',')
        if delimit[-1][1:] in state_abrv:
            new_town = delimit[0] + ', ' + state_abrv.get(delimit[-1][1:])
            town_list[i] = new_town
        
        i += 1
        
    return town_list
    
    
    

mylist = []

with open('collated_newchron.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    paper_list = [rows for rows in reader]
    
    
town_list = [x[3] for x in paper_list[1:]]
database_list = [x[5] for x in paper_list[1:]]

i = -1
for town in town_list:
    new_town = town
    i += 1
    
    if database_list[i] == 'Newspapers.com':
        delimit = town.split(',')
        if delimit[-1] == ' New Zealand':
            new_town = delimit[0] + ', New Zealand'
        if delimit[-1] == ' Australia':
            new_town = delimit[0] + ', Australia'
        if delimit[-1] == ' Canada':
            new_town = delimit[0] + ', Canada'
        if (delimit[-1] == ' England' or delimit[-1] == ' Wales' or delimit[-1] == ' Scotland') and delimit[0] != "St. Ives":
            new_town = delimit[0] + ', United Kingdom'
        mylist.append([town, unidecode(new_town)])
        continue
    
    if database_list[i] == 'GenealogyBank.com':
        delimit = town.split(",")
        if len(delimit[-1]) > 2:
            new_town = delimit[0] + ',' + delimit[-1]
        mylist.append([town, new_town])
        continue
        
    if database_list[i] == 'ChroniclingAmerica.loc.gov':
        delimit = town.split(",")
        if len(delimit) == 3:
           new_town = delimit[0] + ',' + delimit[2]
        mylist.append([town, new_town])
        continue
           
    if database_list[i] == 'NewspaperArchive.com':
        delimit = town.split(",")
        if delimit[-1] == ' US':
            new_town = delimit[0] + ',' + delimit[1]
            
        if delimit[-1] in country_dict:
            new_town = delimit[0] + ',' + country_dict[delimit[-1]]

        '''if delimit[-1] == ' UK' or delimit[-1] == ' AU' or delimit[-1] == ' CA' or delimit[-1] == ' IS' or delimit[-1] == ' NL':
            new_town = delimit[0] + ',' + delimit[-1]
        if delimit[-1] == ' MX':
            new_town = delimit[0] + ', Mexico'    
        if delimit[-1] == ' ES':
            new_town = delimit[0] + ', Spain'''
        mylist.append([town, unidecode(new_town)])
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
        
        mylist.append([town, new_town])
        continue
    


header = ['town_name', 'new_town_name']

#print(mylist)

with open('coord_database.csv', 'w', encoding='UTF8', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerow(header)
    csvwriter.writerows(mylist)


modified_town_list = [x[1] for x in mylist]
reduced_list = reduce_clutter(modified_town_list)
no_duplicates = [*set(reduced_list)]
new = [[x] for x in no_duplicates]

with open('town_lookup.csv', 'w', encoding='UTF8', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerows(new)










