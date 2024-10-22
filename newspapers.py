from bs4 import BeautifulSoup
from core import *
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from ratelimit import limits, sleep_and_retry
import requests
import json
import datetime
import unicodedata
import pandas
import aiohttp
import asyncio
import pdb
import urllib
import time
import math

CURRENT_YEAR = datetime.date.today().year
USER_AGENT = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"}

async def __fetch(session, url, content_type):
    async with session.get(url, ssl=True) as response:
        if content_type == "application/json":
            return await response.json(content_type=content_type)
        else:
            return await response.text()

async def __fetch_all(urls, loop, content_type="application/json"):
    async with aiohttp.ClientSession(loop=loop, headers=USER_AGENT) as session:
        results = await asyncio.gather(*[__fetch(session, url, content_type) for url in urls], return_exceptions=True)
        return results

@sleep_and_retry
@limits(calls=5, period=1) # Five calls per second
def get_with_throttling(newspaper_url):
    return requests.get(url = newspaper_url, headers = USER_AGENT).json()

# https://chroniclingamerica.loc.gov/
def extract_chronicling_america():

    overview = requests.get(
        url = "https://chroniclingamerica.loc.gov/newspapers.json",
        headers = USER_AGENT
    ).json()
    newspaper_urls = list({newspaper["url"] for newspaper in overview["newspapers"]})

    newspaper_data = []
    for newspaper_url in newspaper_urls:
        newspaper_data.append(get_with_throttling(newspaper_url))

    titles = []
    for newspaper in newspapers:
        start_date = newspaper['issues'][0]['date_issued']
        end_date = newspaper['issues'][-1]['date_issued']

        place_name = newspaper['place_of_publication']

        newspaper_title = newspaper['name']

        PERIOD = '.'
        DOTTED_VOLUME = '. [volume]'
        VOLUME = '[volume]'

        # Get newspaper names consistent.
        if newspaper_title.endswith(PERIOD):
            newspaper_title = newspaper_title.rsplit(PERIOD, 1)[0].strip()
        elif newspaper_title.endswith(DOTTED_VOLUME):
            newspaper_title = newspaper_title.rsplit(DOTTED_VOLUME, 1)[0].strip()
        elif newspaper_title.endswith(VOLUME):
            newspaper_title = newspaper_title.rsplit(VOLUME, 1)[0].strip()

        if(len(newspaper['place']) == 1):
            place_name = ", ".join(newspaper['place'][0].split("--")[::-1])
        else:
            place_name = newspaper['place_of_publication']

        titles.append(item_formatter(
            title=newspaper_title,
            start_year=datetime.datetime.strptime(start_date, "%Y-%m-%d").year,
            # Used last issue instead of end year, because the latter can be unknown (e.g. "19xx").
            # Besides, we're more interested in what's digitized than publication dates.
            end_year=datetime.datetime.strptime(start_date, "%Y-%m-%d").year,
            location=place_name,
            link=newspaper['url'][:-5],
            data_provider=CHRONICLING_AMERICA
        ))

    return titles

# https://www.newspapers.com/
def extract_newspapers():
    increment = 50
    newspapers_scanned = 0

    newspaper_urls = []
    titles = []

    total_newspapers = requests.get(
        url = "https://www.newspapers.com/api/title/query",
        params = {
            "fields": ["count"],
            "product-id": ["1"]
        },
        headers = USER_AGENT
    ).json()['count']

    while newspapers_scanned <= total_newspapers:
        prepared_request = requests.Request('GET', 'https://www.newspapers.com/api/title/query', params =
            {
                "start": [newspapers_scanned],
                "count": [increment],
                "sort": ["updated"],
                "fields": ["title,url,location.display,updated,product_canonical_start_year,product_canonical_end_year"],
                "product-id": ["1"]   
            }
        ).prepare()

        newspaper_urls.append(prepared_request.url)
        newspapers_scanned += increment

    loop = asyncio.new_event_loop()
    paginated_response = loop.run_until_complete(__fetch_all(newspaper_urls, loop))

    for page in paginated_response:
        try:
            for title in page["titles"]:
                titles.append(item_formatter(
                    title=title['title'],
                    start_year=title['product_canonical_start_year'],
                    end_year=title['product_canonical_end_year'],
                    location=title['location']['display'],
                    link= f"https://www.newspapers.com{title['url']}",
                    data_provider=NEWSPAPERS
                ))
        except KeyError:
            print(f"\nReceived {page} on URL:\n ${prepared_request.url}\n")
            continue

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

            title = columns[0].text.strip()
            cleaned_title = title.removesuffix(" UPDATED").removesuffix(" NEW").strip()

            location = columns[1].text.strip()
            state = columns[2].text.strip()
            country = columns[3].text.strip()
            start_year, end_year = columns[4].text.strip().split("-")

            titles.append(item_formatter(
                title=cleaned_title,
                start_year=start_year,
                end_year=end_year,
                location=f"{location}, {state}, {country}",
                link=columns[0].a['href'],
                data_provider=NEWSPAPER_ARCHIVE
            ))

        # If publicationrowstring is blank, we exhausted the dataset.
        page_has_data = bool(decoded_html.strip())
        page += 1

    return titles

# https://nyshistoricnewspapers.org/
def extract_nys_historic_newspapers():
    ENDPOINT = "https://nyshistoricnewspapers.org"

    titles = []

    holdings = requests.get(
        url = f"{ENDPOINT}/?a=cl&cl=CL1&e=-------en-20--1--txt-txIN----------",
        headers = USER_AGENT
    )

    decoded_html = holdings.content.decode('utf-8')
    holdings_soup = BeautifulSoup(decoded_html, 'html.parser')

    chapters = holdings_soup.findAll('ul', class_='publicationbrowserlist')    
    titles_markup = [li for chapter in chapters for li in chapter.findAll("li")]

    for title_markup in titles_markup:
        newspaper_endpoint = ENDPOINT + title_markup.a['href']

        newspaper = requests.get(
            url = newspaper_endpoint,
            headers = USER_AGENT
        )

        decoded_html = newspaper.content.decode('utf-8')
        newspaper_soup = BeautifulSoup(decoded_html, 'html.parser')

        publication_info = newspaper_soup.find("div", {"id": "publicationlevelwrap"})

        try:
            title = publication_info.find("b", string="Title:").parent.b.nextSibling.strip()
            location = publication_info.find("b", string="Location:").parent.text.split(":")[1].strip()
            dates = publication_info.find("b", string="Available online:").parent.b.nextSibling
        except AttributeError:
            # Occurs because NYS has only one issue, and links directly to the PDF -- no pub. info.
            print("Could not parse publisher information from URL:\n" + newspaper_endpoint + "\n")
            continue

        # Get start and end dates from string like "24 April 1909 - 24 January 1931 (12 issues)"
        start_date, end_date = dates.split('(')[0].split('-')

        titles.append(item_formatter(
            title=title,
            start_year=datetime.datetime.strptime(start_date.strip(), '%d %B %Y').year,
            end_year=datetime.datetime.strptime(end_date.strip(), '%d %B %Y').year,
            location=f"{location}, New York",
            link=newspaper_endpoint,
            data_provider=NYS_HISTORIC_NEWSPAPERS
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

    browser = webdriver.Chrome()
    timeout = 10
    papers = []

    for state_name in STATE_LIST:
        current_page_number = 0
        total_papers = 0
        total_webpages = 0

        while current_page_number <= total_webpages:
            url = BASE_URL + state_name + f"?page={current_page_number}"

            browser.get(url)
            print(url)

            try:
                element_present = expected_conditions.presence_of_element_located((By.CLASS_NAME, 'views-table'))
                WebDriverWait(browser, timeout).until(element_present)
            except TimeoutException:
                print("Timed out waiting for page to load.")

            soup = BeautifulSoup(browser.page_source, 'html.parser')

            # Finds paper count that is listed at the top for each state's page.
            if not total_papers:
                total_papers = int(soup.find('h1').text.split(" ")[3])
            # GenealogyBank indexes website at 1, but query parameter at 0.
            if not total_webpages:
                total_webpages = math.ceil(total_papers/200) - 1

            table = soup.find('table', class_='views-table')
            table_rows = table.find_all('tr')

            for row in table_rows[1:]:
                columns = row.find_all('td')
                city = columns[0].text.strip()
                start_date, end_date = unicodedata.normalize("NFKD", columns[2].text.strip()).split("–")

                papers.append(item_formatter(
                    title=columns[1].a.text,
                    start_year=datetime.datetime.strptime(start_date.strip(), "%m/%d/%Y").year,
                    end_year=CURRENT_YEAR if end_date.strip() == "Current" else datetime.datetime.strptime(end_date.strip(), "%m/%d/%Y").year,
                    location=f"{city}, {state_name}",
                    link=f"https://genealogybank.com{columns[1].a['href']}",
                    data_provider=GENEALOGY_BANK
                ))

            current_page_number += 1
            # time.sleep(10) # Respect robots.txt
    return papers

# https://news.google.com/newspapers
# Excluded from the data pull below, because Not updated for decades.
# First data pull is, and always will be current.
def extract_google_news_archive():
    GOOGLE_ARCHIVE_ENDPOINT = "https://news.google.com/newspapers"
    ALPHABET = set("A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z")

    titles = []
    date_format = "%b %d, %Y"

    page = requests.get(GOOGLE_ARCHIVE_ENDPOINT)
    soup = BeautifulSoup(page.content, "html.parser")

    # First instance is alphabetical shortcut to newspapers. Second is actual newspapers.
    markup = soup.findAll("table", {"class": "np-bhp-tbl"})[1]
    newspaper_row = markup.findAll("tr")

    for datapoint in newspaper_row:
        newspapers = datapoint.findAll("td")

        # Ignore heading for each alphabet character.
        if newspapers[0].b.text in ALPHABET:
            continue
        
        for newspaper in newspapers:
            if 'class' in newspaper.attrs and newspaper.attrs['class'][0] == 'np-bhp-border-cell':
                continue

            dates = newspaper.findAll("font")[1].text
            start_date, end_date = dates.split("-")

            titles.append(item_formatter(
                title = newspaper.b.text,
                start_year = datetime.datetime.strptime(start_date.strip(), date_format).year,
                end_year = datetime.datetime.strptime(end_date.strip(), date_format).year,
                location = "IDK",
                link = newspaper.a['href'],
                data_provider = GOOGLE_NEWS_ARCHIVE
            ))

    return titles

# https://fairhopepl.advantage-preservation.com/
def extract_advantage_preservation():
    titles = []
    loop = asyncio.new_event_loop()

    SITE_DIRECTORY = "https://api.historyarchives.online/Api/SiteDir/getDetail?url=https://directory.historyarchives.online"
    manifest = requests.get(url=SITE_DIRECTORY).json()
    states = [urllib.parse.quote(state["StateName"]) for state in manifest["statelist"]]

    state_urls = []
    for state in manifest["statelist"]:
        state_url = f"https://directory.advantage-preservation.com/Date/GetCityListSiteDir?state={state["StateName"]}"
        state_urls.append(state_url)

    # Get all newspapers belonging to a specified state.
    state_newspapers = loop.run_until_complete(__fetch_all(state_urls, loop))

    # Flatten array.
    newspapers = [newspaper for state_newspaper in state_newspapers for newspaper in state_newspaper['DataState']]    
    # Create array of URLs to parallelize requests for date information.
    newspaper_date_urls = [f"{newspaper['url']}//search?t={newspaper['TitleID']}" for newspaper in newspapers]

    publication_info = loop.run_until_complete(__fetch_all(newspaper_date_urls, loop, "text/html"))

    for index, newspaper in enumerate(newspapers):
        try:
            publication_soup = BeautifulSoup(publication_info[index], "html.parser")
            date_markup = publication_soup.find("input", {"id": "hdnViewAll"})
            year_range = date_markup['value'].split(',')
        # Might fail because of connection error, or no dates published.
        except:
            continue
        
        location = newspaper['cityName'] + ", " + newspaper['StateName']

        titles.append(item_formatter(
            title=newspaper['publicationName'],
            start_year=year_range[0],
            end_year=year_range[-1],
            location=location,
            link=newspaper_date_urls[index],
            data_provider=ADVANTAGE_PRESERVATION
        ))
    
    return titles

newspapers = []
'''
print("Executing data pull for Chronicling America...")
newspapers.extend(extract_chronicling_america())

print("Executing data pull for Advantage Preservation...")
newspapers.extend(extract_advantage_preservation())

print("Executing data pull for GenealogyBank...")
newspapers.extend(extract_genealogy_bank())

print("Executing data pull for Newspapers.com...")
newspapers.extend(extract_newspapers())

print("Executing data pull for NYS Historic Newspapers...")
newspapers.extend(extract_nys_historic_newspapers())
'''

print("Executing data pull for Newspaper Archive...")
newspapers.extend(extract_newspaper_archive())

data_dumper(newspapers, 'great_data_dump.csv')
