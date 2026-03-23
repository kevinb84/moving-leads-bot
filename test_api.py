import requests
import json
with open('.insforge/project.json') as f:
    cfg = json.load(f)
key = cfg.get('api_key')
h = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
url = cfg.get('oss_host') + '/database/records/moving_leads?select=*'
print("GET:", requests.get(url, headers=h).status_code)
print("POST:", requests.post(url, headers=h, json={'customer_name': 'test'}).status_code)
