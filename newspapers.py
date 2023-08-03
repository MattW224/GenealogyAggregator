from bs4 import BeautifulSoup
import requests
import json
import datetime
import unicodedata
import pandas
import aiohttp
import asyncio

CURRENT_YEAR = datetime.date.today().year
USER_AGENT = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}

# TODO: Is there a more Pythonic way?
def __item_formatter(title, start_year, end_year, location, link, data_provider):
    return {
        'title': title,
        'start_year': start_year,
        'end_year': end_year,
        'location': location,
        'link': link,
        'data_provider': data_provider
    }

async def __fetch(session, url):
    async with session.get(url, ssl=True) as response:
        return await response.json()

async def __fetch_all(urls, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        results = await asyncio.gather(*[__fetch(session, url) for url in urls], return_exceptions=True)
        return results

# https://chroniclingamerica.loc.gov/
def extract_chronicling_america():
    titles = []

    overview = requests.get(
        url = "https://chroniclingamerica.loc.gov/newspapers.json",
        headers = USER_AGENT
    ).json()

    newspaper_urls = [newspaper["url"] for newspaper in overview["newspapers"]]
    
    loop = asyncio.get_event_loop()
    newspapers = loop.run_until_complete(__fetch_all(newspaper_urls, loop))

    for newspaper in newspapers:
        start_date = newspaper['issues'][0]['date_issued']
        end_date = newspaper['issues'][-1]['date_issued']

        place_name = newspaper['place'][0]

        titles.append(__item_formatter(
            # TODO: Remove "[volume]" postfix from newspaper name.
            title=newspaper['name'],
            start_year=datetime.datetime.strptime(start_date, "%Y-%m-%d").year,
            # Used last issue instead of end year, because the latter can be unknown (e.g. "19xx").
            # Besides, we're more interested in what's digitized than publication dates.
            end_year=datetime.datetime.strptime(start_date, "%Y-%m-%d").year,
            location=", ".join(place_name.split("--")[::-1]),
            link=newspaper['url'][:-5],
            data_provider="ChroniclingAmerica.loc.gov"
        ))

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
        
        for title in response['titles']:
            titles.append(__item_formatter(
                title=title['title'],
                start_year=title['product_canonical_start_year'],
                end_year=title['product_canonical_end_year'],
                location=title['location']['display'],
                link= f"https://www.newspapers.com{title['url']}",
                data_provider="Newspapers.com"
            ))

        newspapers_scanned += increment

    return titles

# https://newspaperarchive.com/
def extract_newspaper_archive():
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

            location = columns[1].text.strip()
            state = columns[2].text.strip()
            country = columns[3].text.strip()
            start_year, end_year = columns[4].text.strip().split("-")

            titles.append(__item_formatter(
                # TODO: Remove "NEW" and "UPDATED" postfix from title.
                title=columns[0].text.strip(),
                start_year=start_year,
                end_year=end_year,
                location=f"{location}, {state}, {country}",
                link=columns[0].a['href'],
                data_provider="NewspaperArchive.com"
            ))

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

    for row in table_rows[1:]:
        columns = row.find_all('td')

        # Example: "Buffalo, N.Y., 1971-198?"
        publicationOverview = columns[0].br.nextSibling
        # Stripping publication years -- redundant with third and fourth columns.
        location = publicationOverview[0:publicationOverview.rindex(',')]

        start_date = columns[3].text.strip()
        end_date = columns[4].text.strip()

        titles.append(__item_formatter(
            title=columns[0].strong.text,
            start_year=datetime.datetime.strptime(start_date, "%Y-%m-%d").year,
            end_year=datetime.datetime.strptime(end_date, "%Y-%m-%d").year,
            location=location,
            link=f"https://nyshistoricnewspapers.org{columns[0].a['href']}",
            data_provider="NYSHistoricNewspapers.org"
        ))

    return titles

def extract_genealogy_bank():
    BASE_URL = "https://www.genealogybank.com/newspapers/sourcelist/"
    STATE_LIST = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL',
                'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA',
                'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE',
                'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI',
                'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 
                'WY']

    papers = []

    for state_name in STATE_LIST:
        current_page_number = 0
        total_papers = 0
        total_webpages = 0

        while current_page_number <= total_webpages:
            url = BASE_URL + state_name + f"?page={current_page_number}"
            r = requests.get(url)
            print(url)
            soup = BeautifulSoup(r.content, 'html.parser')

            # Finds paper count that is listed at the top for each state's page.
            if not total_papers:
                total_papers = int(soup.find('h1').text.split(" ")[3])
            # GenealogyBank indexes website at 1, but query parameter at 0.
            if not total_webpages:
                total_webpages = int(total_papers/200)

            table = soup.find('table', class_='views-table')
            table_rows = table.find_all('tr')

            for row in table_rows[1:]:
                columns = row.find_all('td')
                city = columns[0].text.strip()
                start_date, end_date = unicodedata.normalize("NFKD", columns[2].text.strip()).split("–")

                papers.append(__item_formatter(
                    title=columns[1].a.text,
                    start_year=datetime.datetime.strptime(start_date.strip(), "%m/%d/%Y").year,
                    end_year=CURRENT_YEAR if end_date.strip() == "Current" else datetime.datetime.strptime(end_date.strip(), "%m/%d/%Y").year,
                    location=f"{city}, {state_name}",
                    link=f"https://genealogybank.com.org{columns[1].a['href']}",
                    data_provider="GenealogyBank.com"
                ))

            current_page_number += 1
    return papers

def data_dumper(newspaper_data, filename):
    dataframe = pandas.read_json(json.dumps(newspaper_data))
    dataframe.to_csv(filename, encoding="utf-8", index=False)

# Sample usage
# data_dumper(extract_chronicling_america(), 'chronicling_america.csv')