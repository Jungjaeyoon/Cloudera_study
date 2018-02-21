import os
import sys
project_dir = os.path.abspath(os.getcwd())
sys.path.append(project_dir)
import time

from strategy.base_strategy import Strategy
from machine.korbit_machine import KorbitMachine
from machine.coinone_machine import CoinOneMachine
from db.mongodb.mongodb_handler import MongoDbHandler
from pusher.slack import PushSlack
import configparser, datetime, traceback, sys
from logger import get_logger
import redis
from pandas import DataFrame
import pandas as pd
import json

logger = get_logger("step_trade")

class StepTrade(Strategy):
	 
	def __init__(self, machine=None, db_handler=None, coin_type=None, pusher=None):
		if machine is None or db_handler is None:
			raise Exception("Need to machine, db, coin type, strategy")
		if isinstance(machine, KorbitMachine):
			logger.info("Korbit machine")
			self.coin_type="btc_krw"#coin_type+"_krw"
		elif isinstance(machine, CoinOneMachine):
			logger.info("CoinOne machine")
		self.coin = self.coin_type
		self.machine = machine
		self.pusher = pusher
		self.db_handler = db_handler
		self.flag = 0
		self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)
		self.token = self.redis.get(str(self.machine)+self.machine.get_username())

		if self.token == None:
			logger.info("set new token")
			saved_refresh_token = self.redis.get(str(self.machine)+self.machine.get_username()+"refresh")
			if saved_refresh_token is None:
				expire, token, refresh = self.machine.set_token(grant_type="password")
			else:
				self.machine.refresh_token = saved_refresh_token.decode("utf-8")
				expire, token, refresh = self.machine.set_token(grant_type="refresh_token")
			self.redis.set(str(self.machine)+self.machine.get_username(), token, expire-600)
			self.redis.set(str(self.machine)+self.machine.get_username()+"refresh", refresh, 2400)
			self.token = token
		else:
			self.token = self.token.decode("utf-8")
			self.machine.access_token = self.token

		logger.info(self.token)
		logger.info(self.coin_type)
		self.wallet_status = self.machine.get_wallet_status()


	def set_token(self):
		self.token = self.redis.get(str(self.machine)+self.machine.get_username())
		if self.token == None:
			logger.info("set new token")
			saved_refresh_token = self.redis.get(str(self.machine)+self.machine.get_username()+"refresh")
			if saved_refresh_token is None:
				expire, token, refresh = self.machine.set_token(grant_type="password")
			else:
				self.machine.refresh_token = saved_refresh_token.decode("utf-8")
				expire, token, refresh = self.machine.set_token(grant_type="refresh_token")
			self.redis.set(str(self.machine)+self.machine.get_username(), token, expire-600)
			self.redis.set(str(self.machine)+self.machine.get_username()+"refresh", refresh, 2400)
			self.token = token
		else:
			self.token = self.token.decode("utf-8")
			self.machine.access_token = self.token

	def cci(self):
#        self.db_handler(collection_name='candle')
		now = datetime.datetime.now()
		one_day_ago = now - datetime.timedelta(minutes=3600)
		one_day_ago_timestamp = int(one_day_ago.timestamp())

		pipeline = [{"$match":{"ts": {"$gte": one_day_ago_timestamp}, "coin":self.coin_type}}
							 ,{"$sort":{"_id":-1}},{"$limit":100},{"$sort":{"_id":1}}]
		query_result = self.db_handler.aggregate(pipeline,"coiner","candle")
		res = query_result._CommandCursor__data
#        last_price = self.machine.get_ticker(self.coin_type)["last"]

		pipeline1 = [{"$match": {"coin":self.coin_type}}
			, {"$sort": {"_id": -1}}, {"$limit": 1}]
		query_result1 = self.db_handler.aggregate(pipeline1, "coiner", "candle")
		ts = query_result1._CommandCursor__data[0]['ts']
		pipeline2 = [{"$match": {"timestamp": {"$gt": ts},"coin":self.coin_type}},
					{"$group": {"_id":"$coin",
								"min_val": {"$min": "$price"},
								"max_val": {"$max": "$price"},
								"sum_val": {"$sum": "$amount"},
								"open": {"$first": "$price"},
								"last": {"$last": "$price"},
								"ts": {"$last": "$timestamp"}
								}}]
		query_result2 = self.db_handler.aggregate(pipeline2, "coiner", "price_info")
		res1 = list(query_result2._CommandCursor__data)
		res = list(res)
		frame = DataFrame(res)
		frame1 = DataFrame(res1)
		frame = frame.append(frame1)

		constant = 0.015
		n = 14

		hi = pd.to_numeric(frame['max_val'], errors='coerce')
		lo = pd.to_numeric(frame['min_val'], errors='coerce')
		cl = pd.to_numeric(frame['last'], errors='coerce')
		vol = pd.to_numeric(frame['sum_val'], errors = 'coerce')

		frame['TP'] = (hi + lo + cl) / 3 
		CCI = pd.Series((frame['TP'] - frame['TP'].rolling(window=n).mean()) / (constant * frame['TP'].rolling(window=n).std()), name = 'CCI_' + str(n)) 
		CCI = round(CCI, 2)
		val = []
		val.append(CCI.iloc[-1])
		val.append(CCI.iloc[-1]-CCI.iloc[-2])
		val.append(CCI.iloc[-2])
 #       print(CCI.iloc[-5:])
		vol_per = round((vol.iloc[-1]-vol.iloc[-2])/vol.iloc[-2],2)
		val.append(vol_per)

		return val

	def mas(self):
		now = datetime.datetime.now()
		one_day_ago = now - datetime.timedelta(minutes=3600)
		one_day_ago_timestamp = int(one_day_ago.timestamp())

		pipeline = [{"$match":{"ts": {"$gte": one_day_ago_timestamp}, "coin":self.coin_type}}
							 ,{"$sort":{"_id":-1}},{"$limit":100},{"$sort":{"_id":1}}]
		query_result = self.db_handler.aggregate(pipeline,"coiner","candle")
		res = query_result._CommandCursor__data
#        last_price = self.machine.get_ticker(self.coin_type)["last"]

		pipeline1 = [{"$match": {"coin":self.coin_type}}
			, {"$sort": {"_id": -1}}, {"$limit": 1}]
		query_result1 = self.db_handler.aggregate(pipeline1, "coiner", "candle")
		ts = query_result1._CommandCursor__data[0]['ts']
		pipeline2 = [{"$match": {"timestamp": {"$gt": ts},"coin":self.coin_type}},
					{"$group": {"_id":"$coin",
								"min_val": {"$min": "$price"},
								"max_val": {"$max": "$price"},
								"sum_val": {"$sum": "$amount"},
								"open": {"$first": "$price"},
								"last": {"$last": "$price"},
								"ts": {"$last": "$timestamp"}
								}}]
		query_result2 = self.db_handler.aggregate(pipeline2, "coiner", "price_info")
		res1 = list(query_result2._CommandCursor__data)
		res = list(res)
		frame = DataFrame(res)
		frame1 = DataFrame(res1)
		frame = frame.append(frame1)

		frame['MA20'] = frame['last'].rolling(window=20).mean()
		frame['MA60'] = frame['last'].rolling(window=60).mean()
		val = frame['MA20'].iloc[-1] - frame['MA20'].iloc[-2]
		return val

	def buy_scenario(self):
		while(self.flag==0):
			now = datetime.datetime.now()
			print("                                                       ")       
			time.sleep(30)   
			print(now)
			coins = ['btc','eth','bch' ]
			for item in coins:
				self.coin_type=item+"_krw"
				cci_val = self.cci()
				mas_val = self.mas()
				print(self.coin_type," : ",cci_val)
				#print(self.coin_tpye," : ",mas_val)
				if cci_val[0]>0 and  cci_val[1]>0 and cci_val[2]<0 and cci_val[3]>0 :
					print(self.coin_type)
					self.flag = 1
					break
				elif cci_val[0]>100 and cci_val[1]>0 and cci_val[2]<100 and cci_val[3]>0:
					print(self.coin_type)
					self.flag = 2
					break     
		self.set_token()
		self.order_buy_transaction(machine=self.machine, db_handler=self.db_handler, coin_type=self.coin_type)
		send_msg ={"buy transaction made : coin":self.coin_type}
		self.pusher.send_message(message = send_msg)
		time.sleep(11)
		self.wallet_status = self.machine.get_wallet_status()
		print(self.wallet_status) 

 
	def sell_scenario(self):
		print(12)
		cci_val = self.cci()
		#mas_val = self.mas()
		while(self.flag > 0):
			if cci_val[0]<100 and  cci_val[1]<0 and cci_val[2]>100 and self.flag==2: #down stream
				self.flag = 0
				break
			elif(cci_val[1]<0 and self.flag==1):
				self.flag = 0
				break
			print("waiting for selling")
			print(cci_val)
			time.sleep(30)
						#print(mas_val)
		print(1)
		self.set_token()
		self.order_sell_transaction(machine=self.machine, db_handler=self.db_handler, coin_type=self.coin_type)
		send_msg ={"sell transaction made : coin":self.coin_type}
		self.pusher.send_message(message = send_msg)
		time.sleep(10)
		print("sold")
		self.wallet_status = self.machine.get_wallet_status() 
			
	def run(self):
		msg = {"krw" : self.wallet_status['krw']['avail']}
		self.pusher.send_message(message = msg)
		while(True):
			if float(self.wallet_status["krw"]["avail"])>500:
				print("buy session")
				try:
					self.buy_scenario()
				except Exception:
					continue
			else:
				print("sell session")
				try:
					self.sell_scenario()
				except Exception:
					continue
 
	def show_chart(self):
		now = datetime.datetime.now()
		one_day_ago = now - datetime.timedelta(minutes=3600)
		one_day_ago_timestamp = int(one_day_ago.timestamp())

		yesterday=now.day-1
		pipeline = [{"$match":{"ts": {"$gte": one_day_ago_timestamp}, "coin":self.coin_type}}
							 ,{"$sort":{"_id":-1}},{"$limit":50},{"$sort":{"_id":1}}]
		query_result = self.db_handler.aggregate(pipeline,"coiner","candle")
		res = query_result._CommandCursor__data

		res = list(res)
		frame = DataFrame(res)
		hi = pd.to_numeric(frame['max_val'], errors='coerce')
		lo = pd.to_numeric(frame['min_val'], errors='coerce')
		op = pd.to_numeric(frame['open'],errors='coerce')
		cl = pd.to_numeric(frame['last'], errors='coerce')
		vol = pd.to_numeric(frame['sum_val'],errors='coerce')

		fig = plt.figure(figsize=(15, 10))
		top_axes = plt.subplot2grid((4,4), (0,0), rowspan=3, colspan=4)
		bottom_axes = plt.subplot2grid((4,4), (3,0), rowspan=1, colspan=4)

		frame['MA20'] = frame['last'].rolling(window=20).mean()
		frame['MA60'] = frame['last'].rolling(window=60).mean()
		matfin.candlestick2_ohlc(top_axes, frame['open'], frame['max_val'], frame['min_val'], frame['last'], width=0.5, colorup='r', colordown='b')
		top_axes.plot(frame['MA20'], label='MA20')
		top_axes.plot(frame['MA60'], label='MA60')

		bottom_axes.plot(vol)
		
		plt.grid()
		plt.show()

if __name__ == "__main__":
	config = configparser.ConfigParser()
	config.read('conf/config.ini')
	client_id = config['KORBIT']['client_id']
	client_secret = config['KORBIT']['client_secret']
	username = config['KORBIT']['username']
	password = config['KORBIT']['password']
	mongodb = MongoDbHandler("local", "coiner", "price_info")

	korbit_machine = KorbitMachine(mode="Prod",client_id=client_id,
								   client_secret=client_secret,
								   username=username,
								   password=password)
	pusher = PushSlack()
	if len(sys.argv) > 0:
		trader = StepTrade(machine=korbit_machine, db_handler=mongodb, coin_type=None, pusher=pusher)
		trader.run()
	
