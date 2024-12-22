from datetime import datetime

import requests

from exceptions import ApiError


class API:
    def __init__(
            self,
            api_key,
            base_url='http://dataservice.accuweather.com/'
    ):
        self.base_url = base_url
        self.api_key = api_key

    def location_key(self, city_name):
        req = requests.get(url=f'{self.base_url}locations/v1/cities/search',
                           params={
                               'apikey': self.api_key,
                               'q': city_name,
                               'language': 'en-us',
                               'details': 'true'
                           })
        res = req.json()
        return res[0]

    def weather(self, city_name):
        try:
            location = self.location_key(city_name)
            location_key = location["Key"]
        except Exception:
            raise ApiError("Не удалось найти город")
        try:
            req = requests.get(url=f'{self.base_url}forecasts/v1/daily/5day/{location_key}',
                               params={
                                   'apikey': self.api_key,
                                   'language': 'en-us',
                                   'details': 'true',
                                   'metric': 'true'
                               })
            res = req.json()
        except Exception:
            raise ApiError("Не удалось получить погоду")

        try:
            lst = list()
            for day in res['DailyForecasts']:
                lst.append({
                    'city': city_name,
                    'date': datetime.fromisoformat(day['Date']),
                    'temperature': (day['Temperature']['Minimum']['Value'] +
                                    day['Temperature']['Maximum']['Value']) / 2,
                    'rain': day['Day']['RainProbability'],
                    'humidity': day['Day']['RelativeHumidity']['Average'],
                    'wind': day['Day']['Wind']['Speed']['Value'],
                    'lat': location['GeoPosition']['Latitude'],
                    'lot': location['GeoPosition']['Longitude'],
                })

            return lst
        except Exception:
            raise ApiError("Не удалось распаковать данные")
