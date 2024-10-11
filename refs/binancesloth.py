from sys import exit
from os import system, path, chdir, getcwd
from collections import defaultdict
import sched
import time
import numpy as np
import  requests
import talib
#from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures
#from binance.error import ClientError
import json
import random
import urllib3
import subprocess
import platform
from colorama import Fore, Style, init as colorama_init
from tabulate import tabulate


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
colorama_init(autoreset=True)

class BinanceSloth:
	def __init__(self, pair):
		#c configuration loading and LINE test
		self.pair = pair
		self.logging = None
		self.logging = Logging(
			name=self.pair["crypto"]+self.pair["asset"],
			color=self.pair["color"],
			loggingLevel=self.pair["loggingLevel"]
		)

		# Test logging
		self.testLogging()

		# Binance Futures preparation
		self.connect()

		# Display basic account information
		self.account = None
		self.fetchAccount()

		#self.showAccount()
		#self.showBalance()
		#self.closeAllPositions()
		self.test()

	def test(self):
		self.logging.pprint(self.futures.api_trading_status())
		
	def showBalance(self):
		# being designed more sassy showing
		self.logging.pprint(self.account["balances"])

	def closeAllPositions(self):
		pass
		#self.futures

	def showAccount(self):
		self.logging.pprint(self.account)
	
	def fetchAccount(self):
		self.account = defaultdict(dict)
		accOnline = self.futures.account(ecvWindow=2000)
		self.account["canTrade"] = accOnline["canTrade"]
		self.account["totalWalletBalance"] = accOnline["totalWalletBalance"]
		self.account["totalCrossUnPnl"] = accOnline["totalCrossUnPnl"]
		self.config["crypto"] = []
		self.config["assets"] = []
		self.config["symbols"] = []
		for pair in self.config["pairs"]:
			self.config["crypto"].append(pair["crypto"])
			self.config["assets"].append(pair["asset"])
			self.config["symbols"].append(pair["crypto"]+pair["asset"])
		accTmpAssets = []
		for asset in accOnline["assets"]:
			if asset["asset"] in self.config["assets"]:
				accTmpAssets.append(asset)
		self.account["assets"] = accTmpAssets

		balancesTmp = []
		for balance in self.futures.balance():
			if float(balance["balance"]) != 0.0:
				balancesTmp.append(balance)
		self.account["balances"] = balancesTmp
		#self.account["positions"] = accOnline["positions"]
		self.account["dualSidePosition"] = self.futures.get_position_mode()["dualSidePosition"]
		#self.logging.pprint(self.futures.get_position_mode())
		#self.logging.pprint(self.config["assets"])
		#self.logging.pprint(accOnline["positions"])
		symbolsTmp = []
		symbolsMonitoredTmp = []
		for position in accOnline["positions"]:
			if position["symbol"] in self.config["symbols"]:
				symbolsMonitoredTmp.append(position)
			if float(position["entryPrice"]) != 0.0:
				symbolsTmp.append(position)
		self.account["positions"] = symbolsTmp
		self.account["positionsRelateToPairs"] = symbolsMonitoredTmp

	def testLogging(self):
		self.logging.debug("debug msg")
		self.logging.general("general msg")
		self.logging.info("info msg")
		self.logging.success("success msg")
		self.logging.warning("warning msg")
		self.logging.error("error msg")
		self.logging.critical("critical msg")

	def connect(self, retrySecondMin=5, incrementSecond=10, timeout=60*1):
		seconds = retrySecondMin
		connectionPassed = 0
		connectionTotal = 1 #some situation might require more than 1 successful connection to make sure
		while connectionPassed < connectionTotal:
			try:
				futures.ping()
			except:
				self.logging.warning("API connection failed, retry in {} seconds".format(seconds))
				time.sleep(seconds)
				if seconds < timeout:
					seconds += incrementSecond
				else:
					return False
			else:
				self.logging.info("API connected")
				connectionPassed += 1
				return True
			

	def run(self):
		scheduler = sched.scheduler(time.time, time.sleep)
		pairsCount = 0
		for pair in self.config["pairs"]:
			if not pair["enable"]:
				continue
			sloth = self.Sloth(
				pair=pair,
				color=self.config["static"]["colors"][pair["color"]],
				loggingLevel=self.config["loggingLevel"],
				LINE=self.config["LINE"]
			)
			scheduler.enter(1, sloth.priority, sloth.run)
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

class Test:
	def testTAlib():
		c = np.random.randn(100)
		k, d = talib.STOCHRSI(c)
		rsi = talib.RSI(c)
		k, d = talib.STOCHF(rsi, rsi, rsi)
		rsi = talib.RSI(c)
		k, d = talib.STOCH(rsi, rsi, rsi)
		print("TA-lib OK") 

class LINE:
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
	def __init__(self, name, color="LIGHTBLACK_EX", loggingLevel="INFO"):
		self.logging = None
		self.name = name
		self.color = color
		self.loggingLevel = loggingLevel
		
		import logging as logginglib
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

	def addPrefix(self, msg):
		if self.color == "LIGHTBLACK_EX":
			styledMsg = Fore.LIGHTBLACK_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTBLUE_EX":
			styledMsg = Fore.LIGHTBLUE_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTCYAN_EX":
			styledMsg = Fore.LIGHTCYAN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTGREEN_EX":
			styledMsg = Fore.LIGHTGREEN_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTMAGENTA_EX":
			styledMsg = Fore.LIGHTMAGENTA_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTRED_EX":
			styledMsg = Fore.LIGHTRED_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTWHITE_EX":
			styledMsg = Fore.LIGHTWHITE_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		elif self.color == "LIGHTYELLOW_EX":
			styledMsg = Fore.LIGHTYELLOW_EX+"{} ".format(self.name)+Style.RESET_ALL+"{}".format(msg)
		return styledMsg

	def debug(self, msg):
		self.logging.debug(self.addPrefix(self.tint(msg, "LIGHTBLACK_EX")))

	def general(self, msg):
		self.logging.info(self.addPrefix(msg)) 

	def info(self, msg):
		self.logging.info(self.addPrefix(self.tint(msg, "LIGHTBLUE_EX")))
	
	def success(self, msg):
		self.logging.info(self.addPrefix(self.tint(msg, "LIGHTGREEN_EX")))

	def warning(self, msg):
		self.logging.warning(self.addPrefix(self.tint(msg, "LIGHTYELLOW_EX")))

	def error(self, msg):
		self.logging.error(self.addPrefix(self.tint(msg, "LIGHTRED_EX")))

	def critical(self, msg):
		self.logging.critical(self.addPrefix(self.tint(msg, "LIGHTMAGENTA_EX")))

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
		self.debug(self.tint(msg, color))

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
			self.log.warning(
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