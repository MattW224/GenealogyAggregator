import requests
import json

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

def extract_chronicling_america():
    titles = []

    overview = requests.get(
        url = "https://chroniclingamerica.loc.gov/newspapers.json",
        headers = {'User-Agent': USER_AGENT}
    ).json()

    for newspaper in overview["newspapers"]:
        newspaper_details = requests.get(
            url = newspaper["url"],
            headers = {'User-Agent': USER_AGENT}
        ).json()

        # Largest key by far, and not needed -- remove to save memory.
        del newspaper_details["issues"]

        titles.append(newspaper_details)

    return titles

def extract_newspapers():
    increment = 50
    newspapers_scanned = 0
    total_newspapers = 0

    titles = []

    while newspapers_scanned <= total_newspapers:
        response = requests.get(
            url = "https://www.newspapers.com/api/title/query",
            params = {
                "start": [newspapers_scanned],
                "count": [increment],
                "sort": ["updated"],
                "fields": ["title,url,location.display,updated,product_canonical_start_year,product_canonical_end_year,count"],
                "product-id": ["1"]
            },
            headers = {'User-Agent': USER_AGENT}
        ).json()

        if not total_newspapers:
            total_newspapers = response['count']
        
        titles.extend(response['titles'])
        newspapers_scanned += increment

def extract_newspaperarchive():
    page = 1
    page_has_data = True

    while page_has_data:
        encoded_html = requests.post(
            url = "https://newspaperarchive.com/Publications/Publicationlist",
            json = {
                "model": {
                    "MinPubDateYear":1607,
                    "MaxPubDateYear":2023,
                    "PageNumber":page,
                    "PageSize":100,
                    "LastThreeMonths":False,
                    "CityName":"",
                    "StateName":"",
                    "CountryName":"",
                    "Direction":"Desc"
                }
            },
            headers = {
                'User-Agent': USER_AGENT
            }
        )

        decoded_html = json.loads(encoded_html.content.decode('utf-8'))["renderpublicationview"]["publicationrowstring"]
        # TODO: BeautifulSoup parsing.

        # If publicationrowstring is blank, we exhausted the dataset.
        page_has_data = bool(decoded_html.strip())
        page += 1