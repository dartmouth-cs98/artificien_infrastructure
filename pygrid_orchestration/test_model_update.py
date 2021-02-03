import os
import requests
orchestration_endpoint = 'http://localhost:5001/model_progress'
model_id = 'perceptron'
completed_cycles_num = 5
max_cycles = 5
data = {
    'percent_complete': (completed_cycles_num * 100) // max_cycles, 
    'model_id': model_id
}
response = requests.post(url=orchestration_endpoint, json=data)
print(response.text)
