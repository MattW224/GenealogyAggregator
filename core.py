import json
import pandas

ADVANTAGE_PRESERVATION = "Advantage-Preservation.com"
CHRONICLING_AMERICA = "ChroniclingAmerica.loc.gov"
FULTON_HISTORY = "FultonHistory.com"
GENEALOGY_BANK = "GenealogyBank.com"
GOOGLE_NEWS_ARCHIVE = "Google News Archive"
NEWSPAPERS = "Newspapers.com"
NEWSPAPER_ARCHIVE = "NewspaperArchive.com"
NYS_HISTORIC_NEWSPAPERS = "NYSHistoricNewspapers.org"
TROVE = "Trove.nla.gov.au"

catalog_name = 'town_catalog.csv'

country_dict = {
	" UK":" United Kingdom",
	" MX":" Mexico",
	" ES":" Spain",
	" NL":" Netherlands",
	" NZ":" New Zealand",
	" IS":" Iceland",
	" DZ":" Algeria",
	" LV":" Latvia",
	" GL":" Greenland",
	" DE":" Germany",
	" AT":" Austria",
	" FR":" France",
	" ID":" Indonesia",
	" IE":" Ireland",
	" IT":" Italy",
	" PRT":" Portugal",
	" AR":" Argentina",
	" AZ":" Azerbaijan",
	" BS":" Bahamas",
	" BE":" Belgium",
	" BR":" Brazil",
	" CN":" China",
	" HR":" Croatia",
	" CZ":" Czechia",
	" DK":" Denmark",
	" EG":" Egypt",
	" FI":" Finland",
	" JM":" Jamaica",
	" JP":" Japan",
	" KZ":" Kazakhstan",
	" KG":" Kyrgyzstan",
	" MA":" Morocco",
	" NO":" Norway",
	" RO":" Romania",
	" RS":" Serbia",
	" ZA":" South Africa",
	" SR":" Suriname",
	" TJ":" Tajikistan",
	" TN":" Tunisia",
	" TM":" Turkmenistan",
	" UA":" Ukraine",
	" UZ":" Uzbekistan"
}

chronicling_america_state_dict = {
	" Fla":" FL",
	" Minn":" MN",
	" Miss":" MS",
	" Ariz":" AZ",
	" Colo":" CO",
	" Wis":" WI",
	" Ala":" AL",
	" Neb":" NE",
	" Mont":" MT",
	" Wash":" WA",
	" Tenn":" TN",
	" Calif":" CA",
	" Conn":" CT",
	" Nev":" NV",
	" Ark":" AR",
	" Mich":" MI",
	" Ill":" IL",
	" Tex":" TX",
	" Kan":" KS",
	" Cal":" CA",
	" Wyo":" WY",
	" Okla":" OK"
}

australia_dict = {
	"NSW":"New South Wales",
	"NT":"Northern Territory",
	"QLD":"Queensland",
	"SA":"South Australia",
	"TAS":"Tasmania",
	"VIC":"Victoria",
	"WA":"Western Australia"
}

state_abrv = {
	"Alabama":"AL",
	"Alaska":"AK",
	"Arizona":"AZ",
	"Arkansas":"AR",
	"California":"CA",
	"Colorado":"CO",
	"Connecticut":"CT",
	"Delaware":"DE",
	"Florida":"FL",
	"Georgia":"GA",
	"Hawaii":"HI",
	"Idaho":"ID",
	"Illinois":"IL",
	"Indiana":"IN",
	"Iowa":"IA",
	"Kansas":"KS",
	"Kentucky":"KY",
	"Louisiana":"LA",
	"Maine":"ME",
	"Maryland":"MD",
	"Massachusetts":"MA",
	"Michigan":"MI",
	"Minnesota":"MN",
	"Mississippi":"MS",
	"Missouri":"MO",
	"Montana":"MT",
	"Nebraska":"NE",
	"Nevada":"NV",
	"New Hampshire":"NH",
	"New Jersey":"NJ",
	"New Mexico":"NM",
	"New York":"NY",
	"North Carolina":"NC",
	"North Dakota":"ND",
	"Ohio":"OH",
	"Oklahoma":"OK",
	"Oregon":"OR",
	"Pennsylvania":"PA",
	"Rhode Island":"RI",
	"South Carolina":"SC",
	"South Dakota":"SD",
	"Tennessee":"TN",
	"Texas":"TX",
	"Utah":"UT",
	"Vermont":"VT",
	"Virginia":"VA",
	"Washington":"WA",
	"West Virginia":"WV",
	"Wisconsin":"WI",
	"Wyoming":"WY",
	"District of Columbia":"DC",
	"Nova Scotia":"NS",
	"New Brunswick":"NB",
	"Quebec":"QB",
	"Ontario":"ON",
	"Manitoba":"MB",
	"Saskatchewan":"SK",
	"Alberta":"AB",
	"British Columbia":"BC",
	"Yukon":"YK",
	"Northwest Territories":"NT"
}

# TODO: Is there a more Pythonic way?
def item_formatter(title, start_year, end_year, location, link, data_provider):
    return {
        'title': title,
        'start_year': start_year,
        'end_year': end_year,
        'location': location,
        'link': link,
        'data_provider': data_provider
    }

def data_dumper(newspaper_data, filename):
    dataframe = pandas.read_json(json.dumps(newspaper_data))
    dataframe.to_csv(filename, encoding="utf-8", index=False)