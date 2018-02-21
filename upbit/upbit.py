import requests
import time
from pandas import DataFrame
import pandas as pd

import telegram


class Upbit:
	def __init__(self):
		self.host = "https://crix-api-endpoint.upbit.com"
		self.my_token = '502539613:AAE7AVI0SkdC05YCOBVhTImPINgZ0jL5ugk'
		self.bot = telegram.Bot(self.my_token)   #bot을 선언합니다.
		self.chat_id = 495733797
		self.coins = ['SNT','XRP','BTC','ADA','TIX','QTUM','XLM','GRS','BCC','ETH','KMD','STEEM','XEM','EMC2'\
					,'POWR','ETC','MER','NEO','STORJ','OMG','LSK','REP','ARK','BTG','WAVES','MTL','SBD','STRAT'\
					,'VTC','PIVX','LTC','XMR','DASH','ZEC']#,'ARDR']

	def get_ticks(self, coin_type = None):
		tick_api_path = '/v1/crix/trades/ticks'
		coin_type = "CRIX.UPBIT.KRW-"+coin_type
		payload = {'code':coin_type,'count':1}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
		res = requests.get(url_path, params=payload, headers=headers)
		response_json = res.json()

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

	def cci(self,coin_type = None,condition = None, number=None):
		if coin_type is None:
			raise Exception('Need to coin type') 
		time.sleep(1)
		frame = self.get_candles(coin_type, condition)
		constant = .015
		n = number
		hi = frame['highPrice']
		lo = frame['lowPrice']
		cl = frame['tradePrice']
		vol = frame['candleAccTradePrice']
		frame['TP'] = (hi+lo+cl)/3
		CCI = pd.Series((frame['TP'] - frame['TP'].rolling(window=n).mean()) / (constant * frame['TP'].rolling(window=n).std()), name = 'CCI_' + str(n)) 
		val = []
		val.append(CCI.iloc[-1])
		val.append(CCI.iloc[-1]-CCI.iloc[-2])
		val.append(CCI.iloc[-2])
		val.append(frame['candleAccTradePrice'].iloc[-2])
		print(val)
		return val

	def targets(self):
		tars = []
		for coin in self.coins:
			val = self.cci(coin_type = coin, condition = "days", number = 18)
			if val[0]>0 and val[3]>10000000000:
				tars.append(coin)
			time.sleep(1)
			print(tars)
		return tars

	def run(self):
		while(True):
			tars = self.targets()
			self.bot.sendMessage(chat_id=self.chat_id, text = tars)
			for item in tars:
				val = self.cci(coin_type = item, condition = "minutes/15", number = 14)
				#items = []
				#if val[0]>0 and val[1]>0:
				#	items.append(item)
				#msg = items 
				#self.bot.sendMessage(chat_id = self.chat_id, text=msg)
				#elif val[0] <100 and val[1]<0 and val[2]>100:
				#	msg = item + " sell!"
				#	self.bot.sendMessage(chat_id=self.chat_id, text = msg)
				time.sleep(1)					
			time.sleep(3600)
if __name__ == "__main__":
	machine=Upbit()
	machine.run()