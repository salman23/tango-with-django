__author__ = 'salman wahed'

import json
import requests
from requests.auth import HTTPBasicAuth
import urllib


def run_query(search_terms):
    root_url = "https://api.datamarket.azure.com/Bing/Search/v1/Web"
    API_KEY = "********"
    results_per_page = 10
    offset = 0
    query = "'{}'".format(search_terms)
    query = urllib.quote(query)
    results = []
    search_url = "{0}?$format=json&$top={1}&$skip={2}&Query={3}".format(root_url, results_per_page, offset, query)
    print search_url
    try:
        response = requests.get(search_url, auth=HTTPBasicAuth('', API_KEY))
        json_response = json.loads(response.content)
        query_data = json_response.get('d').get('results')
    except Exception as e:
        print e.message
    else:
        for result in query_data:
            results.append(dict(title=result['Title'], link=result['Url'], summary=result['Description']))

    return results
