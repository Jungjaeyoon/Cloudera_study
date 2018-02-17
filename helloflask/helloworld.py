import os
from flask import Flask, make_response
import requests
from pandas import DataFrame
import pandas as pd
import datetime
import io

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
import matplotlib.finance as matfin
from io import StringIO, BytesIO

app = Flask(__name__)
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
		candle_api_path = "/v1/crix/candles/"+condition #ex)minutes/3
		url_path = self.host + candle_api_path
		coin_type = "CRIX.UPBIT.KRW-"+coin_type
		payload = {'code':coin_type, 'count':100}
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
		res = requests.get(url_path, params=payload, headers=headers)
		response_json = res.json()
		frame = DataFrame(response_json)
#		print(frame['timestamp'])
		frame = frame.dropna()
		frame.sort_values("timestamp", inplace=True)
		return frame
		#result=frame.to_json(orient='records')
		#print(result)
		#return result

@app.route('/')
def root():
	upbit = Upbit()
	frame = upbit.get_candles('BTC', 'days')
	fig = plt.figure(figsize=(20, 16))
	ax1 = fig.add_subplot(212)
	ax2 = fig.add_subplot(212)
	ax1 = plt.subplot2grid((4,4), (0,0), rowspan=3, colspan=4)
	ax2 = plt.subplot2grid((4,4), (3,0), rowspan=1, colspan=4)#    ax = fig.add_subplot(111) #    ax.xaxis.set_major_formatter(ticker.FixedLocator(time_list))
	#frame['MA20'] = frame['tradePrice'].rolling(window=20).mean()
	#frame['MA60'] = frame['tradePrice'].rolling(window=60).mean()
	print(frame)
	matfin.candlestick2_ohlc(ax1, frame['openingPrice'], frame['highPrice'], frame['lowPrice'], frame['tradePrice'], width=0.5, colorup='r', colordown='b')
	#ax1.plot(frame['MA20'], label='MA20')
	#ax1.plot(frame['MA60'], label='MA60')
	ax2.plot(frame['candleAccTradeVolume'])
	canvas=FigureCanvas(fig)
	png_output = BytesIO()
	canvas.print_png(png_output)
	response=make_response(png_output.getvalue())
	response.headers['Content-Type'] = 'image/png'
	return response

@app.route('/hello')
def hello():
	result = 'hello world'
	return result	

if __name__ == '__main__':
	app.run(host='0.0.0.0')