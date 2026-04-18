import requests
import time

# def request()

payload = {
    'prompt': 'an astronaught riding a horse on the moon'
}
response = requests.post('http://localhost:8000/generate', json=payload)
print('POST request submitted')

response_json = response.json()
job_id = response_json['job_id']
print(response_json)

status = requests.get(f'http://localhost:8000/status/{job_id}').json()
print(status)
while status['status'] not in ['SUCCESS', 'FAILURE']:
    print(status)
    status = requests.get(f'http://localhost:8000/status/{job_id}').json()
    time.sleep(2)

print(status)
# while requests.get('http://localhost:8000/status/')