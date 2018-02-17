import requests
from pandas import DataFrame
import pandas as pd

class Airquality:
    def __init__(self):
        self.host = "https://api.waqi.info"

    def get_air(self):
        mapq = '/mapq/bounds'
        place = '37.41979929880289,126.81106567382812,37.64849035620595,127.13516235351561'
        payload = {'bounds':place,'inc': 'placeholders','k':'_2Y2EzUBxYHRAdIztCSElWXmldVg09LTdWFXg/ZA==&_=1518844865243'}
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        url_path = self.host+ mapq
        res = requests.get(url_path, params=payload, headers=headers)
        return res
class Upbit:
	def __init__(self):
		self.host = "https://crix-api-endpoint.upbit.com"
	def get_candles(self, coin_type=None, condition=None):
		if coin_type is None:
			raise Exception('Need to coin type') 
		time.sleep(1)
		candle_api_path = "/v1/crix/candles/"+condition #ex)minutes/3
		url_path = self.host + candle_api_path
		coin_type = "CRIX.UPBIT.KRW-"+coin_type
		payload = {'code':coin_type, 'count':20}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
		res = requests.get(url_path, params=payload, headers=headers)
		response_json = res.json()
		frame = DataFrame(response_json)
#		print(frame['timestamp'])
		frame.sort_values("timestamp", inplace=True)
		print(frame)
		return frame	
if __name__ == '__main__':
	air = Airquality()
	air.get_air()
