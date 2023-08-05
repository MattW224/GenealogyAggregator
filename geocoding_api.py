import csv
import requests
import os

API_KEY = os.getenv("GOOGLE_GEOCODING_API")

LATITUDE_KEY = "lat"
LONGITUDE_KEY = "lng"

bad_towns = []

town_catalog = []
latitude_coordinates = []
longitude_coordinates = []

def get_coordinates(location_name):
    location_data = requests.get(
        url = "https://maps.googleapis.com/maps/api/geocode/json",
        params = {
            "address": location_name,
            "key": API_KEY
        }
    ).json()['results']

    if location_data:
        return location_data[0]['geometry']['location']
    else:
        return None

with open('CatalogComparer_wikidata.csv', 'r', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file)
    towns, lats, longs = zip(*reader)

    # Change from tuple to list in order to support item assignment.
    town_catalog = list(towns)
    latitude_coordinates = list(lats)
    longitude_coordinates = list(longs)

for index, coordinate in enumerate(latitude_coordinates):
    if coordinate != 'ERROR':
        continue

    new_coordinates = get_coordinates(town_catalog[index])
    if not new_coordinates:
        continue

    print(town_catalog[index])
    latitude_coordinates[index] = new_coordinates[LATITUDE_KEY]
    longitude_coordinates[index] = new_coordinates[LONGITUDE_KEY]

final_list = [list(a) for a in zip(town_catalog, latitude_coordinates, longitude_coordinates)]
with open('CatalogComparer_wikidata.csv', 'w', encoding='UTF8', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerows(final_list)
