import requests
from pathlib import Path
import json


API_URL = 'https://restcountries.eu/rest/v2/alpha/br'
CACHE_FILE = 'population.cache.json'


def get_country_population(code2):
	must_request = False
	cache = Path(CACHE_FILE)

	if cache.exists():
		data = 
	response = requests.get('https://restcountries.eu/rest/v2/all')
