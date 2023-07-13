from bs4 import BeautifulSoup
import requests
import json
import datetime

USER_AGENT = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}

# https://chroniclingamerica.loc.gov/
def extract_chronicling_america():
    titles = []

    overview = requests.get(
        url = "https://chroniclingamerica.loc.gov/newspapers.json",
        headers = USER_AGENT
    ).json()

    for newspaper in overview["newspapers"]:
        newspaper_details = requests.get(
            url = newspaper["url"],
            headers = USER_AGENT
        ).json()

        # Largest key by far, and not needed -- remove to save memory.
        del newspaper_details["issues"]

        titles.append(newspaper_details)

    return titles

# https://www.newspapers.com/
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
            headers = USER_AGENT
        ).json()

        if not total_newspapers:
            total_newspapers = response['count']
        
        titles.extend(response['titles'])
        newspapers_scanned += increment

    return titles

# https://newspaperarchive.com/
def extract_newspaper_archive():
    CURRENT_YEAR = datetime.date.today().year
    titles = []

    page = 1
    page_has_data = True

    while page_has_data:
        encoded_html = requests.post(
            url = "https://newspaperarchive.com/Publications/Publicationlist",
            json = {
                "model": {
                    "MinPubDateYear":1607,
                    "MaxPubDateYear":CURRENT_YEAR,
                    "PageNumber":page,
                    "PageSize":100,
                    "LastThreeMonths":False,
                    "CityName":"",
                    "StateName":"",
                    "CountryName":"",
                    "Direction":"Desc"
                }
            },
            headers = USER_AGENT
        )

        decoded_html = json.loads(encoded_html.content.decode('utf-8'))["renderpublicationview"]["publicationrowstring"]

        soup = BeautifulSoup(decoded_html, 'html.parser')
        table_rows = soup.find_all('tr')

        for row in table_rows:
            columns = row.find_all('td')
            item = {
                'name': columns[0].text.strip(),
                'link': columns[0].a['href'],
                'location': columns[1].text.strip(),
                'state': columns[2].text.strip(),
                'country': columns[3].text.strip(),
                'date_range': columns[4].text.strip(),
                'last_updated': columns[6].text.strip()
            }
            titles.append(item)

        # If publicationrowstring is blank, we exhausted the dataset.
        page_has_data = bool(decoded_html.strip())
        page += 1

    return titles

# https://nyshistoricnewspapers.org/
def extract_nys_historic_newspapers():
    titles = []

    encoded_html = requests.get(
        url = "https://nyshistoricnewspapers.org/newspapers/",
        headers = USER_AGENT
    )

    decoded_html = encoded_html.content.decode('utf-8')
    soup = BeautifulSoup(decoded_html, 'html.parser')
    table = soup.find('table', class_='browse_collect')
    table_rows = table.find_all('tr')
    headers = [header.text.strip() for header in table_rows[0].find_all('th')]

    for row in table_rows[1:]:
        columns = row.find_all('td')

        # Example: "Buffalo, N.Y., 1971-198?"
        publicationOverview = columns[0].br.nextSibling
        # Stripping publication years -- redundant with third and fourth columns.
        location = publicationOverview[0:publicationOverview.rindex(',')]

        item = {
            headers[0]: columns[0].strong.text,
            'Location': location,
            headers[3]: columns[3].text.strip(),
            headers[4]: columns[4].text.strip()
        }
        titles.append(item)

    return titles
