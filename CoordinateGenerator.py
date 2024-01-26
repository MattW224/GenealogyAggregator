# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 22:45:59 2023

@author: mitch
"""
import csv
from unidecode import unidecode
from CoordinateGeneratorMethods import catalog_generator
from core import *
import sys
import os
import pdb


def reduce_clutter(locations):
    for index, town in enumerate(locations):
        delimit = town.split(',')

        city = delimit[0]
        potential_state = delimit[-1].strip()

        if potential_state in state_abrv:
            new_location = city + ', ' + state_abrv[potential_state]
            locations[index] = new_location

    return locations


scraped_name = 'scraped_data.csv'
print("Opening scraped data file...")

with open(scraped_name, 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    paper_list = [rows for rows in reader]

town_list = [x[3] for x in paper_list[1:]]
database_list = [x[5] for x in paper_list[1:]]

print("Modifying %s town names..." % len(town_list))

scraped_towns = []
# Records indices for entries in format of "County, ST".
county_index_list = []
for index, town in enumerate(town_list):
    new_town = town

    if database_list[index] == NEWSPAPERS:
        delimit = town.split(',')
        if delimit[-1] == ' New Zealand':
            new_town = delimit[0] + ', New Zealand'
        # if delimit[-1] == ' Australia':
         #   new_town = delimit[0] + ', Australia'
        if delimit[-1] == ' Canada':
            new_town = delimit[0] + ',' + delimit[1]
        if delimit[-1] in [' England', ' Wales', ' Scotland'] and delimit[0] != "St. Ives":
            new_town = delimit[0] + ', United Kingdom'
        scraped_towns.append(unidecode(new_town))
    elif database_list[index] == GENEALOGY_BANK:
        delimit = town.split(",")
        if len(delimit[-1]) > 2:
            new_town = delimit[0] + ',' + delimit[-1]
        if delimit[0] == 'County':
            county_index_list.append(i)
        scraped_towns.append(new_town)
    elif database_list[index] == CHRONICLING_AMERICA:
        new_town = town.replace('.', '').replace(
            '[', '').replace(']', '').replace('-', ' ')
        delimit = new_town.split(",")
        if len(delimit) == 3:
            new_town = delimit[0] + ',' + delimit[2]
        if delimit[-1] in chronicling_america_state_dict:
            new_town = delimit[0] + ',' + \
                chronicling_america_state_dict[delimit[-1]]
        scraped_towns.append(new_town)
    elif database_list[index] == NEWSPAPER_ARCHIVE:
        delimit = town.split(",")
        if delimit[-1] == ' US':
            new_town = delimit[0] + ',' + delimit[1]
        if delimit[-1] in country_dict:
            new_town = delimit[0] + ',' + country_dict[delimit[-1]]
        if len(delimit) == 3 and delimit[-1] == ' CA':
            new_town = delimit[0] + ',' + delimit[1]
        if len(delimit) == 3 and delimit[-1] == ' AU':
            if delimit[1][1:] in australia_dict:
                new_town = delimit[0] + ', ' + \
                    australia_dict.get(delimit[1][1:])
            else:
                new_town = delimit[0] + ',' + delimit[1]
        scraped_towns.append(unidecode(new_town))
    elif database_list[index] == NYS_HISTORIC_NEWSPAPERS:
        new_town = town.replace('.', '').replace(
            '[', '').replace(']', '').replace('-', ' ')
        delimit = new_town.split(',')
        if len(delimit) > 2:
            new_town = delimit[0] + ',' + delimit[2]
        if len(delimit) == 1:
            newdelimit = delimit[0].split(' ')
            newdelimit[-1] = ', ' + newdelimit[-1]
            new_town = ''.join(newdelimit)
        scraped_towns.append(new_town)

# Removes entries that are in format "County, ST" from genealogybank. I tried deleting
# in the above loop, but deleting entries above messed up the indexing.
print("Deleting %s 'County, ST' entries from GenealogyBank..." %
      len(county_index_list))
for index in sorted(county_index_list, reverse=True):
    del scraped_towns[index]
    del paper_list[index + 1]

reduced_list = reduce_clutter(scraped_towns)
reduced_list.insert(0, 'modified_town_name')

for i in range(len(reduced_list)):
    missing_modified_town_name = len(paper_list[i]) == 6
    if missing_modified_town_name:
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
        print(
            str(reduced_list[i]) + " never got added to the catalog. Something went wrong.")
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
    os.replace('error_towns_corrections.csv',
               'error_towns_old_corrections.csv')

# Deletes error_towns.csv file when the code has successfully updated the catalog.
# Prevents an overwriting error from being flagged if more towns are added. See WikiData_Search().
path = 'error_towns.csv'
if os.path.exists(path):
    os.remove(path)
