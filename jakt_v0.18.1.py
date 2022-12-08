from marshal import dumps
#from binhex import Error
from sys import exit
from os import system, path, chdir
from collections import defaultdict
import sched, time
#from cv2 import CALIB_NINTRINSIC
from numpy.core.fromnumeric import resize
import  requests 
import numpy as np
from requests import models 
import talib as ta
#from binance.client import Client
from binance.um_futures import UMFutures as Futures
from binance.error import ClientError
import json
import logging
import random
import urllib3
import subprocess
import platform
import pathlib
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from colorama import Fore, Style, init as colorama_init


class Bot:
	def __init__(self, name, color, lineToken, lineNotify=False):
		self.name = name
		self.lineToken = lineToken
		self.lineNotify = lineNotify
		#self.color = random.choice(["LIGHTMAGENTA_EX", "LIGHTYELLOW_EX", "LIGHTCYAN_EX", "LIGHTGREEN_EX", "LIGHTRED_EX"])
		self.color = color

	def pprint(self, msg):
		print(json.dumps(msg, indent=4, sort_keys=False))

	def print(self, msg, type="info"):
		if True:
			#print(msg)
			if type == "info":
				if self.color == "LIGHTMAGENTA_EX":
					LOGGER.info(Fore.LIGHTMAGENTA_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg))
				elif self.color == "LIGHTYELLOW_EX":
					LOGGER.info(Fore.LIGHTYELLOW_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg))
				elif self.color == "LIGHTCYAN_EX":
					LOGGER.info(Fore.LIGHTCYAN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg))
				elif self.color == "LIGHTGREEN_EX":
					LOGGER.info(Fore.LIGHTGREEN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg))
				elif self.color == "LIGHTRED_EX":
					LOGGER.info(Fore.LIGHTRED_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg))

			elif type == "debug":
				LOGGER.debug("{} {}".format(self.name, msg))
			elif type == "warning":
				LOGGER.warning("{} {}".format(self.name, msg))
		if self.lineNotify:
			try:
				self.LINE_notify(msg)
				#print("Line notices!")
			except:
				print("{} LINE notification error".format(self.name))

	def LINE_notify(self, msg):
		url = 'https://notify-api.line.me/api/notify'
		headers = {'Authorization':'Bearer '+self.lineToken}
		return requests.post(url, headers=headers , data = {'message':msg}, files=None)


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
			self.print(
				"internet connection "+Fore.RED+"failed"+Style.RESET_ALL
				+", retry in "+Fore.GREEN+"{}".format(seconds)+Style.RESET_ALL+" second(s)"
			)
			time.sleep(seconds)
			if seconds < retry_sec_max:
				seconds += increment_sec
		self.print(Fore.GREEN + "OK" + Style.RESET_ALL)

	def sleep(self, min=1, max=-1):
		if max == -1:
			time.sleep(min)
		else:
			time.sleep(random.randint(min, max))

	def connectBinanceAPI(self, retry_sec_min=5, increment_sec=10, retry_sec_max=60*3):
		seconds = retry_sec_min
		connectionPassed = 0
		connectionTotal = 1

		while connectionPassed < connectionTotal:
			try:
				response = FUTURES.account()
				connectionPassed += 1
			except ClientError as e:
				self.print(e.error_message)
				self.print(
					"Binance API connection "+Fore.RED+"failed"+Style.RESET_ALL
					+", attempt to fix the problem..."
				)
				self.print("time syncing function is under being developed!")
				####
				# fixing goes here...
				# under construction!
				####
				self.print(
					"attempted, connect again in "+Fore.GREEN+"{}".format(seconds)+Style.RESET_ALL+" second(s)"
				)
			time.sleep(seconds)
			if seconds < retry_sec_max:
				seconds += increment_sec

		if connectionPassed >= connectionTotal:
			self.print(Fore.GREEN + "connected" + Style.RESET_ALL)		

class JAKT(Bot):
	def __init__(
		self, 
		symbol=None, 
		strategy=None, 
		color=None,
		lineToken=None,
		lineNotify=False, 
		priority=1, 
		interval_sec=5, 
		action=False
	):
		Bot.__init__(self, symbol[0]+symbol[1], color, lineToken, lineNotify)
		self.symbol = symbol[0]+symbol[1]
		self.cryptoName = symbol[0]
		self.assetName = symbol[1]
		self.strategy = strategy
		self.interval_sec = interval_sec
		self.priority = priority
		self.availableBalance = None
		self.positionAmt = 0
		self.positionState = None # longed, shorted, or closed
		#self.orderAmt = 0
		self.orderAmtMin = 0.001 # for BTC only, not sure for the others
		self.leverage = 0
		#self.flag_ema_vector = None
		self.action = action
		self.initialize()
	
	# initialization
	def initialize(self):

		self.print("initialization started...")
		if True:
			self.print("checking internet connection...")
			self.waitForInternet()
			self.sleep(1, 2)

		if True:
			self.print("connecting to Binance API...")
			self.connectBinanceAPI()
			self.sleep(1, 2)

		# for debugging only
		if False:
			self.pprint(self.fetchLeverageBracket())
			exit()

		if True:
			self.print("syncing position...")
			self.syncPosition()
			self.print(
				"current position: "
				+Fore.GREEN
				+"{} ".format(self.positionState)
				+Style.RESET_ALL
				+", amt:"
				+Fore.GREEN
				+" {} {}".format(self.positionAmt, self.cryptoName)
				+Style.RESET_ALL
			)
			self.sleep(1, 2)
		
		# close all opened position if needed; default: False
		if False:
			self.print("closing all positions if exist...")
			self.print(self.closeAllPositions())
			self.sleep(2, 3)

		if True:
			self.syncAvailableBalance()
			self.print("available balance: "+Fore.GREEN+"{} {}".format(self.availableBalance, self.assetName)+Style.RESET_ALL)
			self.sleep(1, 2)
			
			#self.print("syncing leverage...")
			self.syncLeverage()
			#self.pprint(self.fetchLeverageBracket())
			self.print("synced leverage: "+Fore.GREEN+"{}x".format(self.leverage)+Style.RESET_ALL)
			self.sleep(1, 2)
		
			if False:
				#self.print("updating order amount...")
				self.updateOrderAmt()
				self.print("max amount per order: "+Fore.GREEN+"{} {}".format(self.orderAmt, self.cryptoName)+Style.RESET_ALL)
				self.sleep(1, 2)

			self.print(
				"set by "+
				Fore.GREEN+
				"{}".format(self.strategy)+
				Style.RESET_ALL+
				" strategy, and scheduled with "+
				Fore.GREEN+"{} seconds".format(self.interval_sec)+
				Style.RESET_ALL+
				" interval"
			)
			self.sleep(1, 2)

		self.print("initialization complete.")
		self.print("--------------------------------")
		self.sleep(1, 2)

	def API_connect(self):
		self.print(FUTURES.ping())


	# taking a short a position with desire quantity, or self.orderAmt
	def short(self, quantity=-1):
		if quantity < 0:
			quantity = self.positionAmt
		response = "self.action is set to False"
		if self.action:
			params = {
				'symbol': self.symbol,
				'side': 'SELL',
				'type': 'MARKET',
				'quantity': abs(quantity)
			}
			try:
				response = FUTURES.new_order(**params)
				#self.positionState = 'shorted'
				time.sleep(1)
				self.syncPosition()
				self.print(Fore.GREEN+"Shorted: {} {}".format(self.positionAmt, self.cryptoName)+Style.RESET_ALL)
			except ClientError as e:
				self.print("Short position with {} qty failed. {}".format(quantity, e.error_message))
				response = e.error_message
		return response


	# taking a long position with desire quantity, or self.orderAmt
	def long(self, quantity=-1):
		if quantity < 0:
			quantity = self.positionAmt
		response = "self.action is set to False"
		if self.action:
			params = {
				'symbol': self.symbol,
				'side': 'BUY',
				'type': 'MARKET',
				'quantity': abs(quantity)
			}
			try:
				response = FUTURES.new_order(**params)
				#self.positionState = 'longed'
				time.sleep(1)
				self.syncPosition()
				self.print(Fore.GREEN+"Longed: {} {}".format(self.positionAmt, self.cryptoName)+Style.RESET_ALL)
			except ClientError as e:
				self.print("Long position with {} {} failed. {}".format(quantity, self.cryptoName, e.error_message))
				response = e.error_message
		return response
	

	def close(self):
		response = "self.action is set to False"
		if self.action:
			self.syncPosition()
			if self.positionAmt > 0:
				self.short(self.positionAmt)
				self.positionState = "closed"
				response = "longed positions are closed"
			elif self.positionAmt < 0:
				self.long(self.positionAmt)
				self.positionState = "closed"
				response = "shorted positions are closed"
			else:
				response = "no opened position to be closed"
			time.sleep(1)
			self.syncPosition()
		return response

	def closeAllPositions(self):
		response = "self.action is set to False"
		if self.action:
			self.syncPosition()
			if self.positionAmt > 0:
				self.short(self.positionAmt)
				response = "longed positions are closed"
			elif self.positionAmt < 0:
				self.long(self.positionAmt)
				response = "shorted positions are closed"
			else:
				response = "no opened position to be closed"
			time.sleep(1)
			self.syncPosition()
		self.positionState = "closed"
		return response


	def syncPosition(self):
		self.positionAmt = float(self.fetchPositionAmt())
		if self.positionAmt > 0:
			self.positionState = "longed"
		elif self.positionAmt < 0:
			self.positionState = "shorted"
		elif self.positionAmt == 0:
			self.positionState = "closed"
		else:
			self.print("syncPosition error")


	# fetch klines
	def fetch(self, tf, samples=50):
		return_data = []
		for each in requests.get(
			"https://fapi.binance.com/fapi/v1/klines?symbol={}&interval={}&limit={}".format(
			#"https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(
				self.symbol, tf, samples
			)
		).json():
			return_data.append(float(each[4])) # we need only closed price
		return np.array(return_data)


	def fetchPositionAmt(self):
		return float(self.fetchOpenPosition()["positionAmt"])


	def fetchAccount(self):
		try:
			response = FUTURES.account(ecvWindow=2000)
		except ClientError as e:
			response = e
		return response


	def fetchOpenOrders(self):
		try:
			response = FUTURES.get_open_orders(symbol=self.symbol, recvWindow=2000)
		except ClientError as e:
			response = e
		return response


	def fetchBalance(self):
		balance = None
		try:
			response = FUTURES.balance(recvWindow=2000)
			for asset in response:
				if asset["asset"] == self.assetName:
					return asset["availableBalance"]
		except ClientError as e:
			return e


	def fetchLeverageBracket(self):
		leverages = FUTURES.leverage_brackets()
		for leverage in leverages:
			if leverage["symbol"] == self.symbol:
				for bracket in leverage["brackets"]:
					#if bracket["initialLeverage"] == self.leverage:
					return bracket


	def fetchLeverage(self):
		for position in self.fetchAccount()["positions"]:
			if position["symbol"] == self.symbol:
				return position["leverage"]


	# not tested yet, but might works
	def fetchUnPNL(self):
		account = self.fetchAccount()
		return account["totalCrossUnPnl"]


	def fetchOpenPosition(self):
		try:
			risks = FUTURES.get_position_risk(recvWindow=6000)
			for risk in risks:
				if risk["symbol"] == self.symbol:
					return risk
		except ClientError as e:
			return e


	def syncLeverage(self):
		self.leverage = int(self.fetchLeverage())
		return self.leverage


	def syncAvailableBalance(self):
		self.availableBalance = float(self.fetchBalance())


	# going to be deleted, not neccessary!
	def updateOrderAmt(self):
		leverage = self.fetchLeverageBracket()
		self.orderAmt = leverage["maintMarginRatio"]


	def calOpenLoss(self):
		# = Number of contract * abs val {min[0, direction of order * (markprice - orderprice)]}
		#return self.orderAmt*abs(min([0, 1*markprice-orderprice]))
		pass
	

	def calInitMargin(self, price):
		return price*self.orderAmtMin/self.leverage


	def calMaxQTY(self, price, percent=100):
		# under implementation! This could return the float, not int!?
		return int((percent/100*self.availableBalance)/self.calInitMargin(price))


	def calQTY(self, price, percent=100):
		# under implementation! This could return the float, not int!?
		return self.calMaxQTY(price, percent) * self.orderAmtMin


	def getEMA(self, data, ema=5):
		return round(ta.EMA(data, ema)[-2], 2)


	def getEMA_comp_cross(self, data, ema_small=5, ema_large=10):
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


	def getEMA_vector(self, data, ema=5, depth=3, step=1):
		#
		# u and d stand for up and down respectively
		#
		emas = ta.EMA(data, ema)
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


	def getDeltaEMA(self, data, ema_small, ema_large):
		return round(ta.EMA(data, ema_small)[-2]-ta.EMA(data, ema_large)[-2], 2)


	def getMACD(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
		_, _, macdhist = ta.MACD(data, fastperiod, slowperiod, signalperiod)
		return round(macdhist[-2], 2)
	

	def getMACD_zcross(self, data, fastperiod=12, slowperiod=26, signalperiod=9):
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


	def getMACD_vector(self, data, fastperiod=12, slowperiod=26, signalperiod=9, step=1):
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


	def getRSI(self, data):
		return round(ta.RSI(data, 6)[-2], 2)
		

	def getSAR(self, data, timeperiod=30):
		return ta.SAR(data.high, data.low, acceleration=0, maximum=0)


	def run(self):
		predict = 'ready'
		action = 'watch'
		indy = defaultdict(dict)

		if self.strategy == "basic":
			tf="1m"
			closing_data = self.fetch(tf, 50)
			indy["pair"] = self.symbol
			indy[tf]["ema_dif"] = self.getDeltaEMA(closing_data, 5, 10)
			indy[tf]["macd"] = self.getMACD(closing_data)
			indy[tf]["rsi"] = self.getRSI(closing_data)

			if indy[tf]["ema_dif"] >= 0:
				if indy[tf]["macd"] >= 0: # this TF says should take LONG
					predict = 'long'
			else:
				if indy[tf]["macd"] < 0:
					predict = 'short'
		
		if self.strategy == "simple33":
			tf="3m"
			closing_data = self.fetch(tf, 200)
			indy["pair"] = self.symbol
			indy[tf]["ema_19_vector"] = self.getEMA_vector(closing_data, ema=19, depth=3)
			indy[tf]["ema_19"] = self.getEMA(data=closing_data, ema=19)
			indy[tf]["ema_33"] = self.getEMA(data=closing_data, ema=33)

			if self.positionState == "closed":
				# this condition is to consider when should taking long or short
				if (indy[tf]["ema_19_vector"] == "uuu") and (indy[tf]["ema_19"] <= indy[tf]["ema_33"]):
					# taking long position
					self.long()
					action="open longed order"
				elif (indy[tf]["ema_19_vector"] == "ddd") and (indy[tf]["ema_19"] > indy[tf]["ema_33"]):
					# taking short position
					self.short()
					action="open shorted order"
				else:
					action="waiting for the top and the dip"

			elif self.positionState == "longed":
				if indy[tf]["ema_19_vector"] == "ddd":
					# taking close position
					self.close()
					action="close a longed position"
				else:
					action="let longed profit run"

			elif self.positionState == "shorted":
				if indy[tf]["ema_19_vector"] == "uuu":
					# taking  close position
					self.close()
					action="close a shorted position"
				else:
					action="let shorted profit run"
			else:
				self.print("self.positionState invalid: {}".format(self.positionState))

			self.print("action: {}, position state: {}".format(action, self.positionState))


		elif self.strategy == "onlymacd30m":
			tf="30m"
			closing_data = self.fetch(tf, 50)
			indy["pair"] = self.symbol
			indy[tf]["ema_dif"] = self.getDeltaEMA(closing_data, ema_small=5, ema_large=10)
			indy[tf]["macd"] = self.getMACD(closing_data, fastperiod=12, slowperiod=26, signalperiod=9)
			indy[tf]["rsi"] = self.getRSI(closing_data)

			if indy[tf]["ema_dif"] >= 0:
				if indy[tf]["macd"] >= 0: # this TF says should take LONG
					predict = 'long'
			else:
				if indy[tf]["macd"] < 0:
					predict = 'short'
			
		elif self.strategy == "testindy":
			tf="1m"
			closing_data = self.fetch(tf, 50)
			indy["pair"] = self.symbol
			indy[tf]["closed"] = closing_data[-2]
			indy[tf]["ema_5"] = self.getEMA(closing_data, 5)
			indy[tf]["ema_10"] = self.getEMA(closing_data, 10)
			indy[tf]["macd"] = self.getMACD(closing_data, fastperiod=12, slowperiod=26, signalperiod=9)
			indy[tf]["rsi"] = self.getRSI(closing_data)
			self.pprint(indy)
		
		elif self.strategy == "MaoNoi1h":
			tf="1h"
			closing_data = self.fetch(tf, 200)
			indy["pair"] = self.symbol
			indy[tf]["ema_dif"] = self.getDeltaEMA(closing_data, 5, 10)
			indy[tf]["macd"] = self.getMACD(closing_data, fastperiod=12, slowperiod=26, signalperiod=9)
			#indy[tf]["rsi"] = self.getRSI(closing_data)

			if indy[tf]["macd"] > 0:
				pass
			else:
				pass
		elif self.strategy == "MaoJayNoi15m":
			pass
		elif self.strategy == "MaoKayNoi":
			pass
		elif self.strategy == "MaoToneNoi":
			pass
		elif self.strategy == "test":
			tf="3m"
			closing_data = self.fetch(tf, 330)
			#response = FUTURES.change_leverage(symbol=self.symbol, leverage=1, recvWindow=6000)
			#self.print("Available balance: {} {}".format(self.fetchBalance(), self.assetName))
			#self.pprint(self.getLeverage())
			#print(self.getTemp_CPU())
			#self.short()
			#time.sleep(1)
			#self.pprint(FUTURES.get_all_orders(self.symbol)[-1])
			#self.pprint(self.close_test())
			#self.pprint(FUTURES.get_all_orders(self.symbol, recvWindow=2000))
			#print(self.close(self.getRecentOrders()["orderId"]))
			#display("Orders: {}".format(self.fetchOpenOrders()))
			#self.print(closing_data[0])
			#self.print(self.calQTY(closing_data[0], 100))
			#self.pprint(self.fetchLeverageBracket())
			if True:
				self.updateOrderAmt()
				self.print("max amount per order: "+Fore.GREEN+"{} {}".format(self.orderAmt, self.cryptoName)+Style.RESET_ALL)
			#self.print("EMA_vector: {}".format(self.getEMA_vector(closing_data, ema=5, depth=2)))
			#self.print("MACD_vector: {}".format(self.getMACD_vector(closing_data, fastperiod=12, slowperiod=26, signalperiod=9)))

			self.print(self.getMACD_vector(closing_data, fastperiod=99, slowperiod=150, signalperiod=99, step=1))
			self.print("end test strategy")
			#time.sleep(30)
			
		elif self.strategy == "testOpenOrder":
			tf="15m"
			closing_data = self.fetch(tf, 1)

			self.print("testing long...")
			self.long(self.calQTY(closing_data[0], 100))
			time.sleep(5)
			self.print("testing close...")
			self.close()
			time.sleep(5)
			self.print("testing short...")
			self.short(self.calQTY(closing_data[0], 100))
			time.sleep(5)
			self.print("testing close...")
			self.close()
			
			self.print("end test strategy")
			#time.sleep(30)

		elif self.strategy == "MACD99-150-99":
			tf="3m"
			closing_data = self.fetch(tf, 300)
			
			self.print("{} operated".format(self.strategy))
			#time.sleep(30)

		elif self.strategy == "MACDez":
			action="doing nothing"
			tf="3m"

			closing_data = self.fetch(tf, 200)
			indy["QTY_percent"] = 50
			indy["QTY"] = self.calQTY(closing_data[0], percent=indy["QTY_percent"])
			indy[tf]["MACD_zcross"] = self.getMACD_zcross(closing_data, fastperiod=66, slowperiod=100, signalperiod=33)
			indy[tf]["MACD_vector"] = self.getMACD_vector(closing_data, fastperiod=66, slowperiod=100, signalperiod=33, step=1)
			self.pprint(indy)
			
			if self.positionState == "closed":
				# this condition is to consider when should taking long or short
				if (indy[tf]["MACD_zcross"] == "nnp"):
					# taking long position
					self.long(indy["QTY"])
					action="open longed order"
				elif (indy[tf]["MACD_zcross"] == "ppn"):
					# taking short position
					self.short(indy["QTY"])
					action="open shorted order"
				else:
					action="waiting for the top and the dip"

			elif self.positionState == "longed":
				if indy[tf]["MACD_vector"] == "udd" or indy[tf]["MACD_vector"] == "ddd":
					# taking close position
					self.close(indy["QTY"])
					action="close a longed position"
				else:
					action="let longed profit run"

			elif self.positionState == "shorted":
				if indy[tf]["MACD_vector"] == "duu" or indy[tf]["MACD_vector"] == "uuu":
					# taking  close position
					self.close(indy["QTY"])
					action="close a shorted position"
				else:
					action="let shorted profit run"
			else:
				self.print("self.positionState invalid: {}".format(self.positionState))

			self.print("{} just {}, current position state: {}".format(self.strategy, action, self.positionState))
			#sleep(10)
			
		else:
			self.print("no strategy is set!")

		#self.print("suggest: {}, act: {}, has {}".format(predict, action, self.positionState))
		SCHEDULER.enter(self.interval_sec, self.priority, self.run)


################################################
# MAIN SECTION
################################################
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S'))
LOGGER.addHandler(stream_handler)
colorama_init(autoreset=True)
configFile = "config.json"

while True:
	if path.exists(configFile):
		try:
			f = open(configFile, encoding = 'utf-8')
			config = json.load(f)
			f.close()
			print("{} loaded".format(configFile))
		except KeyError as e:
			print(e)
			exit()

		if config["customWD"]["enable"]:
			if platform.system() == "Linux":
				chdir(config["customWD"]["linux"])
			elif platform.system() == "Windows":
				chdir(config["customWD"]["windows"])
			else:
				print("Operating system unknown. Invalid WD might cause an error.")

		SCHEDULER = sched.scheduler(time.time, time.sleep)
		FUTURES = Futures(
			key=config["BinanceAPI"]["key"],
			secret=config["BinanceAPI"]["secret"],
			base_url=config["BinanceAPI"]["base_url"]
		)

		pairsCount = 0
		for pair in config["pairs"]:
			if not pair["enable"]:
				continue
			A = JAKT(
				symbol=[pair["crypto"], pair["asset"]],
				strategy=pair["strategy"],
				interval_sec=pair["interval_seconds"],
				color=pair["color"],
				lineToken=config["LINE"]["token"],
				lineNotify=config["LINE"]["enable"],
				action=config["action"]
			)
			SCHEDULER.enter(A.interval_sec, A.priority, A.run)
			pairsCount += 1

		if pairsCount > 0:
			time.sleep(random.randint(2, 3))
			try:
				LOGGER.info("getting started...")
				SCHEDULER.run()
			except NameError as e:
				LOGGER.info(e)
		else:
			LOGGER.info("no pair to run.")
	else:
		LOGGER.info("could not load the configuration file!")
		
	LOGGER.info("retry in 30 seconds...")
	time.sleep(30)