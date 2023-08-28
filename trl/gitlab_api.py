import requests
import traceback
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

def query_gitlab_api(endpoint):
    gitlab_project_id = os.environ.get('TRL_GITLAB_PROJECT_ID')
    api_url =  os.environ.get('TRL_GITLAB_API_URL') + gitlab_project_id + endpoint
    
    try:
        response = requests.get(api_url, headers={
            "PRIVATE-TOKEN": os.environ.get('TRL_GITLAB_READ_API_ACCESS_TOKEN'),
        })
        return response
    except:
        print(traceback.format_exc())
        return None


def get_gitlab_variable(key):
    api_endpoint = "/variables/" + key
    response = query_gitlab_api(api_endpoint)
    value = response.json().get('value')
    return value