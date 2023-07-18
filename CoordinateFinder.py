import requests
 
def fetch_wikidata(params):
    url = 'https://www.wikidata.org/w/api.php'
    try:
        return requests.get(url, params=params)
    except:
        return 'There was and error'
    
def getWikidata(query):
    endpointUrl = 'https://query.wikidata.org/sparql'

    # The endpoint defaults to returning XML, so the Accept: header is required
    r = requests.get(endpointUrl, params={'query' : query}, headers={'Accept' : 'application/sparql-results+json'})
    data = r.json()
    statements = data['results']['bindings']
    return statements

    
# What text to search for
query = 'New York, New York'
 
# Which parameters to use
params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'search': query,
        'language': 'en'
    }
 
data = fetch_wikidata(params)
data = data.json()
Q = data['search'][0]['title']

SQLquery = '''
SELECT ?coords ?coordsLabel
 WHERE {
        wd:%s wdt:P625 ?coords;
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
}''' % Q


latitude = []
longitude = []

researchers = getWikidata(SQLquery)
coords = researchers[0]['coords']['value'][6:-1]
latitude.append(coords.split(" ")[1])
longitude.append(coords.split(" ")[0])


print(latitude, longitude)











