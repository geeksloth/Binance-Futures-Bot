import argparse
import talib as ta
from sys import exit
from os import system, path, chdir, getcwd, environ
from collections import defaultdict
import sched
import time
import logging as logginglib
import numpy as np
import  requests
from binance.um_futures import UMFutures
from binance.error import ClientError
import json
import random
import urllib3
import subprocess
import platform
from colorama import Fore, Style, init as colorama_init
from tabulate import tabulate
import math


################################################
# BinanceSloth Classes
################################################
class SlothAnalysis:
	def map(self, x, in_min, in_max, out_min, out_max):
		'''
			long map(long x, long in_min, long in_max, long out_min, long out_max) {
			return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
			}
		'''
		return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
	
	def ta_consistency(self, tfs, mode="D"):
		'''
		Default mode "D" means direction, return -1, 0, 1 stand for
		consistence neg, not consistence, and consistence pos consequently.
		"N" mode returns score -100 to 100
		'''
		consist = 0
		tf_count = len(tfs)
		for _, tf_v in tfs.items():
			if tf_v > 0:
				consist += 1
			else:
				consist -= 1
		consist = consist/tf_count

		if mode == "N":
			return consist
		elif mode == "D":
			if consist == 100:
				return 1
			elif consist == -100:
				return -1
			else:
				return 0
		else:
			return consist

	def ta_ema(self, data, ta_ema=5):
		return round(ta.EMA(data, ta_ema)[-2], 2)

	def ta_ma(self, data, ta_ma=5):
		return round(ta.MA(data, ta_ma)[-2], 4)

	def ta_ema_comp_cross(self, data, ema_small=5, ema_large=10):
		#
		# p and n stand for positive and negative respectively
		#
		emas_small = ta.EMA(data, ema_small)
		emas_large = ta.EMA(data, ema_large)

		if ((emas_small[-4]-emas_large[-4]) > 0) and ((emas_small[-3]-emas_large[-3]) > 0) and ((emas_small[-2]-emas_large[-2]) > 0):
			return"ppp"
		elif ((emas_small[-4]-emas_large[-4]) > 0) and ((emas_small[-3]-emas_large[-3]) > 0) and ((emas_small[-2]-emas_large[-2]) <= 0):
			return "ppn"
		elif ((emas_small[-4]-emas_large[-4]) > 0) and ((emas_small[-3]-emas_large[-3]) <= 0) and ((emas_small[-2]-emas_large[-2]) > 0):
			return "pnp"
		elif ((emas_small[-4]-emas_large[-4]) > 0) and ((emas_small[-3]-emas_large[-3]) <= 0) and ((emas_small[-2]-emas_large[-2]) <= 0):
			return "pnn"
		elif ((emas_small[-4]-emas_large[-4]) <= 0) and ((emas_small[-3]-emas_large[-3]) > 0) and ((emas_small[-2]-emas_large[-2]) > 0):
			return "npp"
		elif ((emas_small[-4]-emas_large[-4]) <= 0) and ((emas_small[-3]-emas_large[-3]) > 0) and ((emas_small[-2]-emas_large[-2]) <= 0):
			return "npn"
		elif ((emas_small[-4]-emas_large[-4]) <= 0) and ((emas_small[-3]-emas_large[-3]) <= 0) and ((emas_small[-2]-emas_large[-2]) > 0):
			return "nnp"
		elif ((emas_small[-4]-emas_large[-4]) <= 0) and ((emas_small[-3]-emas_large[-3]) <= 0) and ((emas_small[-2]-emas_large[-2]) <= 0):
			return "nnn"

	def ta_ema_vector(self, data, ta_ema=5, depth=3, step=1):
		#
		# u and d stand for up and down respectively
		#
		emas = ta.EMA(data, ta_ema)
		if depth == 2:
			if emas[-(step+3)] > emas[-(step+2)] >  emas[-(step+1)]:
				return "dd"
			elif emas[-(step+3)] > emas[-(step+2)] <= emas[-(step+1)]:
				return "du"
			elif emas[-(step+3)] <= emas[-(step+2)] > emas[-(step+1)]:
				return "ud"
			elif emas[-(step+3)] <= emas[-(step+2)] <= emas[-(step+1)]:
				return "uu"
		elif depth == 3:
			if emas[-(step+4)] > emas[-(step+3)] > emas[-(step+2)] >  emas[-(step+1)]:
				return "ddd"
			elif emas[-(step+4)] > emas[-(step+3)] > emas[-(step+2)] <= emas[-(step+1)]:
				return "ddu"
			elif emas[-(step+4)] > emas[-(step+3)] <= emas[-(step+2)] > emas[-(step+1)]:
				return "dud"
			elif emas[-(step+4)] > emas[-(step+3)] <= emas[-(step+2)] <= emas[-(step+1)]:
				return "duu"
			elif emas[-(step+4)] <= emas[-(step+3)] > emas[-(step+2)] > emas[-(step+1)]:
				return "udd"
			elif emas[-(step+4)] <= emas[-(step+3)] > emas[-(step+2)] <= emas[-(step+1)]:
				return "udu"
			elif emas[-(step+4)] <= emas[-(step+3)] <= emas[-(step+2)] > emas[-(step+1)]:
				return "uud"
			elif emas[-(step+4)] <= emas[-(step+3)] <= emas[-(step+2)] <= emas[-(step+1)]:
				return "uuu"

	def ta_macd_delta(self, data, ema_small, ema_large):
		return round(ta.EMA(data, ema_small)[-2]-ta.EMA(data, ema_large)[-2], 2)

	def ta_macd(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
		_, _, macdhist = ta.MACD(data, fastperiod, slowperiod, signalperiod)
		return round(macdhist[-2], 2)

	def ta_macd_vector(self, data, fastperiod=12, slowperiod=26, signalperiod=9, step=1):
		#
		# u and d stand for up and down respectively
		#
		if len(data)*2 <= slowperiod:
			return "not enough data."
		else:
			_, _, macdhist = ta.MACD(data, fastperiod, slowperiod, signalperiod)
			if macdhist[-(step+4)] > macdhist[-(step+3)] > macdhist[-(step+2)] >  macdhist[-(step+1)]:
				return "ddd"
			elif macdhist[-(step+4)] > macdhist[-(step+3)] > macdhist[-(step+2)] <= macdhist[-(step+1)]:
				return "ddu"
			elif macdhist[-(step+4)] > macdhist[-(step+3)] <= macdhist[-(step+2)] > macdhist[-(step+1)]:
				return "dud"
			elif macdhist[-(step+4)] > macdhist[-(step+3)] <= macdhist[-(step+2)] <= macdhist[-(step+1)]:
				return "duu"
			elif macdhist[-(step+4)] <= macdhist[-(step+3)] > macdhist[-(step+2)] > macdhist[-(step+1)]:
				return "udd"
			elif macdhist[-(step+4)] <= macdhist[-(step+3)] > macdhist[-(step+2)] <= macdhist[-(step+1)]:
				return "udu"
			elif macdhist[-(step+4)] <= macdhist[-(step+3)] <= macdhist[-(step+2)] > macdhist[-(step+1)]:
				return "uud"
			elif macdhist[-(step+4)] <= macdhist[-(step+3)] <= macdhist[-(step+2)] <= macdhist[-(step+1)]:
				return "uuu"

	def ta_macd_zcross(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
		#
		# p and n stand for positive and negative respectively
		#
		_, _, macdhist = ta.MACD(data, fastperiod, slowperiod, signalperiod)
		if macdhist[-4] > 0 and macdhist[-3] > 0 and macdhist[-2] > 0:
			return"ppp"
		elif macdhist[-4] > 0 and macdhist[-3] > 0 and macdhist[-2] <= 0:
			return "ppn"
		elif macdhist[-4] > 0 and macdhist[-3] <= 0 and macdhist[-2] > 0:
			return "pnp"
		elif macdhist[-4] > 0 and macdhist[-3] <= 0 and macdhist[-2] <= 0:
			return "pnn"
		elif macdhist[-4] <= 0 and macdhist[-3] > 0 and macdhist[-2] > 0:
			return "npp"
		elif macdhist[-4] <= 0 and macdhist[-3] > 0 and macdhist[-2] <= 0:
			return "npn"
		elif macdhist[-4] <= 0 and macdhist[-3] <= 0 and macdhist[-2] > 0:
			return "nnp"
		elif macdhist[-4] <= 0 and macdhist[-3] <= 0 and macdhist[-2] <= 0:
			return "nnn"

	def ta_insideway(self, rsi, ovs=40, ovb=60):
		'''
		input rsi 0 to 100, output -100 to 100. -100 means recommend to short, and vice versa.
		'''
		score = 0
		if rsi <= ovb and rsi >= ovs:
			return score
		elif rsi > ovb:
			return self.map(rsi, ovb, 100, 0, 100)
		elif rsi < ovs:
			return self.map(rsi, 0, ovs, -100, 0)

	def ta_rsi(self, data, value=6):
		return round(ta.RSI(data, value)[-2], 2)

	def ta_rsi_vector(self, data, value=6, step=1):
		rsis = ta.RSI(data, value)
		if rsis[-(step+4)] > rsis[-(step+3)] > rsis[-(step+2)] >  rsis[-(step+1)]:
			return "ddd"
		elif rsis[-(step+4)] > rsis[-(step+3)] > rsis[-(step+2)] <= rsis[-(step+1)]:
			return "ddu"
		elif rsis[-(step+4)] > rsis[-(step+3)] <= rsis[-(step+2)] > rsis[-(step+1)]:
			return "dud"
		elif rsis[-(step+4)] > rsis[-(step+3)] <= rsis[-(step+2)] <= rsis[-(step+1)]:
			return "duu"
		elif rsis[-(step+4)] <= rsis[-(step+3)] > rsis[-(step+2)] > rsis[-(step+1)]:
			return "udd"
		elif rsis[-(step+4)] <= rsis[-(step+3)] > rsis[-(step+2)] <= rsis[-(step+1)]:
			return "udu"
		elif rsis[-(step+4)] <= rsis[-(step+3)] <= rsis[-(step+2)] > rsis[-(step+1)]:
			return "uud"
		elif rsis[-(step+4)] <= rsis[-(step+3)] <= rsis[-(step+2)] <= rsis[-(step+1)]:
			return "uuu"
		return None

	def ta_sar(self, data, timeperiod=30):
		return ta.SAR(data.high, data.low, acceleration=0, maximum=0)

	def ta_vector_fibo(self, vals):
		score = 0
		if vals[0] == "n" or vals[0] == "d":
			score -= 21
		else:
			score += 21
		if vals[1] == "n" or vals[1] == "d":
			score -= 34
		else:
			score += 34
		if vals[2] == "n" or vals[2] == "d":
			score -= 55
		else:
			score += 55
		return self.map(score, -110, 110, -100, 100)

class BinanceSloth(SlothAnalysis):
	def __init__(self, pair):
		#c configuration loading and LINE test
		self.pair = pair
		self.symbol = self.pair["crypto"]+self.pair["asset"]
		self.positionStatus = None
		self.prefix = LOGGER.tint(self.symbol, color=self.pair["color"])

		# Test logging
		#LOGGER.testLogging()

		# Binance Futures preparation
		#self.connect()
		self.fetch()
		#exit()
		#self.test()

	def getAsset(self, name="USDT"):
		if self.fetch():
			assets = self.account["assets"]
			for asset in assets:
				if asset["asset"] == name:
					return asset
			return False 

	def fetch(self):
		if self.connect():
			self.position = FUTURES.get_position_risk(symbol=self.symbol)[0]
			#LOGGER.pprint(self.position)
			self.account = FUTURES.account()
			if float(self.position["positionAmt"]) > 0:
				self.positionStatus = "longed"
			elif float(self.position["positionAmt"]) < 0:
				self.positionStatus = "shorted"
			else:
				self.positionStatus = "closed"
			return True
		else:
			return False

	def map(self, x, in_min, in_max, out_min, out_max):
		'''
			long map(long x, long in_min, long in_max, long out_min, long out_max) {
			return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
			}
		'''
		return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
	
	def round_decimals_down(number:float, decimals:int=2):
		"""
		Returns a value rounded down to a specific number of decimal places.
		"""
		if not isinstance(decimals, int):
			raise TypeError("decimal places must be an integer")
		elif decimals < 0:
			raise ValueError("decimal places has to be 0 or more")
		elif decimals == 0:
			return math.floor(number)

		factor = 10 ** decimals
		return math.floor(number * factor) / factor
	
	def round_decimals_up(number:float, decimals:int=2):
		"""
		Returns a value rounded up to a specific number of decimal places.
		round_decimals_up(8.343)
		# Returns: 8.35
		"""
		if not isinstance(decimals, int):
			raise TypeError("decimal places must be an integer")
		elif decimals < 0:
			raise ValueError("decimal places has to be 0 or more")
		elif decimals == 0:
			return math.ceil(number)

		factor = 10 ** decimals
		return math.ceil(number * factor) / factor

	def maxQty(self, percent=None):
		if percent is None:
			percent = self.pair["used_asset_percent"]
		ex_info = FUTURES.exchange_info()
		filter = None
		for symbol in ex_info["symbols"]:
			if symbol["symbol"] == self.symbol:
				for filt in symbol["filters"]:
					if filt["filterType"] == "MARKET_LOT_SIZE":
						filter = filt
		assetUsed = (percent/100*float(self.account["availableBalance"]))
		markPrice = float(FUTURES.mark_price(symbol=self.symbol)["markPrice"])
		minPriceBuyable = markPrice * float(filter["minQty"])
		leverage = self.get_leverage()
		# I spent many hours for the following line!
		maximumQty = int(assetUsed*leverage/minPriceBuyable) * float(filter["stepSize"])
		return maximumQty

	def cal_QTY2(self, percent=None):
		if percent is None:
			percent = self.pair["used_asset_percent"]
		ex_info = FUTURES.exchange_info()
		filter = None
		for symbol in ex_info["symbols"]:
			if symbol["symbol"] == self.symbol:
				for filt in symbol["filters"]:
					if filt["filterType"] == "MARKET_LOT_SIZE":
						filter = filt
						LOGGER.pprint(filt)
		assetUsed = (percent/100*float(self.account["availableBalance"]))
		markPrice = float(FUTURES.mark_price(symbol=self.symbol)["markPrice"])
		minPriceBuyable = markPrice * float(filter["minQty"])
		stepSize = float(filter["stepSize"])
		leverage = self.get_leverage()
		if filter["minQty"].rfind(".") > -1:
			_, deci = filter["minQty"].split(".")
			quantityPrecision = len(deci)
		else:
			quantityPrecision = 0
		minimumQty = max(
			float(filter["minQty"]),
			self.round_decimals_up(
				(float(filter["stepSize"]) / markPrice),
				quantityPrecision
			)
		)
		# I spent many hours for the following line!
		maximumQty = int(assetUsed*leverage/minPriceBuyable) * float(filter["stepSize"])
		'''
		print("assetUsed:{} ".format(assetUsed))
		print("markPrice:{} ".format(markPrice))
		print("minPriceBuyable:{} ".format(minPriceBuyable))
		print("quantityPrecision:{} ".format(quantityPrecision))
		print("minimumQty:{} ".format(minimumQty))
		print("maximumQty: {}".format(maximumQty))
		print("MAX: {}".format(maximumQty*minPriceBuyable))
		'''
		return maximumQty

	'''
	def cal_QTY(self, price, percent=None):
		# under implementation! This could return the float, not int!?
		if percent is None:
			percent = self.pair["used_asset_percent"]
		qty = float(self.cal_QTY_max(float(price), percent) * self.minimum_order_amt)
		qty = self.float_trim(qty, 3)
		print("QTY: {}".format(qty))
		#qty=5.0
		return qty

	def cal_QTY_max(self, price, percent):
		# under implementation! This could return the float, not int!?
		return float((percent/100*float(self.account["availableBalance"]))/self.cal_initMargin(float(price)))

	def cal_initMargin(self, price):
		ex_info = FUTURES.exchange_info()
		for symbol in ex_info["symbols"]:
			if symbol["symbol"] == self.symbol:
				#LOGGER.pprint(symbol["filters"])
				for filter in symbol["filters"]:
					if filter["filterType"] == "MARKET_LOT_SIZE":
						LOGGER.pprint(filter)
						self.minimum_order_amt = float(filter["minQty"])
						self.minimum_order_stepSize = float(filter["stepSize"])
		result = float(float(price)*self.minimum_order_amt/self.get_leverage())
		print("cal_initMargin:{} ".format(result))
		return result
	'''

	def get_leverage(self):
		if self.fetch():
			for position in self.account["positions"]:
				if position["symbol"] in CONFIG["symbols"]:
					return int(position["leverage"])
			return False

	def float_trim(self, input, decimal):
		x_str = str(input)
		x = x_str.split(".")
		result = str(x[0])+"."+str(x[1][:decimal])
		return(float(result))

	def long(self, quantity=None):
		if self.connect():
			if quantity is None:
				quantity = self.maxQty()
			params = {
				'symbol': self.symbol,
				'side': 'BUY',
				'type': 'MARKET',
				'quantity': abs(quantity)
			}
			try:
				if self.pair["testOrder"]:
					response = FUTURES.new_order_test(**params)
				else:
					response = FUTURES.new_order(**params)
				time.sleep(1)
				LOGGER.success("{} just open {} position.".format(self.prefix, LOGGER.tint("LONG", color="success")))
			except ClientError as e:
				LOGGER.warning("{} LONG with {} {} failed. {}".format(self.prefix, quantity, self.pair["crypto"], e))
				response = e
				#LOGGER.pprint(response.error_message)
				LINE.notify("{}, LONG failed. {}".format(CONFIG["BinanceAPI"]["name"], response.error_message))
			else:
				self.positionStatus = "longed"

			return response

	def short(self, quantity=None):
		if self.connect():
			if quantity is None:
				quantity = self.maxQty()
			params = {
				'symbol': self.symbol,
				'side': 'SELL',
				'type': 'MARKET',
				'quantity': abs(quantity)
			}
			try:
				if self.pair["testOrder"]:
					response = FUTURES.new_order_test(**params)
				else:
					response = FUTURES.new_order(**params)
				time.sleep(1)
				LOGGER.success("{} just open {} position.".format(self.prefix, LOGGER.tint("SHORT", color="success")))
			except ClientError as e:
				LOGGER.warning("{} SHORT with {} {} failed. {}".format(self.prefix, quantity, self.pair["crypto"], e))
				response = e
				#LOGGER.pprint(response.error_message)
				LINE.notify("{}, SHORT failed. {}".format(CONFIG["BinanceAPI"]["name"], response.error_message))
			else:
				self.positionStatus = "shorted"
			return response

	def fetch_klines(self, tf="15m", samples=50):
		'''
		response (for SOLUSDT):
		[
			[
				1701621900000,	// Open time
				"62.8270",		// Open
				"63.0830",		// High
				"62.7870",		// Low
				"62.8900",		// Close
				"119247",		// Volume
				1701622799999,	// Close time
				"7505644.4280",	// Quote asset volume
				8325,			// Number of trades
				"66790",		// Taker buy base asset volume
				"4203732.1250",	// Taker buy quote asset volume
				"0"				// Ignore.
			]
		]
		'''
		klines = FUTURES.klines(symbol=self.symbol, interval=tf, limit=samples)
		return klines

	def fetch_closes(self, tf="15m", samples=50):
		return_data = []
		klines = self.fetch_klines(tf, samples)
		for kline in klines:
			return_data.append(float(kline[4]))
		#LOGGER.pprint(return_data)
		return np.array(return_data)

	def close(self):
		if self.fetch():
			if self.positionStatus == "shorted":
				self.long(float(self.position["positionAmt"]))
				self.positionStatus = "closed"
				LOGGER.general("{} SHORT position is just {}.".format(self.prefix, LOGGER.tint("closed", color="success")))
			elif self.positionStatus == "longed":
				self.short(float(self.position["positionAmt"]))
				self.positionStatus = "closed"
				LOGGER.general("{} LONG position is just {}.".format(self.prefix, LOGGER.tint("closed", color="success")))
			else:
				LOGGER.general("{} The position is already closed.".format(self.prefix))

	def test(self):
		if self.connect():
			LOGGER.pprint(FUTURES.get_orders())


	def connect(self, retrySecondMin=5, incrementSecond=10, timeout=60*1):
		seconds = retrySecondMin
		connectionPassed = 0
		connectionTotal = 1 #some situation might require more than 1 successful connection to make sure
		while connectionPassed < connectionTotal:
			try:
				FUTURES.ping()
			except:
				LOGGER.warning("API connection failed, retry in {} seconds".format(seconds))
				time.sleep(seconds)
				if seconds < timeout:
					seconds += incrementSecond
				else:
					return False
			else:
				LOGGER.debug("API connected")
				connectionPassed += 1
				return True

	def run(self):
		if self.pair["strategy"] == "MACDrider":
			# Open when MA25 crosses MA99, close when MA25 reverses direction
			indy = defaultdict(dict)
			data = defaultdict(dict)
			tf = "1h"
			data = self.fetch_closes(tf)
			ma7 = self.ta_ma(data, 7)
			ma25 = self.ta_ma(data, 25)
			#LOGGER.pprint(ma7)
			#LOGGER.pprint(ma25)
			
			if self.positionStatus == "closed":
				if ma7 > ma25:
					self.long()
				else:
					self.short()
			elif self.positionStatus == "longed":
				if ma7 < ma25:
					self.close()
					time.sleep(1)
					self.short()
			elif self.positionStatus == "shorted":
				if ma7 > ma25:
					self.close()
					time.sleep(1)
					self.long()
		elif self.pair["strategy"] == "MA25xMA99":
			indy = defaultdict(dict)
			data = defaultdict(dict)
			tf = "4h"
			data = self.fetch_closes(tf, samples=200)
			ma25 = self.ta_ma(data, 25)
			ma99 = self.ta_ma(data, 99)
			#LOGGER.pprint(ma25)
			#LOGGER.pprint(ma99)

			if self.positionStatus == "closed":
				if ma25 > ma99:
					self.long()
				else:
					self.short()
			elif self.positionStatus == "longed":
				if ma25 < ma99:
					self.close()
					time.sleep(1)
					self.short()
			elif self.positionStatus == "shorted":
				if ma25 > ma99:
					self.close()
					time.sleep(1)
					self.long()
		elif self.pair["strategy"] == "K90_v1":
			indy = defaultdict(dict)
			data = defaultdict(dict)
			criterion = defaultdict(dict)
			k = defaultdict(dict)

			criterion["rsi_oversold"] = 40
			criterion["rsi_overbought"] = 60
			criterion["long_if_over"] = 33
			criterion["close_longed_if_below"] = 30
			criterion["short_if_below"] = -33
			criterion["close_shorted_if_over"] = -30
			
			#tfs = ["5m", "15m", "1h"]
			tfs = ["1h", "4h"]
			tfs_weight = [1, 2]
			k_weights = [
				#[2, 3, 3, 2], #fibo_macd_v, macd_zcross, rsi_v, insideway
				[1, 1, 1, 1],
				[2, 3, 3, 2]
				]

			'''
			prepare indicator values to be used in analysis process
			'''
			for tf in tfs:
				data[tf] = self.fetch_closes(tf)
				#indy[tf]["macd"] = self.ta_macd(data[tf])
				indy[tf]["macd_v"] = self.ta_macd_vector(data[tf])
				indy[tf]["macd_zcross"] = self.ta_macd_zcross(data[tf])
				indy[tf]["rsi"] = self.ta_rsi(data[tf])
				indy[tf]["rsi_v"] = self.ta_rsi_vector(data[tf])
				indy[tf]["insideway"] = self.ta_insideway(
					indy[tf]["rsi"],
					criterion["rsi_oversold"],
					criterion["rsi_overbought"]
				)
			#LOGGER.pprint(indy)
			'''
			Calculate k_results for each timeframe, which is including fibo_macd_v, macd_zcross, rsi_v, and insideway consequently.
			This segtion can be further designed more complex as desire.
			'''
			k_results = defaultdict(dict)
			weight_counter = 0
			for tf in tfs:
				k[tf]["fibo_macd_v"] = k_weights[weight_counter][0] * self.ta_vector_fibo(indy[tf]["macd_v"])
				k[tf]["macd_zcross"] = k_weights[weight_counter][1] * self.ta_vector_fibo(indy[tf]["macd_zcross"])
				k[tf]["rsi_v"] = k_weights[weight_counter][2] * self.ta_vector_fibo(indy[tf]["rsi_v"])
				k[tf]["insideway"] = k_weights[weight_counter][3] * indy[tf]["insideway"]
				k_result = (
					k[tf]["fibo_macd_v"]
					+ k[tf]["macd_zcross"]
					+ k[tf]["rsi_v"]
					+ k[tf]["insideway"]
					) / sum(k_weights[weight_counter])
				#self.pprint(k)
				weight_counter += 1
				k_results[tf] = k_result
			#LOGGER.pprint(k)
			#LOGGER.pprint(k_results)
			'''
			Final segtion which will calculate the K_score,
			which will be used as the criteria in openning the long or close position.
			'''
			weight_counter = 0
			K_score = 0
			for tf in tfs:
				K_score += k_results[tf]*tfs_weight[weight_counter]
				weight_counter += 1
			K_score = K_score / sum(tfs_weight)
			LOGGER.info(str(round(K_score, 2)))
			#LOGGER.debug(str(self.ta_consistency(k_results)))
			'''
			After we've achived the K_score, the OUR INCREDIBLE FACTOR, then the actual trading is coming below...
			'''
			#LOGGER.info(K_score)
			if self.positionStatus == "closed":
				if K_score >= criterion["long_if_over"]:
					try:
						self.long()
					except KeyError as e:
						LOGGER.error(e)
				elif K_score <= criterion["short_if_below"]:
					try:
						self.short()
					except KeyError as e:
						LOGGER.error(e)
				else:
					LOGGER.info("{} K_score: {}, sit on hands and keep waiting.".format(self.symbol, round(K_score, 2)))
			elif self.positionStatus == "longed":
				if K_score < criterion["close_longed_if_below"]:
					try:
						self.close()
						LOGGER.info("{} K_score: {}, longed position just closed".format(self.symbol, round(K_score, 2)))
					except KeyError as e:
						LOGGER.error(e)
				else:
					LOGGER.info("{} K_score: {}, let {} profit run".format(self.symbol, round(K_score), self.positionStatus))
			elif self.positionStatus == "shorted":
				if K_score > criterion["close_shorted_if_over"]:
					try:
						self.close()
						LOGGER.info("{} K_score: {}, shorted position just closed".format(self.symbol, round(K_score, 2)))
					except KeyError as e:
						LOGGER.error(e)
				else:
					LOGGER.info("{} K_score: {}, let {} profit run".format(self.symbol, round(K_score), self.positionStatus))
			else:
				LOGGER.warning("{} self.positionStatus: {}".format(self.symbol, self.positionStatus))
			#LOGGER.pprint(indy)

		elif self.pair["strategy"] == "test":
			time.sleep(5)
			'''
			tf="3m"
			data = self.fetch_closes(tf, 100)
			self.pprint(self.ta_rsi_vector(data))
			'''
		elif self.pair["strategy"] == "testOpenOrder":
			tf="15m"
			data = self.fetch_closes(tf, 1)
			LOGGER.info("testing long...")
			self.long()
			time.sleep(5)
			LOGGER.info("testing close...")
			self.close()
			time.sleep(5)
			LOGGER.info("testing short...")
			self.short()
			time.sleep(5)
			LOGGER.info("testing close...")
			self.close()
			LOGGER.info("end test strategy")
		elif self.pair["strategy"] == "MACDez":
			pass
		else:
			LOGGER.warning("{} strategy not available!".format(self.prefix))

		LOGGER.general("{} is {}".format(self.prefix, LOGGER.tint("running", color="success")))
		if(self.positionStatus == "closed"):
			SCHEDULER.enter(self.pair["interval_when_closed"], self.pair["priority"], self.run)
		else:
			SCHEDULER.enter(self.pair["interval_when_opened"], self.pair["priority"], self.run)

class Test:
	def testTAlib():
		c = np.random.randn(100)
		k, d = ta.STOCHRSI(c)
		rsi = ta.RSI(c)
		k, d = ta.STOCHF(rsi, rsi, rsi)
		rsi = ta.RSI(c)
		k, d = ta.STOCH(rsi, rsi, rsi)
		print("TA-lib OK") 

class Line:
	def __init__(self, lineApi, lineToken, lineEnable):
		self.lineApi = lineApi
		self.lineToken = lineToken
		self.headers = {'Authorization':'Bearer '+self.lineToken}
		self.lineEnable = lineEnable

	def notify(self, msg):
		if self.lineEnable:
			try:
				return requests.post(
					self.lineApi,
					headers=self.headers,
					data = {'message':msg},
					files=None
				)
			except KeyError as e:
				print(e)
class Logging:
	def __init__(self, loggingLevel="INFO"):
		self.logging = None
		self.loggingLevel = loggingLevel
		logger = logginglib.getLogger()
		if self.loggingLevel.upper() == "DEBUG":
			logger.setLevel(logginglib.DEBUG)
		elif self.loggingLevel.upper() == "INFO":
			logger.setLevel(logginglib.INFO)
		elif self.loggingLevel.upper() == "WARNING":
			logger.setLevel(logginglib.WARNING)
		elif self.loggingLevel.upper() == "ERROR":
			logger.setLevel(logginglib.ERROR)
		elif self.loggingLevel.upper() == "CRITICAL":
			logger.setLevel(logginglib.CRITICAL)
		else:
			print("loggingLevel invalid [{}]".format(self.loggingLevel))
			logger.setLevel(logginglib.DEBUG)
		sh = logginglib.StreamHandler()
		sh.setFormatter(logginglib.Formatter('[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S'))
		logger.addHandler(sh)
		self.logging = logger

	def debug(self, msg):
		self.logging.debug(self.tint(msg, "LIGHTBLACK_EX"))

	def general(self, msg):
		self.logging.info(msg) 

	def info(self, msg):
		self.logging.info(self.tint(msg, "LIGHTBLUE_EX"))
	
	def success(self, msg):
		self.logging.info(self.tint(msg, "LIGHTGREEN_EX"))

	def warning(self, msg):
		self.logging.warning(self.tint(msg, "LIGHTYELLOW_EX"))

	def error(self, msg):
		self.logging.error(self.tint(msg, "LIGHTRED_EX"))

	def critical(self, msg):
		self.logging.critical(self.tint(msg, "LIGHTMAGENTA_EX"))

	def pprint(self, msg):
		print(json.dumps(msg, indent=4, sort_keys=False))

	def pretty(self, msg):
		return(json.dumps(msg, indent=4, sort_keys=False))

	def tint(self, msg, color=None):
		if color is None:
			color = self.color
		if color == "LIGHTBLACK_EX":
			return Fore.LIGHTBLACK_EX+msg+Style.RESET_ALL
		elif color == "LIGHTBLUE_EX" or color == "info":
			return Fore.LIGHTBLUE_EX+msg+Style.RESET_ALL
		elif color == "LIGHTCYAN_EX":
			return Fore.LIGHTCYAN_EX+msg+Style.RESET_ALL
		elif color == "LIGHTGREEN_EX" or color == "success":
			return Fore.LIGHTGREEN_EX+msg+Style.RESET_ALL
		elif color == "LIGHTMAGENTA_EX" or color == "critical":
			return Fore.LIGHTMAGENTA_EX+msg+Style.RESET_ALL
		elif color == "LIGHTRED_EX" or color == "danger":
			return Fore.LIGHTRED_EX+msg+Style.RESET_ALL
		elif color == "LIGHTWHITE_EX":
			return Fore.LIGHTWHITE_EX+msg+Style.RESET_ALL
		elif color == "LIGHTYELLOW_EX" or color == "warning":
			return Fore.LIGHTYELLOW_EX+msg+Style.RESET_ALL
		else:
			return msg

	def printTint(self, msg, color=None):
		print(self.tint(msg, color))

	def testLogging(self):
		self.debug("debug msg")
		self.general("general msg")
		self.info("info msg")
		self.success("success msg")
		self.warning("warning msg")
		self.error("error msg")
		self.critical("critical msg")

class Utils:
	def __init__(self):
		pass

	def getTemp_CPU(self):
		response = subprocess.run(['cat', '/sys/class/thermal/thermal_zone0/temp'], stdout=subprocess.PIPE)
		return ''.join(e for e in str(response.stdout) if e.isnumeric())

	def ping(self, hostname="www.google.com", count=1):
		response = None
		if platform.system() == "Linux":
			response = system("ping -c " + str(count) + " " + hostname + " > /dev/null 2>&1")
		elif platform.system() == "Windows":
			response = system("ping -n " + str(count) + " " + hostname + " > $null ")
		if response == 0:
			return 1
		else:
			return 0

	def waitForInternet(self, retry_sec_min=1, increment_sec=10, retry_sec_max=60*3):
		seconds = retry_sec_min
		while not self.ping():
			LOGGER.warning(
				"internet connection "+Fore.RED+"failed"+Style.RESET_ALL
				+", retry in "+Fore.GREEN+"{}".format(seconds)+Style.RESET_ALL+" second(s)"
			)
			time.sleep(seconds)
			if seconds < retry_sec_max:
				seconds += increment_sec
		return True

	def sleep(self, min=1, max=-1):
		if max == -1:
			time.sleep(min)
		else:
			time.sleep(random.randint(min, max))

	def float_trim(self, input, decimal):
		x_str = str(input)
		x = x_str.split(".")
		result = str(x[0])+"."+str(x[1][:decimal])
		return(float(result))

class Reporter():
	def __init__(self, interval, priority):
		self.interval=interval
		self.priority=priority

	def connect(self, retrySecondMin=5, incrementSecond=10, timeout=60*1):
		seconds = retrySecondMin
		connectionPassed = 0
		connectionTotal = 1 #some situation might require more than 1 successful connection to make sure
		while connectionPassed < connectionTotal:
			try:
				FUTURES.ping()
			except:
				LOGGER.error("API connection failed, retry in {} seconds".format(seconds))
				time.sleep(seconds)
				if seconds < timeout:
					seconds += incrementSecond
				else:
					return False
			else:
				connectionPassed += 1
				return True
			
	def report(self):
		if self.connect():
			account = FUTURES.account()
			acc_info = "totalWalletBalance: [{}], totalCrossUnPnl: [{}], ".format(
				LOGGER.tint(str(round(float(account["totalWalletBalance"]), 4)), color="success"),
				LOGGER.tint(str(round(float(account["totalCrossUnPnl"]), 4)), color="success")
			)
			for asset in account["assets"]:
				if asset["asset"] in CONFIG["assets"]:
					acc_info += asset["asset"] + ": [" + LOGGER.tint(str(round(float(asset["availableBalance"]), 4)), color="success") + "] "

			headers_pairs = [
				"Symbol",
				"Side",
				"Amount",
				"x",
				"UnPnl",
				"UseAsset",
				"Strategy"
			]
			row_pairs = []
			for position in account["positions"]:
				if position["symbol"] in CONFIG["symbols"]:
					row = [
						LOGGER.tint(position["symbol"], color=CONFIG_DICT["pairs"][position["symbol"]]["color"]),
						position["positionSide"],
						round(float(position["positionAmt"]), 4),
						position["leverage"],
						round(float(position["unrealizedProfit"]), 2),
						str(CONFIG_DICT["pairs"][position["symbol"]]["used_asset_percent"])+"%",
						CONFIG_DICT["pairs"][position["symbol"]]["strategy"]
					]
					row_pairs.append(row)
			global global_firstRun
			if global_firstRun:
				LINE.notify("{}, totalWalletBalance: [{}], totalCrossUnPnl: [{}]".format(
					CONFIG["BinanceAPI"]["name"],
					str(round(float(account["totalWalletBalance"]), 4)),
					str(round(float(account["totalCrossUnPnl"]), 4))
				))
				global_firstRun = False
			LOGGER.general(acc_info+"\n"+tabulate(row_pairs, headers_pairs, tablefmt="pretty"))
		SCHEDULER.enter(self.interval, self.priority, self.report)

	
# ########
# MAIN SECTION
# ########
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
colorama_init(autoreset=True)
global_firstRun = True
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="GeekSloth's Binance bot")
	parser.add_argument("-c", "--config", help="configuration JSON file", default="config.json")
	args = vars(parser.parse_args())

	while True:
		CONFIG = None
		CONFIG_DICT = defaultdict(dict)
		if path.exists(args["config"]):
			# ########
			# Configuration file loading.
			# Additional keys for efficient processing.
			# ########
			try:
				f = open(args["config"], encoding = 'utf-8')
				CONFIG = json.load(f)
				f.close()
				print("{} loaded".format(args["config"]))
			except KeyError as e:
				raise Exception(e)
			if CONFIG["customWD"]["enable"]:
				if platform.system() == "Linux":
					chdir(CONFIG["customWD"]["linux"])
				elif platform.system() == "Windows":
					chdir(CONFIG["customWD"]["windows"])
				else:
					print("Operating system unknown. Invalid WD might cause an error.")
			i = 0
			for pair in CONFIG["pairs"]:
				if pair["enable"]:
					# add symbol key to each pair
					CONFIG["pairs"][i]["symbol"] = pair["crypto"]+pair["asset"]
					# make dictionary for easier access
					CONFIG_DICT["pairs"][str(pair["crypto"]+pair["asset"])] = pair
			CONFIG["assets"] = []
			CONFIG["symbols"] = []
			for pair in CONFIG["pairs"]:
				if pair["enable"]:
					if pair["asset"] not in CONFIG["assets"]:
						CONFIG["assets"].append(pair["asset"])
					if pair["crypto"]+pair["asset"] not in CONFIG["symbols"]:
						CONFIG["symbols"].append(pair["crypto"]+pair["asset"])
			
			# ########
			# Essential objects and functions construction
			# ########
			environ['TZ'] = CONFIG["timezone"]
			time.tzset()
			SCHEDULER = sched.scheduler(time.time, time.sleep)
			FUTURES = UMFutures(
				key=CONFIG["BinanceAPI"]["key"],
				secret=CONFIG["BinanceAPI"]["secret"]
			)
			LINE = Line(
				lineApi=CONFIG["LINE"]["api"],
				lineToken=CONFIG["LINE"]["token"],
				lineEnable=CONFIG["LINE"]["enable"]
			)
			LOGGER = Logging(loggingLevel=CONFIG["loggingLevel"])
			REPORTER = Reporter(CONFIG["reporter"]["interval"], priority=2)
			SCHEDULER.enter(1, REPORTER.priority, REPORTER.report)

			# ########
			# Run each pair simultaenously.
			# ########
			pairsCount = 0
			for pair in CONFIG["pairs"]:
				if not pair["enable"]:
					continue
				sloth = BinanceSloth(pair)
				SCHEDULER.enter(1, pair["priority"], sloth.run)
				pairsCount += 1

			if pairsCount > 0:
				time.sleep(random.randint(2, 3))
				try:
					print("getting started...")
					SCHEDULER.run()
				except NameError as e:
					print(e)
			else:
				print("no pair to run.")
		else:
			print("could not load the configuration file!")

		print("retry to load {} again in 30 seconds...".format(args["config"]))
		time.sleep(30)