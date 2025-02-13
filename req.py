import requests

url = 'http://127.0.0.1:5000'
response = requests.put(url+'/3',json= {"name": "Prince", "email": "prince@example.com"})
# response = requests.get(url+'/6')
# response = requests.delete(url+'/7')

print(response.json())
