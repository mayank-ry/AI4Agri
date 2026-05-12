import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("OPEN_WEATHER")
city = "Indore"
url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
response = requests.get(url)
data = response.json()

if response.status_code == 200:
    print("Temperature:", data['main']['temp'])
    print("Humidity:", data['main']['humidity'])
    print("Weather:", data['weather'][0]['description'])
else:
    # This will tell you EXACTLY why it failed (e.g., "Invalid API key")
    print(f"API Error {response.status_code}: {data.get('message')}")