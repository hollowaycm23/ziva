import requests


def get_weather(location):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid=YOUR_API_KEY&units=metric'
    response = requests.get(url)
    data = response.json()
    if data['cod'] == 200:
        return {
            'temperature': data['main']['temp'],
            'condition': data['weather'][0]['description'],
            'wind_speed': data['wind']['speed']
        }
    else:
        return {'error': 'Location not found'}


# Example usage
location = 'Artur Nogueira'
weather = get_weather(location)
print(weather)
