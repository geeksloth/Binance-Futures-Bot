from asyncio.log import logger
from sys import exit
from os import system, path, chdir
from collections import defaultdict
import sched, time
from numpy.core.fromnumeric import resize
import  requests
import numpy as np
import talib as ta
#from binance.futures import Futures
from binance.cm_futures import CMFutures as Futures
from binance.error import ClientError
import json
import logging
import random
import urllib3
import subprocess
import platform
from colorama import Fore, Style, init as colorama_init
import argparse
from tabulate import tabulate


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
colorama_init(autoreset=True)


class Bot:
	def __init__(self, name, color, loggingLevel, LINE):
		self.name = name
		self.color = color
		self.LINE = self.LINE(LINE["api"], LINE["token"], LINE["enable"])
		self.log = self.Log(name, color, loggingLevel, self.LINE, LINE["enableErrorNotify"])

	class LINE():
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

	class Log:
		def __init__(self, name, color, loggingLevel, LINE, enableErrorNotify):
			self.logger = None
			self.name = name
			self.color = color
			self.LINE=LINE
			self.loggingLevel = loggingLevel
			self.enableErrorNotify = enableErrorNotify

			logger = logging.getLogger()
			if self.loggingLevel.upper() == "DEBUG":
				logger.setLevel(logging.DEBUG)
			elif self.loggingLevel.upper() == "INFO":
				logger.setLevel(logging.INFO)
			elif self.loggingLevel.upper() == "WARNING":
				logger.setLevel(logging.WARNING)
			elif self.loggingLevel.upper() == "ERROR":
				logger.setLevel(logging.ERROR)
			elif self.loggingLevel.upper() == "CRITICAL":
				logger.setLevel(logging.CRITICAL)
			else:
				print("loggingLevel invalid [{}]".format(self.loggingLevel))
				logger.setLevel(logging.DEBUG)
			sh = logging.StreamHandler()
			sh.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S'))
			logger.addHandler(sh)
			self.logger = logger

		def addPrefix(self, msg):
			if self.color == "LIGHTMAGENTA_EX":
				styledMsg = Fore.LIGHTMAGENTA_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
			elif self.color == "LIGHTYELLOW_EX":
				styledMsg = Fore.LIGHTYELLOW_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
			elif self.color == "LIGHTCYAN_EX":
				styledMsg = Fore.LIGHTCYAN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
			elif self.color == "LIGHTGREEN_EX":
				styledMsg = Fore.LIGHTGREEN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
			elif self.color == "LIGHTRED_EX":
				styledMsg = Fore.LIGHTRED_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
			return styledMsg

		def debug(self, msg):
			self.logger.debug(self.addPrefix(msg))

		def info(self, msg):
			self.logger.info(self.addPrefix(msg))

		def warning(self, msg):
			self.logger.warning(self.addPrefix(msg))

		def error(self, msg):
			self.logger.error(self.addPrefix(msg))
			if self.enableErrorNotify:
				self.LINE.notify("{} error: {}".format(self.name, msg))

		def critical(self, msg):
			self.logger.critical(self.addPrefix(msg))
			if self.enableErrorNotify:
				self.LINE.notify("critical: {}".format(self.name, msg))

	def pprint(self, msg):
		print(json.dumps(msg, indent=4, sort_keys=False))

	def pretty(self, msg):
		return(json.dumps(msg, indent=4, sort_keys=False))

	def print(self, msg):
		if self.color == "LIGHTMAGENTA_EX":
			styled_msg = Fore.LIGHTMAGENTA_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTYELLOW_EX":
			styled_msg = Fore.LIGHTYELLOW_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTCYAN_EX":
			styled_msg = Fore.LIGHTCYAN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTGREEN_EX":
			styled_msg = Fore.LIGHTGREEN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTRED_EX":
			styled_msg = Fore.LIGHTRED_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		print(styled_msg)

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

	def pingAPI(self):
		response = None
		return futures.time()

	def waitForInternet(self, retry_sec_min=1, increment_sec=10, retry_sec_max=60*3):
		seconds = retry_sec_min
		while not self.ping():
			self.log.warning(
				"internet connection "+Fore.RED+"failed"+Style.RESET_ALL
				+", retry in "+Fore.GREEN+"{}".format(seconds)+Style.RESET_ALL+" second(s)"
			)
			time.sleep(seconds)
			if seconds < retry_sec_max:
				seconds += increment_sec
		self.log.info(Fore.GREEN + "OK" + Style.RESET_ALL)

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
				response = futures.account()
				connectionPassed += 1
			except ClientError as e:
				self.log.error(e.error_message)
				self.log.info(
					"Binance API connection "+Fore.RED+"failed"+Style.RESET_ALL
					+", attempt to fix the problem..."
				)
				self.log.warning("time syncing function is under being developed!")
				####
				# fixing goes here...
				# under construction!
				####
				self.log.warning(
					"attempted, connect again in "+Fore.GREEN+"{}".format(seconds)+Style.RESET_ALL+" second(s)"
				)
			time.sleep(seconds)
			if seconds < retry_sec_max:
				seconds += increment_sec

		if connectionPassed >= connectionTotal:
			self.log.info(Fore.GREEN + "connected" + Style.RESET_ALL)

	def float_trim(self, input, decimal):
		x_str = str(input)
		x = x_str.split(".")
		result = str(x[0])+"."+str(x[1][:decimal])
		return(float(result))

class JAKT(Bot):
	def __init__(self, pair, color, loggingLevel, LINE):
		self.symbol = pair["crypto"]+pair["asset"]
		self.cryptoName = pair["crypto"]
		self.assetName = pair["asset"]
		self.strategy = pair["strategy"]
		self.used_asset_percent = int(pair["used_asset_percent"])
		self.interval_when_closed = int(pair["interval_when_closed"])
		self.interval_when_opened = int(pair["interval_when_opened"])
		self.priority = int(pair["priority"])
		self.availableBalance = None
		self.positionAmt = 0
		self.positionState = None # longed, shorted, or closed
		self.orderAmtMin = float(pair["minimum_order_amt"]) # for BTC only, not sure for the others
		self.leverage = 0
		self.cUnPnl = None
		Bot.__init__(self, self.symbol, color, loggingLevel, LINE)
		self.initialize()

	def connect_API(self):
		self.log.info(futures.ping())

	def cal_initMargin(self, price):
		return float(float(price)*self.orderAmtMin/self.leverage)

	def cal_openLoss(self):
		# = Number of contract * abs val {min[0, direction of order * (markprice - orderprice)]}
		#return self.orderAmt*abs(min([0, 1*markprice-orderprice]))
		pass

	def cal_QTY(self, price):
		# under implementation! This could return the float, not int!?
		qty = self.cal_QTY_max(float(price), self.used_asset_percent) * self.orderAmtMin

		#print(qty)
		return self.float_trim(qty, 3)

	def cal_QTY_max(self, price, percent):
		# under implementation! This could return the float, not int!?
		return float((percent/100*self.availableBalance)/self.cal_initMargin(float(price)))

	def close(self):
		response = None
		self.sync_position()
		if self.positionAmt > 0:
			self.short()
			self.positionState = "closed"
			response = "longed positions are closed"
		elif self.positionAmt < 0:
			self.long()
			self.positionState = "closed"
			response = "shorted positions are closed"
		else:
			response = "no opened position to be closed"
		time.sleep(1)
		self.sync_position()
		return response

	def close_all(self):
		response = None
		self.sync_position()
		if self.positionAmt > 0:
			self.short(self.positionAmt)
			response = "longed positions are closed"
		elif self.positionAmt < 0:
			self.long(self.positionAmt)
			response = "shorted positions are closed"
		else:
			response = "no opened position to be closed"
		time.sleep(1)
		self.sync_position()
		self.positionState = "closed"
		return response

	def fetch_closes(self, tf, samples=50):
		return_data = []
		for each in requests.get(
			"https://fapi.binance.com/fapi/v1/klines?symbol={}&interval={}&limit={}".format(
			#"https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(
				self.symbol, tf, samples
			)
		).json():
			return_data.append(float(each[4])) # we need only closed price
		return np.array(return_data)

	def fetch_account(self):
		try:
			response = futures.account(ecvWindow=2000)
		except ClientError as e:
			response = e
		return response

	def fetch_balance(self):
		try:
			response = futures.balance(recvWindow=2000)
			for asset in response:
				if asset["asset"] == self.assetName:
					return asset["availableBalance"]
		except ClientError as e:
			return e

	def fetch_leverage(self):
		for position in self.fetch_account()["positions"]:
			if position["symbol"] == self.symbol:
				return position["leverage"]

	def fetch_leverageBracket(self):
		leverages = futures.leverage_brackets()
		for leverage in leverages:
			if leverage["symbol"] == self.symbol:
				for bracket in leverage["brackets"]:
					#if bracket["initialLeverage"] == self.leverage:
					return bracket

	def fetch_openedOrders(self):
		try:
			response = futures.get_open_orders(symbol=self.symbol, recvWindow=2000)
		except ClientError as e:
			response = e
		return response

	def fetch_position(self):
		try:
			risks = futures.get_positions(recvWindow=6000)
			for risk in risks:
				if risk["symbol"] == self.symbol:
					return risk
		except ClientError as e:
			return e

	def fetch_position_amt(self):
		val = self.fetch_position()["positionAmt"]
		if val is None:
			self.log.warning("NoneType returned from fetch_position()")
			return float(0.0)
		else:
			return float(val)

	# not tested yet, but should work maybe
	def fetch_UnPNL_cross(self):
		account = self.fetch_account()
		return account["totalCrossUnPnl"]

	def getReady(self):
		try:
			self.sync_position()
			self.sync_stats()
			return True
		except NameError as e:
			return False

	def initialize(self):
		self.log.info("initialization started...")
		if False:
			#self.LINE.notify("Just notify")
			self.log.debug("test debug")
			self.log.info("test info")
			self.log.warning("test warning")
			self.log.error("test ERROR")
			#self.log.critical("test CRITICAL!")
			exit()

		if False:
			#self.log.debug(self.used_asset_percent)
			self.log.info(self.fetch_UnPNL_cross())
			#self.LINE("Hi, I'm {}->{}.".format(path.basename(__file__), self.symbol))
			self.log.info("end test.")
			#exit()

		if True:
			self.log.info("checking internet connection...")
			self.waitForInternet()
			self.sleep(1, 2)
		if True:
			self.log.info("connecting to Binance API...")
			self.connectBinanceAPI()
			self.sleep(1, 2)
		if True:
			#self.log.info("syncing position...")
			self.sync_position()
			self.log.info(
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
			self.log.warning("closing all positions if exist...")
			self.log.info(self.close_all())
			self.sleep(2, 3)
		if True:
			self.sync_availableBlance()
			self.log.info("available balance: "+Fore.GREEN+"{} {}".format(round(self.availableBalance, 4), self.assetName)+Style.RESET_ALL)
			self.sleep(1, 2)
			#self.log.info("syncing leverage...")
			self.sync_leverage()
			#self.pprint(self.fetch_leverageBracket())
			self.log.info("synced leverage: "+Fore.GREEN+"{}x".format(self.leverage)+Style.RESET_ALL)
			self.sleep(1, 2)
			self.log.info("used asset: "+Fore.GREEN+"{}%".format(self.used_asset_percent)+Style.RESET_ALL)
			self.sleep(1, 2)
			self.log.info(
				"set by "+
				Fore.GREEN+
				"{}".format(self.strategy)+
				Style.RESET_ALL+
				" strategy"
			)
			self.log.info(
				"interval when closed: "+
				Fore.GREEN+"{} seconds".format(self.interval_when_closed)+
				Style.RESET_ALL
			)
			self.log.info(
				"interval when opened: "+
				Fore.GREEN+"{} seconds".format(self.interval_when_opened)+
				Style.RESET_ALL
			)
			self.sleep(1, 2)

		self.log.info("initialization completed.")
		#self.LINE("{} {} initialized".format(path.basename(__file__), self.symbol))
		self.log.info("-"*32)
		self.sleep(1, 2)

	def long(self, quantity=None):
		if quantity is None:
			quantity = self.positionAmt
		response = "self.action is set to False"
		params = {
			'symbol': self.symbol,
			'side': 'BUY',
			'type': 'MARKET',
			'quantity': abs(quantity)
		}
		try:
			response = futures.new_order(**params)
			time.sleep(1)
			self.sync_position()
			self.log.info(Fore.GREEN+"Longed: {} {}".format(self.positionAmt, self.cryptoName)+Style.RESET_ALL)
		except ClientError as e:
			self.log.info("Long with {} {} failed. {}".format(quantity, self.cryptoName, e.error_message))
			response = e.error_message
		return response

	def map(self, x, in_min, in_max, out_min, out_max):
		'''
			long map(long x, long in_min, long in_max, long out_min, long out_max) {
			return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
			}
		'''
		return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

	def printCurrentStats(self):
		#self.log.info(self.positionState)
		headers = [
			"strategy",
			"avl[{}]".format(self.assetName),
			"posStt",
			"posAmt[{}]".format(self.cryptoName),
			"lvrg",
			"cUnPnl",
			"asset%"
		]
		row = [[
			self.strategy,
			self.availableBalance,
			self.positionState,
			self.positionAmt,
			self.leverage,
			self.cUnPnl,
			self.used_asset_percent
		]]
		self.log.info("\n"+tabulate(row, headers, tablefmt="github"))

	def short(self, quantity=None):
		if quantity is None:
			quantity = self.positionAmt
		response = "self.action is set to False"
		params = {
			'symbol': self.symbol,
			'side': 'SELL',
			'type': 'MARKET',
			'quantity': abs(quantity)
		}
		try:
			response = futures.new_order(**params)
			#self.positionState = 'shorted'
			time.sleep(1)
			self.sync_position()
			self.log.warning(Fore.GREEN+"Shorted: {} {}".format(self.positionAmt, self.cryptoName)+Style.RESET_ALL)
		except ClientError as e:
			self.log.error("Short position with {} qty failed. {}".format(quantity, e.error_message))
			response = e.error_message
		return response

	def sync_availableBlance(self):
		self.availableBalance = float(self.fetch_balance())

	def sync_leverage(self):
		self.leverage = int(self.fetch_leverage())
		return self.leverage

	def sync_position(self):
		self.positionAmt = self.fetch_position_amt()
		if self.positionAmt > 0:
			self.positionState = "longed"
		elif self.positionAmt < 0:
			self.positionState = "shorted"
		elif self.positionAmt == 0:
			self.positionState = "closed"
		else:
			self.log.error("sync_position error")

	def sync_stats(self):
		try:
			account = self.fetch_account()
			for position in account["positions"]:
				if position["symbol"] == self.symbol:
					self.leverage = int(position["leverage"])
			self.cUnPnl = float(account["totalCrossUnPnl"])
		except NameError as e:
			self.log.error("sync_stats: "+e)

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

	def run(self):
		if(self.getReady()):
			if self.strategy == "MACDRider":
				indy = defaultdict(dict)
				data = defaultdict(dict)
				tf = "15m"
				data = self.fetch_closes(tf)
				if self.positionState == "closed":
					pass
				elif self.positionState == "longed":
					pass
				elif self.positionState == "shorted":
					pass
				else:
					self.log.info("self.positionState: {}".format(self.positionState))
				#self.pprint(indy)
			if self.strategy == "MA99surfer":
				indy = defaultdict(dict)
				data = defaultdict(dict)
				tf = "1h"
				data = self.fetch_closes(tf)

				if self.positionState == "closed":
					pass
				elif self.positionState == "longed":
					pass
				elif self.positionState == "shorted":
					pass
				else:
					self.log.info("self.positionState: {}".format(self.positionState))

			elif self.strategy == "K90_v1":
				indy = defaultdict(dict)
				data = defaultdict(dict)
				criterion = defaultdict(dict)
				k = defaultdict(dict)

				criterion["rsi_oversold"] = 40
				criterion["rsi_overbought"] = 60
				criterion["long_if_over"] = 20
				criterion["short_if_below"] = -20
				criterion["close_shorted_if_over"] = -10
				criterion["close_longed_if_below"] = 10

				#tfs = ["15m", "1h", "4h"]
				tfs = ["1h", "4h"]
				tfs_weight = [1, 3]
				k_weights = [
					#[2, 3, 3, 2], #fibo_macd_v, macd_zcross, rsi_v, insideway
					[1, 1, 1, 1],
					[2, 3, 3, 2]]

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
				#self.pprint(indy)

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
				#self.pprint(k)
				#self.pprint(k_results)

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
				self.log.debug(round(K_score, 2))

				self.log.debug(self.ta_consistency(k_results))
				exit()
				'''
				After we've achived the K_score, OUR INCREDIBLE FACTOR, the actual trading is coming below...
				'''
				#self.log.info(K_score)
				if self.positionState == "closed":
					qty = self.cal_QTY(data[tfs[0]][-1])
					if K_score >= criterion["long_if_over"]:
						try:
							self.long(qty)
							self.log.info("K_score: {}, longed with {} {}".format(round(K_score, 2), qty, self.cryptoName))
						except KeyError as e:
							self.log.error(e)
					elif K_score <= criterion["short_if_below"]:
						try:
							self.short(qty)
							self.log.info("K_score: {}, short with {} {}".format(round(K_score, 2), qty, self.cryptoName))
						except KeyError as e:
							self.log.error(e)
					else:
						self.log.info("K_score: {}, sit on hands and keep waiting.".format(round(K_score, 2)))
				elif self.positionState == "longed":
					if K_score < criterion["close_longed_if_below"]:
						try:
							self.close()
							self.log.info("K_score: {}, longed position just closed".format(round(K_score, 2)))
						except KeyError as e:
							self.log.error(e)
					else:
						self.log.info("K_score: {}, let {} profit run".format(round(K_score), self.positionState))
				elif self.positionState == "shorted":
					if K_score > criterion["close_shorted_if_over"]:
						try:
							self.close()
							self.log.info("K_score: {}, shorted position just closed".format(round(K_score, 2)))
						except KeyError as e:
							self.log.error(e)
					else:
						self.log.info("K_score: {}, let {} profit run".format(round(K_score), self.positionState))
				else:
					self.log.warning("self.positionState: {}".format(self.positionState))
				#self.pprint(indy)

			elif self.strategy == "test":
				time.sleep(5)
				'''
				tf="3m"
				data = self.fetch_closes(tf, 100)
				self.pprint(self.ta_rsi_vector(data))
				'''
			elif self.strategy == "testOpenOrder":
				tf="15m"
				data = self.fetch_closes(tf, 1)
				self.log.info("testing long...")
				self.long(self.cal_QTY(data[0], 100))
				time.sleep(5)
				self.log.info("testing close...")
				self.close()
				time.sleep(5)
				self.log.info("testing short...")
				self.short(self.cal_QTY(data[0], 100))
				time.sleep(5)
				self.log.info("testing close...")
				self.close()
				self.log.info("end test strategy")
			elif self.strategy == "MACDez":
				pass
			else:
				self.log.warning("no strategy is set!")

		self.printCurrentStats()
		if(self.positionState == "closed"):
			scheduler.enter(self.interval_when_closed, self.priority, self.run)
		else:
			scheduler.enter(self.interval_when_opened, self.priority, self.run)


################################################
# MAIN SECTION
################################################
parser = argparse.ArgumentParser(description="JAKT bot")
parser.add_argument("-c", "--config", help="configuration JSON file", default="config.json")
args = vars(parser.parse_args())

while True:
	if path.exists(args["config"]):
		try:
			f = open(args["config"], encoding = 'utf-8')
			config = json.load(f)
			f.close()
			print("{} loaded".format(args["config"]))
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

		scheduler = sched.scheduler(time.time, time.sleep)

		'''
		futures = Futures(
			key=config["BinanceAPI"]["key"],
			secret=config["BinanceAPI"]["secret"],
			base_url=config["BinanceAPI"]["base_url"]
		)
		'''
		
		futures = Futures(key=config["BinanceAPI"]["key"], secret=config["BinanceAPI"]["secret"])

		pairsCount = 0
		for pair in config["pairs"]:
			if not pair["enable"]:
				continue
			A = JAKT(
				pair=pair,
				color=config["static"]["colors"][pair["color"]],
				loggingLevel=config["loggingLevel"],
				LINE=config["LINE"]
			)
			scheduler.enter(1, A.priority, A.run)
			pairsCount += 1

		if pairsCount > 0:
			time.sleep(random.randint(2, 3))
			try:
				print("getting started...")
				scheduler.run()
			except NameError as e:
				print(e)
		else:
			print("no pair to run.")
	else:
		print("could not load the configuration file!")

	print("retry to load {} again in 30 seconds...".format(args["config"]))
	time.sleep(30)