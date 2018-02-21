from selenium import webdriver
import requests
import time
from pandas import DataFrame
import pandas as pd
import datetime
import telegram
import sys, traceback, configparser
from optparse import OptionParser

class Upbit:
	def __init__(self):
		config = configparser.ConfigParser()
		config.read('config.ini')
		self.email = config['UPBIT']['email']
		self.password = config['UPBIT']['password']
		self.host = "https://crix-api-endpoint.upbit.com"
		self.my_token = '502539613:AAE7AVI0SkdC05YCOBVhTImPINgZ0jL5ugk'
		self.bot = telegram.Bot(self.my_token)
		self.chat_id = 495733797
		self.coins = ['SNT','XRP','BTC','ADA','TIX','QTUM','XLM','GRS','BCC','ETH','KMD','STEEM','XEM','EMC2'\
					,'POWR','ETC','MER','NEO','STORJ','OMG','LSK','REP','ARK','BTG','WAVES','SBD','STRAT'\
					,'VTC','PIVX','LTC','XMR','DASH','ZEC']#,'ARDR']
		self.flag = 0
		self.coin_type = 'BTC'

	def get_ticks(self, coin_type = None):
		tick_api_path = '/v1/crix/trades/ticks'
		coin_type = "CRIX.UPBIT.KRW-"+coin_type
		payload = {'code':coin_type,'count':1}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
		res = requests.get(url_path, params=payload, headers=headers)
		response_json = res.json()

	def get_candles(self, coin_type=None, condition=None, count=None):
		if coin_type is None:
			raise Exception('Need to coin type') 
		time.sleep(1)
		candle_api_path = "/v1/crix/candles/"+condition #ex)minutes/3
		url_path = self.host + candle_api_path
		coin_type = "CRIX.UPBIT.KRW-"+coin_type
		payload = {'code':coin_type, 'count':count}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
		res = requests.get(url_path, params=payload, headers=headers)
		response_json = res.json()
		frame = DataFrame(response_json)
#		print(frame['timestamp'])
		frame.sort_values("timestamp", inplace=True)
		print(frame)
		return frame

	def cci(self,coin_type = None,condition = None, number=None, count=None):
		if coin_type is None:
			raise Exception('Need to coin type') 
		time.sleep(1)
		frame = self.get_candles(coin_type, condition, count)
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
			val = self.cci(coin_type = coin, condition = "days", number = 9, count=12)
			if val[0]>0 and val[3]>1000000000:
				tars.append(coin)
			time.sleep(1)
			print(tars)
		return tars
	
	def buy_scenario(self):
		targets = self.targets()
		while(self.flag==0):
			#targets = self.targets()
			now = datetime.datetime.now()
			print("                                                       ")       
			time.sleep(60)   
			print(now)

			for item in targets:
				self.coin_type = item
				cci_val = self.cci(coin_type = self.coin_type, condition = "minutes/1", number = 20, count = 25)
				print(item," : ",cci_val)
				if cci_val[0]>-100 and  cci_val[1]>0 and cci_val[2]<-100:
					print(self.coin_type)
					self.flag = 1
					break
				elif cci_val[0]>100 and cci_val[1]>20 and cci_val[2]<100:
					print(self.coin_type)
					self.flag = 2
					break     

		send_msg ={"buy transaction made : coin":self.coin_type}
		self.bot.send_message(chat_id = self.chat_id,text = send_msg)
		time.sleep(11)

	def sell_scenario(self):
		print(12)
		
		while(self.flag > 0):
			cci_val = self.cci(coin_type = self.coin_type, condition = "minutes/1", number = 20, count=25)
			if cci_val[0]<100 and  cci_val[1]<0 and cci_val[2]>100 and self.flag==2: #down stream
				self.flag = 0
				break
			elif(cci_val[1]<0 and self.flag==1):
				self.flag = 0
				break
			elif(cci_val[0]>100 and self.flag==1):
				self.flag = 2	
			print("waiting for selling")
			print(cci_val)
			time.sleep(60)
						#print(mas_val)
		print(1)
		send_msg ={"sell transaction made : coin":self.coin_type}
		self.bot.send_message(chat_id = self.chat_id,text = send_msg)
		time.sleep(10)
		print("sold")


	def getaccess(self):
		driver = webdriver.Chrome('/home/server2/바탕화면/chromedriver')
		driver.implicitly_wait(5)

		driver.get('https://upbit.com/home')
		driver.find_element_by_link_text('닫기').click()
		driver.find_element_by_link_text('로그인').click()
		time.sleep(1)
		driver.find_element_by_class_name('btnKakao').click()
		driver.switch_to_window(driver.window_handles[1])

		elem=driver.find_element_by_id('email')
		elem.click()
		elem.clear()
		elem.send_keys(self.email)
		elem1 = driver.find_element_by_id('password')
		elem1.click()
		elem1.clear()
		elem1.send_keys(self.password)
		driver.find_element_by_id('btn_login').click()

		time.sleep(15)
		driver.switch_to_window(driver.window_handles[0])
		driver.find_element_by_xpath('//a[@href="/exchange"]').click()

		while(True):
			if self.flag == 0:
				self.buy_scenario()
				txt = "//em[contains(text(),"+self.coin_type+")]"
				driver.find_element_by_xpath(txt).click()
				#driver.find_element_by_class_name('layerB').click()
				driver.find_element_by_xpath('//a[@class="/btn"]').click()
				driver.find_element_by_link_text('100%최대').click()
				driver.find_element_by_class_name('plus').click()
				driver.find_element_by_link_text('매수').click()
			elif self.flag >0:
				self.sell_scenario()
				driver.find_element_by_class_name('매도').click()
#				driver.find_element_by_link_text(self.coin_type).click()
				driver.find_element_by_class_name('layerB').click()
				driver.find_element_by_link_text('100%최대').click()
				driver.find_element_by_class_name('plus').click()
				driver.find_element_by_link_text('매도').click()




if __name__ == "__main__":
	machine = Upbit()
	machine.getaccess()
