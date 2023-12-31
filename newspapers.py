from bs4 import BeautifulSoup
import requests
import json
import datetime
import unicodedata
import pandas
import aiohttp
import asyncio
import pdb

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

    loop = asyncio.get_event_loop()
    paginated_response = loop.run_until_complete(__fetch_all(newspaper_urls, loop))

    for page in paginated_response:
        for title in page["titles"]:
            titles.append(__item_formatter(
                title=title['title'],
                start_year=title['product_canonical_start_year'],
                end_year=title['product_canonical_end_year'],
                location=title['location']['display'],
                link= f"https://www.newspapers.com{title['url']}",
                data_provider="Newspapers.com"
            ))

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
                    link=f"https://genealogybank.com{columns[1].a['href']}",
                    data_provider="GenealogyBank.com"
                ))

            current_page_number += 1
    return papers

# https://news.google.com/newspapers
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

            titles.append(__item_formatter(
                title = newspaper.b.text,
                start_year = datetime.datetime.strptime(start_date.strip(), date_format).year,
                end_year = datetime.datetime.strptime(end_date.strip(), date_format).year,
                location = "IDK",
                link = newspaper.a['href'],
                data_provider = "Google News Archive"
            ))

    return titles

# https://fairhopepl.advantage-preservation.com/
def extract_advantage_preservation():
    titles = []
    loop = asyncio.get_event_loop()

    SITE_DIRECTORY = "https://directory.advantage-preservation.com/SiteDirectory"

    page = requests.get(SITE_DIRECTORY)
    soup = BeautifulSoup(page.content, "html.parser")

    # Manually parse state names from UI, because "state" is misleading -- not necessarily
    # US states. It contains oddities like "Cuba" and "Griffin".
    state_html = soup.find("ul", {"class": "stateUl"})

    state_urls = []
    for state in state_html:
        state_name = state.text.strip()
        if not state_name:
            continue

        state_url = f"https://directory.advantage-preservation.com/Date/GetCityListSiteDir?state={state_name}"
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
            year_range = ["Unknown"]
        
        location = newspaper['cityName'] + ", " + newspaper['StateName']

        titles.append(__item_formatter(
            title=newspaper['publicationName'],
            start_year=year_range[0],
            end_year=year_range[-1],
            location=location,
            link=newspaper_date_urls[index],
            data_provider="Advantage-Preservation.com"
        ))
    
    return titles

def data_dumper(newspaper_data, filename):
    dataframe = pandas.read_json(json.dumps(newspaper_data))
    dataframe.to_csv(filename, encoding="utf-8", index=False)

# Sample usage
data_dumper(extract_advantage_preservation(), 'advantage_preservation.csv')