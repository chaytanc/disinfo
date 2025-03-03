import requests

# References
# https://github.com/ASD-at-GMF/junkiprocessor/blob/main/junkipedia_client.py
# https://docs.junkipedia.org/reference-material/api/query-string-parameters/lists 

BASE_URL = "https://www.junkipedia.org/api/v1/"
API_KEY = TODO

def get_data():
    # response = requests.get(f"{BASE_URL}?lists={lists_str}&per_page={results_per_page}&page={page_num}", headers={"Authorization": f"Bearer {self.api_key}"})
    # response = requests.get(f"{BASE_URL}/posts?lists=TODOlistnumber")
    response = requests.get(f"{BASE_URL}/posts?keyword=tenet+media", headers={"Authorization": f"Bearer {API_KEY}"})

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()
    return response