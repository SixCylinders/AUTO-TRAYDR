# Changelog 0.9.6
"""
minor bugfixes
buys more in november because of election stuff
"""
#recommended cron timing below. Program is able to handle other cron timings, buy why would you change it? There's no need for it. you also gotta change TRADE_HOUR and RESET_HOUR
#0 12,16 * * *
#full command to be pasted into cron

#0 12,16 * * * bash -c "source /home/myVenv/bin/activate && /home/myVenv/bin/python3 /home/AUTOTRAYDR.py"

import robin_stocks.robinhood as rs #i forgor what this one does :(
import sys #save terminal to txt
import json #save file
import time #time.sleep reduces CPU usage by waiting N seconds
import os #gets relative filepath
import pyotp #auto 2factor if you choose
import random
from stopit import threading_timeoutable as timeoutable #prevents program from running FOREVER
from datetime import datetime #get time

TRADE_PARAM_DISABLED = 7050 #dummy value
DEFAULT_PERFORMANCE = -5667.0 #dummy value
TRADE_HOUR = 12 #hour at which program will trade
RESET_HOUR = 16 #same thing but for reset
BROKERAGE_ROLLING_AVERAGE = -1.33338 #dummy value
ADD_SAVINGS_DAY = 1 #day of month when savings items will get updated
MIN_BUY_DOLLAR = 1.25 #minimum buy order amount
INDIVIDUAL_CRASH = -8.0 #if percentChange for stock below this, treat as if it crashed
DAYS_TO_DIVIDE_MONEY_ACROSS = 60 #daily budget calculated as money/this variable

stockList = ['ADI', 'ADP', 'ACN', 'AFL', 'ALAB', 'AMAT', 'AMCX', 'AMD', 'AMZN', 'ANET', 'AON', 'APH', 'APO', 'APP', 'ARES', 'ARHS', 'ARM', 'AVGO', 'AXP', #developer stocklist teehee
	'BAC', 'BKNG', 'BLK', 'BR', 'BRK.B', 'BSX', 'BX',
	'C', 'CARR', 'CAT', 'CEG', 'CIFR', 'CLSK', 'COPX', 'COST', 'CPER', 'CRM', 'CRWD', 'CSWI',
	'DELL', 'DIA', 'DHR', 'DJT', 'DTEGY', 'DTST', 
	'EBAY', 'EME', 'EMR', 'ERO',
	'FI', 'FICO', 'FIX', 'FLTW', 
	'GD', 'GDDY', 'GDX', 'GE', 'GEV', 'GLD', 'GME', 'GOLD', 'GOOGL', 'GS', 'GWW',
	'HCA', 'HD', 'HOOD', 'HTHIY', 'HUBB',
	'IAU', 'IBM', 'IBKR', 'ICE', 'IDCC', 'INTC', 'INTU', 'IONQ', 'IRM', 'ISRG', 'ITA', 'IVV', 
	'JPM', 
	'KGC', 'KKR', 'KLAC', 'KO',
	'LIN', 'LLY', 'LMT', 'LNG', 'LNTH', 'LOGI', 'LRCX', 
	'MA', 'MCO', 'META', 'MO', 'MPLX', 'MS', 'MSFT', 'MSI', 'MSTR', 'MU', 
	'NDAQ', 'NKTX', 'NLR', 'NNE', 'NOC', 'NOW', 'NTAP', 'NVDA', 
	'O', 'OKLO', 'ORCL',
	'PAA', 'PANW', 'PEG', 'PG', 'PGR', 'PH', 'PLTR', 'PM', 'PWR',
	'QCOM', 'QQQM', 'QUAL',
	'RCRUY', 'RDDT', 'RKLB', 'RTX',
	'SAP', 'SCCO', 'SHOP', 'SHW', 'SLV', 'SMCI', 'SPGI', 'SPHD', 'SPHQ', 'SPMO', 'SPY', 'SPYG', 'STLD', 'SMH', 'SPHD', 'SYK',
	'T', 'TDG', 'TT', 'TTD', 'TM', 'TMUS', 'TRGP', 'TRV', 'TSLA', 'TSM', 'TW', 'TXN',
	'UBS', 'UEC', 'UMI', 'UNH',
	'V', 'VINC', 'VONG', 'VOO', 'VOOG', 'VST', 'VTI', 'VUG', 'VWO',
	'WAB', 'WELL', 'WMB', 'WMT', 
	'X', 'XAR', 'XLK', 'XLF', 'XOM',
]
cryptoList = ['BTC', 'ETH', 'DOGE', 'SHIB']
loadedDevPrefs = False #overrides setup if dev prefs were loaded
indentNum = 1
defconLevel = 0
failedTrades = 0 #prevents 100s of failed orders on occasional market closure
"""
DEFCON levels
0 - Program will execute trades and perform as designed
1 - Program will NOT execute trades, but it will do everything else
2 - Program pretends to do everything. Values don't get changed
"""

#Saved data
stockInfo = {}
budget = {
	"brokerage": 0.0, #actual value of brokerage
	"brokerageRollingAverage": [BROKERAGE_ROLLING_AVERAGE] * 14,

	"dailyBudget": 0.0,

	"moneyLeftDaily": 0.0,
	"moneyLeftTotal": 0.0,
}
savings = {
	"main": {"max": 99999999999, "balance": 2500, "addMonthly": 300},
	"crash": {"max": 400, "balance": 0, "addMonthly": 2}, #crash added daily
}
tradeParams = {
	"pcBottomThreshold": 0.0,
	"pcBottomNum": 0,
	"pcBottomBudget": 0.0,
	"pcTopThreshold": 0.0,
	"pcTopNum": 0,
	"pcTopBudget": 0.0,

	"equityBottomThreshold": 0.0,
	"equityBottomNum": 0,
	"equityBottomBudget": 0.0,

	"ageOldestThreshold": 0,
	"ageOldestNum": 0,
	"ageOldestBudget": 0.0,

	"performanceAbsThreshold": 0.0, #if performancenum below, dont buy at all
	"performanceTopNum": 0,
	"performanceTopBudget": 0.0,

	"randomNum": 0,
	"randomBudget": 0.0,
}
	
oneTime = {
	"forceWeekend": False, #input args
	"forceTrade": False,
	"forceReset": False,

	"testWeekend": False, #test functionality
	"testTrade": False,
	"testReset": False,

	"weekendCheck": False, #prevent re-run on same day
	"resetCheck": False,
	"tradeCheck": False,
}
accountInfo = { #how to encrypt this variable hmmmmmm thinky thinky
	"username": "", #at the moment, the only real security for this is "Why would someone go after some random guy instead of a big company"
	"password": "",
	"auto2factor": False,
	"auto2FactorCode": "",
}
misc = {
	"performanceDays": 50, #num of days to track performance. Recommended to be at least 30 for crash detection to work
	"devMode": False, #automatically propagates dev prefs since im tired of updating them every time i revise this program
	"performanceLowConfidenceThreshold": 0.0, #at what performanceNum will a stock be labeled as low confidence
	"performanceNormalThreshold": 0.0, #inverse. lc to normal
}
#/Saved data
"""
TODO encrypt passswords
TODO make manual
TODO add all thresholds to tradeparameter
TODO allow other trade times
TODO cant get out of errorcode = 1
TODO allow no 2factor in login()
"""

now = datetime.now()
weekday = now.weekday()
hour = now.hour
minute = now.minute
day = now.day
month = now.month
year = now.year

#startup/shutdown
def verifyDevMode(): 
	global indentNum
	global stockInfo
	global tradeParams
	global misc
	indentNum += 1
	pnt("Entered verifyDevMode")

	pnt("verifying stocks")
	toremove = []
	for stock in stockInfo.keys():
		exists = False
		for ref in stockList:
			if stock == ref:
				exists = True
		for ref in cryptoList:
			if stock == ref:
				exists = True
		if not exists:
			pnt("stock " + stock + " removed from stockInfo")
			toremove.append(stock)
	for stock in toremove:
		stockInfo.pop(stock)
	for ref in stockList:
		exists = False
		for stock in stockInfo.keys():
			if stock == ref:
				exists = True
		if not exists:
			pnt("stock " + ref + " added to stockInfo")
			stockInfo[ref] = {}
	for ref in cryptoList:
		exists = False
		for stock in stockInfo.keys():
			if stock == ref:
				exists = True
		if not exists:
			pnt("stock " + ref + " added to stockInfo")
			stockInfo[ref] = {}
			stockInfo[ref]['isCrypto'] = True
	aa = []
	for stock in stockInfo:
		aa.append(stock)

	pnt("verifying tradeParams")
	tradeParams = {
		"pcBottomThreshold": -0.5,
		"pcBottomNum": 5,
		"pcBottomBudget": 1.25,
		"pcTopThreshold": 1.0,
		"pcTopNum": 3,
		"pcTopBudget": 1.25,

		"equityBottomThreshold": 300.0,
		"equityBottomNum": 20,
		"equityBottomBudget": 1.25,

		"ageOldestThreshold": 30,
		"ageOldestNum": 3,
		"ageOldestBudget": 0.5,

		"performanceAbsThreshold": -3.0,
		"performanceTopNum": 5,
		"performanceTopBudget": 1.5,

		"randomNum": 5,
		"randomBudget": 0.5,
	}
	misc['performanceLowConfidenceThreshold'] = 0.1
	misc['performanceNormalThreshold'] = 1.0
	misc['performanceDays'] = 31

	pnt("verifying savings")
	balances = []
	for item in savings:
		balances.append(savings[item]['balance'])
		savings[item] = {}
	savings['main']['addMonthly'] = 300
	savings['main']['max'] = 100000
	savings['crash']['addDaily'] = 2
	savings['crash']['max'] = 500
	savings['car']['addMonthly'] = 300
	savings['car']['max'] = 20000
	savings['house']['addMonthly'] = 200
	savings['house']['max'] = 1000000
	for item in savings:
		try:
			savings[item]['balance'] = balances[0]
			balances.pop(0)
		else:
			pnt("no balance for " + item)
			savings[item]['balance'] = 0

	pnt("Exited verifyDevMode")
	indentNum -= 1
def startup(condition):
	global indentNum
	global oneTime
	global defconLevel
	indentNum = 0
	indentNum += 1
	"""
	Startup conditions
	0 - normal
	1 - user activated setup
	2 - test all mainLoop functions
	3 - user activated reset
	4 - user activated trade
	5 - update stockinfo only
	"""
	pnt("Entered startup")
	pnt("condition " + str(condition))
	number = 0
	whileNum = 0
	while True:
		number += 1
		if number >= 4 or whileNum >= 4:
			stop()
		try:
			load() #calls setup if error
			pnt("loadedDevPrefs " + str(loadedDevPrefs))
			if condition == 1 and not loadedDevPrefs:
				setupHandler(0)
			login()
			break
		except Exception as e:
			pnt("Error in startup loop")
			pnt(e)
			whileNum += 1

	if condition == 0 or condition == 1:
		oneTime['forceReset'] = False
		oneTime['forceTrade'] = False
		mainLoop()
	elif condition == 2:
		pnt("Program disarmed")
		tempArmed = defconLevel
		defconLevel = 2
		pnt("Testing weekend...")
		oneTime['testWeekend'] = True
		oneTime['testTrade'] = False
		oneTime['testReset'] = False
		mainLoop()
		login()
		pnt("Testing trade...")
		oneTime['testWeekend'] = False
		oneTime['testTrade'] = True
		oneTime['testReset'] = False
		mainLoop()
		login()
		pnt("Testing reset...")
		oneTime['testWeekend'] = False
		oneTime['testTrade'] = False
		oneTime['testReset'] = True
		mainLoop()
		oneTime['testReset'] = False
		pnt("Testing complete")
		defconLevel = tempArmed
	elif condition == 3:
		oneTime['forceReset'] = True
		oneTime['forceTrade'] = False
		mainLoop()
		oneTime['forceReset'] = False
	elif condition == 4:
		oneTime['forceReset'] = False
		oneTime['forceTrade'] = True
		mainLoop()
		oneTime['forceTrade'] = False
	elif condition == 5:
		updateStockInfo()
	pnt("Exited startup")
	indentNum -= 1
def login(): #calls setup if error
	global indentNum
	global accountInfo
	indentNum += 1
	pnt("Entered login")
	pnt("Logging in...")
	try:
		wait(1)
		if accountInfo['auto2factor']:
			totp = pyotp.TOTP(accountInfo['auto2FactorCode']).now()
			login = rs.login(accountInfo['username'], accountInfo['password'], mfa_code=totp)
		else: #no 2factor bypass
			login = rs.login(accountInfo['username'], accountInfo['password'])

		pnt("Login successful")
		pnt("Welcome, " + str(accountInfo['username']))
		pnt("Exited login")
		indentNum -= 1
	except Exception as e:
		print(e)
		pnt("Error logging in. Invalid accountInfo")
		pnt("ERROR-INVALIDLOGIN")
		pnt("Error logging in. Check spelling of your username and password")
		pnt("User- " + accountInfo['username'])
		pnt("Pass- " + accountInfo['password'])
		setupHandler(1)
		pnt("Exited login")
		indentNum -= 1
		raise ValueError("Error logging in. Check spelling of your username and password")
def logout():
	global indentNum
	indentNum += 1
	pnt("Entered logout")
	pnt("Logging out...")
	wait(1)
	rs.logout()
	pnt("Exited logout")
	indentNum -= 1

#main
def mainLoop():
	global indentNum
	global budget
	global oneTime
	indentNum += 1
	pnt("Entered mainLoop")

	isweekend = weekday > 4 and not oneTime['weekendCheck'] #skip weekends
	pnt("oneTime['forceWeekend'] " + str(oneTime['forceWeekend']))
	pnt("isweekend " + str(isweekend))
	pnt("oneTime['testWeekend'] " + str(oneTime['testWeekend']))
	if oneTime['forceWeekend'] or isweekend or oneTime['testWeekend']:
		pnt("Weekend")
		if defconLevel != 2:
			oneTime['weekendCheck'] = True

	istrade = weekday <= 4 and hour == TRADE_HOUR and not oneTime['tradeCheck'] #trade on weekday at noon
	pnt("oneTime['forceTrade'] " + str(oneTime['forceTrade']))
	pnt("istrade " + str(istrade))
	pnt("oneTime['testTrade'] " + str(oneTime['testTrade']))
	if oneTime['forceTrade'] or istrade or oneTime['testTrade']:
		pnt("devMode " + str(misc['devMode']))
		if misc['devMode']:
			verifyDevMode()
		if defconLevel != 2:
			oneTime['tradeCheck'] = True
			oneTime['resetCheck'] = False
		updateStockInfo()
		save()
		trade()

	isreset = hour == RESET_HOUR and weekday <= 4 and not oneTime['resetCheck'] #reset at 1600 on weekdays
	pnt("oneTime['forceReset'] " + str(oneTime['forceReset']))
	pnt("isreset " + str(isreset))
	pnt("oneTime['testReset'] " + str(oneTime['testReset']))
	if oneTime['forceReset'] or isreset or oneTime['testReset']:
		if defconLevel != 2:
			oneTime['resetCheck'] = True #reset on trade day
		save()
		reset()

	pnt("Exited mainLoop")
	indentNum -= 1
def reset():
	global indentNum
	global budget
	global stockInfo
	global oneTime
	global savings
	indentNum += 1
	pnt("Entered reset")
	
	pnt("Resetting oneTime...")
	oneTime['testWeekend'] = False
	oneTime['testTrade'] = False
	oneTime['testReset'] = False
	oneTime['forceWeekend'] = False
	oneTime['forceTrade'] = False
	oneTime['forceReset'] = False
	oneTime['weekendCheck'] = False
	oneTime['tradeCheck'] = False
	pnt("Reset oneTime")
	
	pnt("Incrementing daysSinceTrade...")
	if defconLevel != 2:
		for stock in stockInfo:
			stockInfo[stock]['daysSinceTrade'] += 1
			pnt(stock + " " + str(stockInfo[stock]['daysSinceTrade']))
	else:		
		pnt("daysSinceTrade not incremented")
	pnt("Incremented daysSinceTrade")

	pnt("Getting brokerage balance...")
	wait(1)
	userProf = rs.account.build_user_profile()
	pnt(userProf)
	budget['moneyLeftDaily'] = 0.0
	budget['brokerage'] = float(userProf['cash'])
	budget['brokerageRollingAverage'] = budget['brokerageRollingAverage'][-1:] + budget['brokerageRollingAverage'][:-1] #rotate
	budget['brokerageRollingAverage'][0] = budget['brokerage']
	budget["moneyLeftTotal"] = budget['brokerage']
	for item in budget['brokerageRollingAverage']: #use lowest value for brokerage
		if item == BROKERAGE_ROLLING_AVERAGE and budget['moneyLeftTotal'] == budget['brokerage']:
			budget['moneyLeftTotal'] = budget['brokerage']
			pnt("Using today's brokerage")
		elif item < budget['moneyLeftTotal']: #recurring deposits for WHATEVER reason are multiplied by 2 when theyre processing
			budget["moneyLeftTotal"] = item #robinhood does this, not me. A recurring deposit of $5 would cause robinhood to think brokerage is actually $10 (plus pre-existing funds) for some fucking reason
			pnt("Set money to " + str(budget['moneyLeftTotal']))
	pnt("Got brokerage balance " + str(budget["moneyLeftTotal"]))

	pnt("Allocating savings...")
	for item in savings:
		if budget["moneyLeftTotal"] > savings[item]['balance']:
			if day == ADD_SAVINGS_DAY and savings[item]['balance'] < savings[item]['max']: #monthly
				try:
					savings[item]['balance'] += savings[item]['addMonthly']
					pnt("Added " + str(savings[item]['addMonthly']) + " to " + item)
				except:
					pass

			if savings[item]['balance'] < savings[item]['max']: #daily
				try: 
					savings[item]['balance'] += savings[item]['addDaily']
					pnt("Added " + str(savings[item]['addDaily']) + " to " + item)
				except:
					pass

			if item == "crash" and savings[item]['balance'] > savings[item]['max']: #crash can go over limit
					savings[item]['balance'] += savings[item]['addDaily']*0.5

			budget["moneyLeftTotal"] -= savings[item]['balance']
			pnt(str(item) + str(savings[item]['balance']))
			pnt("Success")
		else:
			pnt("Not enough money to allocate to " + str(item))
			budget["moneyLeftTotal"] = 0
	pnt("Savings allocated ")
	pnt(budget['moneyLeftTotal'])
	
	pnt("Filling stocks...")
	for stock in stockInfo:
		if budget['moneyLeftTotal'] < stockInfo[stock]['stockMoney']:
			pnt("Tried to allocate " + str(stockInfo[stock]['stockMoney']) + " to stock")
			continue
		if defconLevel != 2:
			budget['moneyLeftTotal'] -= stockInfo[stock]['stockMoney']
		else:
			pnt("Not filled")
	pnt("Filled stocks")
	pnt(budget['moneyLeftTotal'])

	pnt("Filling moneyLeftDaily with normal amount")
	budget['dailyBudget'] = budget['moneyLeftTotal']/DAYS_TO_DIVIDE_MONEY_ACROSS
	if budget['moneyLeftTotal'] > budget['dailyBudget']:
		if defconLevel != 2:
			pnt("moneyLeftDaily refilled with " + str(budget['dailyBudget']))
			budget['moneyLeftDaily'] += budget['dailyBudget']
			budget['moneyLeftTotal'] -= budget['dailyBudget']
		else:
			pnt("moneyLeftDaily refilled with " + str(budget['dailyBudget']) + " but not really")
	else:
		pnt("Program tried to add $" + str(budget['dailyBudget']) + " to daily budget with $" + str(budget['moneyLeftTotal']) + " left")
	pnt("Filled moneyLeftDaily with normal amount")
	pnt(budget['moneyLeftTotal'])

	if month == 11: #election shenanigans, so spend more
		pnt("NOVEMBER!!!!!!!!!")
		if budget['moneyLeftTotal'] > budget['dailyBudget']:
			if defconLevel != 2:
				pnt("moneyLeftDaily overfilled with " + str(budget['dailyBudget']))
				budget['moneyLeftDaily'] += budget['dailyBudget']
				budget['moneyLeftTotal'] -= budget['dailyBudget']
			else:
				pnt("moneyLeftDaily overfilled with " + str(budget['dailyBudget']) + " but not really")
		else:
			pnt("Program tried to add $" + str(budget['dailyBudget']) + " to daily budget with $" + str(budget['moneyLeftTotal']) + " left")
	pnt("Exited reset")
	indentNum -= 1
	
#trade
def crashCheck():
	global indentNum
	indentNum += 1
	pnt("Entered crashCheck")
	pnt("Checking for market crash")
	for stock in stockInfo:
		newPerf = 0
		for i in stockInfo[stock]['performance']: #check performance excluding today
			if i == stockInfo[stock]['performance'][0]: #skip today
				continue
			if i == DEFAULT_PERFORMANCE:
				continue
			newPerf += i
		newPerf /= misc['performanceDays']-1
		if stockInfo[stock]['percentChange'] < INDIVIDUAL_CRASH and newPerf > 1:
			pnt(stock + " crashed")
			pnt("Spending 5% of crash savings on " + stock)
			stockInfo[stock]['stockMoney'] += savings['crash']['balance']*0.05
			savings['crash']['balance'] -= savings['crash']['balance']*0.05
	pnt("Exited crashCheck")
	indentNum -= 1
def trade():
	global indentNum
	global stockInfo
	global budget
	global tradeParams
	indentNum += 1
	pnt("Entered trade")

	crashCheck()

	sortByParameter('equity')
	#buy bottom equity
	pnt("buy bottom equity")
	tradeParameter(
		tradeParams['equityBottomNum'], 
		tradeParams['equityBottomBudget'], 
		0,
		True,
	)

	#buy oldest
	sortByParameter('daysSinceTrade')
	pnt("buy oldest")
	tradeParameter(
		tradeParams['ageOldestNum'], 
		tradeParams['ageOldestBudget'], 
		1, 
		False,
	)

	sortByParameter('percentChange')
	#buy bottom pc
	pnt("buy bottom pc")
	tradeParameter(
		tradeParams['pcBottomNum'], 
		tradeParams['pcBottomBudget'], 
		2, 
		True, 
	)

	#buy top pc
	pnt("buy top pc")
	tradeParameter(
		tradeParams['pcTopNum'], 
		tradeParams['pcTopBudget'], 
		3, 
		False,
	)

	sortByParameter('performanceNum')
	#buy top performer
	pnt("buy top performer")
	tradeParameter(
		tradeParams['performanceTopNum'],
		tradeParams['performanceTopBudget'],
		4,
		False,
	)

	#randomize order
	pnt("Randomizing order...")
	lista = list(range(0, len(stockInfo)))
	random.shuffle(lista)
	i = 0
	for stock in stockInfo:
		num = random.randrange(0, len(stockInfo)+1, 1)
		stockInfo[stock]['order'] = int(lista[i])
		i += 1
	pnt("Success")

	pnt("buy random")
	tradeParameter(
		tradeParams['randomNum'],
		tradeParams['randomBudget'],
		5,
		False,
	)

	pnt("Spending at least quarter of daily budget")
	while budget['moneyLeftDaily'] > budget['dailyBudget']/4: #spend some money every day
		lista = list(range(0, len(stockInfo)))
		random.shuffle(lista)
		i = 0
		for stock in stockInfo:
			num = random.randrange(0, len(stockInfo)+1, 1)
			stockInfo[stock]['order'] = int(lista[i])
			i += 1
		tradeParameter(
			1,
			tradeParams['randomBudget'],
			5,
			False,
		)

	pnt("Placing orders")
	for stock in stockInfo:
		if stockInfo[stock]['stockMoney'] < MIN_BUY_DOLLAR:
			pnt(stock + " $" + str(stockInfo[stock]['stockMoney']))
			continue
		number = 0
		while number != 3:
			if placeOrder(stock, stockInfo[stock]['stockMoney'], True):
				pnt("Success")
				break
			else:
				number += 1
				pnt("Retrying " + str(number))
		if number == 3:
			pnt("Timed out")
	pnt("Exited trade")
	indentNum -= 1
def tradeParameter(num, shoppingCart, condition, isBottom):
	global indentNum
	global stockInfo
	global budget
	indentNum += 1
	pnt("Entered tradeParameter")
	pnt("num " + str(num))
	pnt("shoppingCart " + str(shoppingCart))
	pnt("condition " + str(condition))
	pnt("isBottom " + str(isBottom))
	"""
	Condition: unique code to be run for
	0 = buy bottom equity
	1 = buy oldest
	2 = buy bottom pc
	3 = buy top pc
	4 = buy top performer
	5 = buy random
	"""
	newShoppingCart = shoppingCart
	localBought = []
	limitNum = num
	if not isBottom:
		limitNum = len(stockInfo) - num
	isBreak = False
	doPrint = True

	if num == TRADE_PARAM_DISABLED or num == 0:
		pnt("Disabled")
		pnt("Exited tradeParameter")
		indentNum -= 1
		return

	if month == 11: #spend twice as much in november because of election shenanigans
		newShoppingCart *= 2
	
	while not isBreak:
		if limitNum > len(stockInfo) or limitNum < 0:
			pnt("Made it to the bottom of the list. no more companies qualify for this parameter")
			break
		for stock in stockInfo:
			if len(localBought) >= num:
				if not isBreak:
					pnt("Bought enough stocks")
				isBreak = True
				continue

			if isBottom and stockInfo[stock]['order'] > limitNum: #stay in bounds
				continue
			if not isBottom and stockInfo[stock]['order'] < limitNum:
				continue

			alreadyBought = False #prevent repeats
			for stockb in localBought:
				if stockb == stock:
					if doPrint:
						pnt("Already bought " + stock)
					alreadyBought = True
			if alreadyBought:
				continue

			if condition == 1: #thresholds
				if stockInfo[stock]['daysSinceTrade'] < tradeParams['ageOldestThreshold']:
					if doPrint:
						pnt(stock + " not old enough " + str(stockInfo[stock]['daysSinceTrade']))
					continue
			elif condition == 2:
				if stockInfo[stock]['percentChange'] > tradeParams['pcBottomThreshold']:
					if doPrint:
						pnt(stock + " pc not below theshold " + str(stockInfo[stock]['percentChange']))
					continue
			elif condition == 0:
				if stockInfo[stock]['equity'] > tradeParams['equityBottomThreshold']*stockInfo[stock]['confidence']: #equity threshold accounts for performance
					if doPrint:
						pnt(stock + " equity greater than minimum " + str(stockInfo[stock]['equity']))
					continue

			if condition != 0: #equity completely unaffected
				if condition != 5: #random is unaffected by lc
					pnt("Confidence factor " + str(stockInfo[stock]['confidence']))
					newShoppingCart *= stockInfo[stock]['confidence']
				if stockInfo[stock]['performanceNum'] < tradeParams['performanceAbsThreshold']: 
					pnt(stock + " performing very low " + str(stockInfo[stock]['performanceNum']))
					newShoppingCart *= stockInfo[stock]['confidence']

			pnt(stock + " candidate for trade")
			pnt(stockInfo[stock])

			if isOrderValid(stock, newShoppingCart, True):
				budget['moneyLeftDaily'] -= newShoppingCart
				stockInfo[stock]['stockMoney'] += newShoppingCart
				localBought.append(stock)
				pnt("Added $" + str(newShoppingCart) + " to " + stock)
				pnt("money-" + str(stockInfo[stock]['stockMoney']))
			else:
				pnt("Invalid order")
				isBreak = True

		if len(localBought) < num:
			pnt("expanded range to buy enough stocks")
			doPrint = False
			if isBottom:
				limitNum += 1
			else:
				limitNum -= 1
	pnt("Exited tradeParameter")
	indentNum -= 1
def placeOrder(stock, shoppingCart, buy): #returns false if trade fails
	global indentNum
	global budget
	global failedTrades
	indentNum += 1
	pnt("Entered placeOrder")
	pnt("stock " + stock)
	pnt("shoppingCart " + str(shoppingCart))
	pnt("buy " + str(buy))

	if hour >= 16 or (hour < 9 and minute < 30):#markets closed anyway
		pnt("Markets closed, skipping order")
		pnt("Exited placeOrder")
		indentNum -= 1
		return True

	wait(1)
	userProf = rs.account.build_user_profile()
	oldBrokerage = float(userProf['cash'])
	wait(1)
	if buy:
		if defconLevel == 0:
			if stockInfo[stock]['isCrypto']:
				rs.orders.order_buy_crypto_by_price(stock, shoppingCart)
			else:
				rs.orders.order_buy_fractional_by_price(stock, shoppingCart)
		else:
			pnt("Didn't buy shit")
		pnt(stock + " bought for $" + str(shoppingCart))
	else:
		if defconLevel == 0:
			if stockInfo[stock]['isCrypto']:
				rs.orders.order_sell_crypto_by_price(stock, shoppingCart, shoppingCart+0.1)
			else:
				rs.orders.order_sell_fractional_by_price(stock, shoppingCart)
		else:
			pnt("Didn't sell shit")
		pnt(stock + " sold for $" + str(shoppingCart))

	if defconLevel == 2:
		pnt("Exited placeOrder")
		indentNum -= 1
		return True
	pnt("Waiting 30 seconds so robinhood doesn't throw a fit")
	wait(30)
	newUserProf = rs.account.build_user_profile()
	newBrokerage = float(newUserProf['cash'])

	if oldBrokerage == newBrokerage: #fail
		failedTrades += 1
		if defconLevel != 0 or failedTrades > 10:
			pnt("No way to tell if trade failed or succeeded")
			pnt("Exited placeOrder")
			indentNum -= 1
			return True
		else:
			pnt("Trade failed " + stock + " $" + str(shoppingCart))
			try:
				pnt("Trying to cancel order...")
				orders = rs.orders.get_all_open_stock_orders()
				info = rs.orders.cancel_stock_order(orders[0]['id'])
				pnt("Success")
			except Exception as e:
				pnt("Couldn't get orders")
				pnt(e)
			pnt("Exited placeOrder")
			indentNum -= 1
			return False

	else: #success
		if buy:
			if defconLevel != 2:
				stockInfo[stock]['daysSinceTrade'] = 0
				stockInfo[stock]['stockMoney'] -= shoppingCart
				pnt(stock + "money-" + str(stockInfo[stock]['stockMoney']))
			else:
				pnt("Didn't negate shit")
		else:
			stockInfo[stock]['daysSinceTrade'] = 0
			pnt(stock + " daysSinceTrade " + str(stockInfo[stock]['daysSinceTrade']))

		pnt("Exited placeOrder")
		indentNum -= 1
		return True
def isOrderValid(stock, shoppingCart, buy): #returns true if should buy/sell
	global indentNum
	indentNum += 1
	pnt("Entered isOrderValid")
	pnt("stock " + stock)
	pnt("shoppingCart " + str(shoppingCart))
	pnt("buy " + str(buy))

	if buy:
		if budget['moneyLeftDaily'] <= 0.0: #no funds
			pnt("Not enough money $" + str(budget['moneyLeftDaily']))
			pnt("Exited isOrderValid")
			indentNum -= 1
			return False

		loweredPrice = False #if wanting to buy too much, lower price
		while shoppingCart > budget['moneyLeftDaily']:
			shoppingCart -= 0.01
			loweredPrice = True
		if loweredPrice:
			pnt("Insufficient funds initially. Shopping cart lowered to $" + str(shoppingCart))

		pnt("Valid buy")
		pnt("Exited isOrderValid")
		indentNum -= 1
		return True
	else:
		if stockInfo[stock]['equity'] < shoppingCart:
			pnt("Insufficient equity to sell")
			pnt("ATTEMPTED TO SELL $" + str(shoppingCart) + " OF " + stock + ". INSUFFICIENT EQUITY")
			pnt("Exited isOrderValid")
			indentNum -= 1
			return False

		pnt("Valid sell")

		pnt("Exited isOrderValid")
		indentNum -= 1
		return True

#save/load
def save():
	global indentNum
	global stockInfo
	global budget
	global tradeParams
	global oneTime
	global misc
	indentNum += 1
	pnt("Entered save")

	pnt("Saving...")
	scriptDir = os.path.dirname(__file__)
	absFilePath = os.path.join(scriptDir, "savedLogin.txt")
	with open(absFilePath, "w") as fp:
		json.dump(accountInfo, fp)
		pnt("Saved savedLogin.txt")

	jsonData = {
		'stockInfo': stockInfo,
		'budget': budget,
		'tradeParams': tradeParams,
		'oneTime': oneTime,
		'misc': misc,
		'savings': savings,
	}
	with open(os.path.join(scriptDir, "data.txt"), "w") as fp:
		json.dump(jsonData, fp)
		pnt("Saved data.txt")
	pnt("Exited save")
	indentNum -= 1
def loadVariable(blank, new): #fills blank with new only if the key exists in blank
	global indentNum
	indentNum += 1
	pnt("Entered loadVariable")
	retVal = {}
	for oldKey in blank.keys():
		found = False
		for newKey in new.keys():
			if oldKey == newKey:
				pnt("Found key " + str(newKey))
				found = True
				retVal[newKey] = new[newKey] #add to variable
		if not found:
			pnt("key " + str(oldKey) + " not found")
			pnt("adding " + oldKey + " with ->" + str(blank[oldKey]) + "<- value")
			retVal[oldKey] = blank[oldKey]
	pnt("Exited loadVariable")
	indentNum -= 1
	return retVal
def loadList(blank, new): #fills blank with new only if length of new permits, else fill with blank
	global indentNum
	indentNum += 1
	pnt("Entered loadList")
	retVal = []
	for i in range(len(blank)):
		try:
			retVal.append(new[i])
		except:
			retVal.append(blank[i])
	pnt("Exited loadList")
	indentNum -= 1
	return retVal
def load(): #calls setup and returns if error
	global indentNum
	global accountInfo
	global savings
	global stockInfo
	global oneTime
	global budget
	global tradeParams
	global misc
	indentNum += 1
	pnt("Entered load")

	try:
		scriptDir = os.path.dirname(__file__)
		relPath = "savedLogin.txt"
		absFilePath = os.path.join(scriptDir, relPath)
		with open(absFilePath, "r") as fp:
			accountInfo = loadVariable(accountInfo, json.load(fp))
			pnt("Loaded savedLogin.txt")
	except:
		pnt("Failed to load savedLogin.txt. Either file doesn't exist, or incorrect user/pass")
		setupHandler(1)
		pnt("Exited load with savedLogin.txt error")
		indentNum -= 1
		raise ValueError("Failed to load savedLogin.txt. Either file doesn't exist, or incorrect user/pass")

	try:
		jsonData = {}
		scriptDir = os.path.dirname(__file__)
		with open(os.path.join(scriptDir, "data.txt"), "r") as fp:
			jsonData = json.load(fp)
			pnt("Loaded data.txt")
	except:
		pnt("Failed to load data.txt")
		setupHandler(2)
		pnt("Exited load with data.txt error")
		indentNum -= 1
		raise ValueError("Failed to load data.txt")

	try:
		stockInfo = jsonData['stockInfo']
	except:
		pnt("Error loading stockInfo. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		budget = loadVariable(budget, jsonData['budget'])
	except:
		pnt("Error loading budget. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		tradeParams = loadVariable(tradeParams, jsonData['tradeParams'])
	except:
		pnt("Error loading tradeParams. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		oneTime = loadVariable(oneTime, jsonData['oneTime'])
	except:
		pnt("Error loading oneTime. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		misc = loadVariable(misc, jsonData['misc'])
	except:
		pnt("Error loading misc. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		savings = jsonData['savings']
	except:
		pnt("Error loading savings")
	pnt("Exited load")
	indentNum -= 1

#setup
def setupMainMenu(errorCode):
	global indentNum
	indentNum += 1
	pnt("Entered mainMenu")
	pnt("errorCode " + str(errorCode))

	if errorCode == 1:
		pnt("Exited mainMenu")
		indentNum -= 1
		return 4 #go to account

	pnt("What would you like to edit?")
	pnt("1 - Stocks")
	pnt("2 - Budget")
	pnt("3 - Trade parameters")
	pnt("4 - Account")
	pnt("6 - Savings Allotments")
	pnt("5 - Exit")
	selection = getInput()
	if selection == "1":
		pnt("Exited mainMenu")
		indentNum -= 1
		return 1
	elif selection == "2":
		pnt("Exited mainMenu")
		indentNum -= 1
		return 2
	elif selection == "3":
		pnt("Exited mainMenu")
		indentNum -= 1
		return 3
	elif selection == "4":
		pnt("Exited mainMenu")
		indentNum -= 1
		return 4
	elif selection == "5":
		pnt("Exited mainMenu")
		indentNum -= 1
		return 5
	elif selection == "6":
		pnt("Exited mainMenu")
		indentNum -= 1
		return 6
	pnt("Exited mainMenu")
	indentNum -= 1
def setupStocks(errorCode):
	global indentNum
	global stockInfo
	indentNum += 1
	pnt("Entered setupStocks")

	selected = ""
	while True:
		slist = []
		for stock in stockInfo:
			slist.append(stock)
		pnt("Current stocks: " + str(slist))

		pnt("Type the ticker name of stock you would like to edit/add (e.g. NVDA)")
		pnt("Selected stock ->" + selected)
		pnt("1 - Remove selected")
		pnt("12 - Remove ALL stocks")
		try:
			pnt("2 - Toggle crypto " + str(stockInfo[selected]['isCrypto']))
			pnt("4 - Reset low confidence budget " + str(stockInfo[selected]['stockMoney']))
		except:
			pass
		pnt("@ - Exit")
		userInput = getInput()

		if userInput == "1":
			if selected == "":
				pnt("No stock selected")
				continue
			stockInfo.pop(selected)
			selected = ""

		elif userInput == "12":
			stockInfo.clear()

		elif userInput == "2":
			if selected == "":
				pnt("No stock selected")
				continue
			stockInfo[selected]['isCrypto'] = not stockInfo[selected]['isCrypto']

		elif userInput == "4":
			if selected == "":
				pnt("No stock selected")
				continue
			stockInfo[selected]['stockMoney'] = 0.0

		elif userInput == "@":
			if len(stockInfo) < 1:
				pnt("Gotta put Something in there, guy")
				continue
			pnt("Exited setupStocks")
			indentNum -= 1
			return 0
		elif userInput == "secret":
			global misc
			misc['devMode'] = True
			verifyDevMode()
			save()
			pnt("Exited setupStocks")
			indentNum -= 1
			return -1

		else:
			selected = userInput
			#check if already exists
			exists = False
			for stock in stockInfo:
				if stock == selected:
					exists = True
					pnt("Hey dumbass, this stock is already in the list")
			if not exists:
				pnt("Added " + selected)
				stockInfo[selected] = {}
				stockInfo[selected]['isCrypto'] = False
def setupTradeParams(errorCode):
	global indentNum
	global budget
	indentNum += 1
	pnt("Entered setupTradeParams")
	while True:
		pnt("Which parameter would you like to edit? See manual for more detailed information")
		pnt("PCBT - pcBottomThreshold " + str(tradeParams['pcBottomThreshold']))
		pnt("PCBN - pcBottomNum " + str(tradeParams['pcBottomNum']))
		pnt("PCBB - pcBottomBudget " + str(tradeParams['pcBottomBudget']))
		pnt("PCTT - pcTopThreshold " + str(tradeParams['pcTopThreshold']))
		pnt("PCTN - pcTopNum " + str(tradeParams['pcTopNum']))
		pnt("PCTB - pcTopBudget " + str(tradeParams['pcTopBudget']))
		pnt("EBT - equityBottomThreshold " + str(tradeParams['equityBottomThreshold']))
		pnt("EBN - equityBottomNum " + str(tradeParams['equityBottomNum']))
		pnt("EBB - equityBottomBudget " + str(tradeParams['equityBottomBudget']))
		pnt("AOT - ageOldestThreshold " + str(tradeParams['ageOldestThreshold']))
		pnt("AON - ageOldestNum " + str(tradeParams['ageOldestNum']))
		pnt("AOB - ageOldestBudget " + str(tradeParams['ageOldestBudget']))
		pnt("PTT - performanceAbsThreshold " + str(tradeParams['performanceAbsThreshold']))
		pnt("PTN - performanceTopNum " + str(tradeParams['performanceTopNum']))
		pnt("PTB - performanceTopBudget " + str(tradeParams['performanceTopBudget']))
		pnt("RN - randomNum " + str(tradeParams['randomNum']))
		pnt("RB - randomBudget " + str(tradeParams['randomBudget']))
		pnt("@ - Exit")

		userInput = getInput()
		match userInput:
			case "PCBT":
				tradeParams['pcBottomThreshold'] = float(getInput())
			case "PCBN":
				tradeParams['pcBottomNum'] = int(getInput())
			case "PCBB":
				tradeParams['pcBottomBudget'] = float(getInput())
			case "PCTT":
				tradeParams['pcTopThreshold'] = float(getInput())
			case "PCTN":
				tradeParams['pcTopNum'] = int(getInput())
			case "PCTB":
				tradeParams['pcTopBudget'] = float(getInput())
			case "EBT":
				tradeParams['equityBottomThreshold'] = float(getInput())
			case "EBN":
				tradeParams['equityBottomNum'] = int(getInput())
			case "EBB":
				tradeParams['equityBottomBudget'] = float(getInput())
			case "AOT":
				tradeParams['ageOldestThreshold'] = int(getInput())
			case "AON":
				tradeParams['ageOldestNum'] = int(getInput())
			case "AOB":
				tradeParams['ageOldestBudget'] = float(getInput())
			case "PTT":
				tradeParams['performanceAbsThreshold'] = float(getInput())
			case "PTN":
				tradeParams['performanceTopNum'] = int(getInput())
			case "PTB":
				tradeParams['performanceTopBudget'] = float(getInput())
			case "RN":
				tradeParams['randomNum'] = int(getInput())
			case "RB":
				tradeParams['randomBudget'] = float(getInput())

			case "@":
				pnt("Exited setupTradeParams")
				indentNum -= 1
				return 0
def setupAccount(errorCode):
	global indentNum
	global accountInfo
	indentNum += 1
	pnt("Entered setupAccount")
	selection = "0"
	while True:
		pnt("Account setup")
		pnt("1 - Username/Password")
		pnt("2 - Auto 2factor authentication: " + str(accountInfo['auto2factor']))
		pnt("@ - Exit")
		userInput = getInput()

		if userInput == "1":
			pnt("What is the email associated with your account?")
			accountInfo['username'] = getInput()
			pnt("What is the password associated with your account?")
			accountInfo['password'] = getInput()

		elif userInput == "2":
			pnt("Do you want to enable automatic 2 factor authentication?")
			pnt("NOTE: to use this feature, you will have to sign into your robinhood account and turn on two factor authentication. Robinhood will ask you which two factor authorization app you want to use. Select “other”. Robinhood will present you with an alphanumeric code.")
			pnt("y - Yes")
			pnt("n - No")
			userInput = getInput()
			if userInput == "y":
				accountInfo['auto2factor'] = True
				pnt("What is the code?")
				accountInfo['auto2FactorCode'] = getInput()
			elif selection == "n":
				pass

		elif userInput == "@":
			indentNum -= 1
			pnt("Exited setupAccount")
			if errorCode == 1:
				errorCode = 0
			return 0
def setupSavings(errorCode):
	global indentNum
	global savings
	indentNum += 1
	pnt("Entered setupSavings")

	selected = ""
	while True:
		pnt("Type the name of the account you would like to edit/add")
		pnt(str(savings))
		pnt("Selected -> ")
		try:
			pnt("1 - balance " + str(savings[selected]['balance']))
			pnt("2 - addMonthly " + str(savings[selected]['addMonthly']))
			pnt("3 - max " + str(savings[selected]['max']))
			pnt("4 - remove")
			pnt("5 - remove all")
		except:
			pass
		pnt("6 - Exit")
		userInput = getInput()
		if selected == "":
			selected = userInput
			savings[selected]['balance'] = 0
			savings[selected]['max'] = 50
			savings[selected]['addMonthly'] = 2
		if userInput == "1":
			pnt("What is the new balance?")
			savings[selected]['balance'] = int(getInput())
		elif userInput == "2":
			pnt("What is the new addMonthly?")
			savings[selected]['addMonthly'] = int(getInput())
		elif userInput == "3":
			pnt("What is the max balance?")
			savings[selected]['max'] = int(getInput())
		elif userInput == "4":
			savings.pop(selected)
			selected = ""
		elif userInput == "5":
			savings.clear()
		elif selection == "6":
			return 0
		else:
			selected = userInput
			try:
				var = savings[selected]['balance']
			except:
				savings[selected]['balance'] = 0
				savings[selected]['max'] = 50
				savings[selected]['addMonthly'] = 2
def setupHandler(errorCode):
	global indentNum
	indentNum += 1
	"""
	Error Codes
	0 - no error
	1 - load savedLogin.txt failed
	2 - load data.txt failed
	3 - load stockInfo failed
	5 - load tradeParams failed
	6 - invalid login
	"""
	pnt("Entered setup")
	pnt("errorCode " + str(errorCode))
	number = 0
	if errorCode == 1:
		number = setupAccount(errorCode)
	elif errorCode == 2:
		number = setupStocks(errorCode)
		if number == -1: #dev prefs selected
			pnt("Exited setup")
			indentNum -= 1
			return
		number = setupTradeParams(errorCode)
	elif errorCode == 3:
		number = setupStocks(errorCode)
	elif errorCode == 5:
		number = setupTradeParams(errorCode)
	elif errorCode == 6:
		number = setupAccount(errorCode)

	while True:
		#main menu
		if number == 0:
			number = setupMainMenu(errorCode)
		#stocks
		elif number == 1:
			number = setupStocks(errorCode)
		#budget
		elif number == 2:
			number = setupBudget(errorCode)
		#trade parameters
		elif number == 3:
			number = setupTradeParams(errorCode)
		#account
		elif number == 4:
			number = setupAccount(errorCode)
		#done
		elif number == 5:
			save()
			pnt("Exited setup")
			indentNum -= 1
			return
		#savings
		elif number == 6:
			number = setupSavings(errorCode)

#helper
def pnt(string): #prints to terminal and log file
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "log.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + (" " * indentNum*2) + str(string) + "\n")
	file.close()
	print(getTime() + (" " * indentNum*2) + str(string))
def updateStockInfo(): #puts new data in stockInfo
	global indentNum
	global stockInfo
	indentNum += 1
	pnt("Entered updateStockInfo")

	pnt("Getting prices...")
	wait(1)
	dictionary = rs.account.build_holdings(with_dividends=True)
	wait(1)
	cryptoDict = rs.crypto.get_crypto_positions()
	pnt("Got dictionary")
	order = 0
	for stock in stockInfo:
		pnt(stock)
		information = {
			"isCrypto": False,
			"price": 0.0,
			"lastPrice": 0.0,
			"equity": 0.0,
			"percentChange": 0.0,
			"daysSinceTrade": 0,
			"confidence": 0.1,
			"stockMoney": 0.0,
			"order": 0,
			"performance": [DEFAULT_PERFORMANCE] * misc['performanceDays'],
			"performanceNum": 0.0, #numerical value of performance combined
		}
		information['order'] = order
		try:
			information['isCrypto'] = stockInfo[stock]['isCrypto']
		except Exception as e:
			pnt("couldnt find isCrypto. assuming false")
			pnt(e)
			information['isCrypto'] = False

		if information['isCrypto']:
			wait(1)
			markPrice = rs.crypto.get_crypto_quote(stock)
			information['price'] = float(markPrice['mark_price'])
			for item in cryptoDict:
				if item['currency']['code'] == stock:
					information['equity'] = float(item['quantity']) * information['price']
		else:
			try:
				info = dictionary[stock]
				information['price'] = float(info['price'])
			except:
				pnt("couldnt get price")
				wait(1)
				information['price'] = float(rs.stocks.get_quotes([stock], 'last_trade_price')[0])
			try:
				info = dictionary[stock]
				information['equity'] = float(info['equity'])
			except:
				pnt("couldnt find equity for " + stock + " assuming 0")
				
		
		try:
			if not oneTime['forceTrade']:
				information['lastPrice'] = stockInfo[stock]['price']
		except:
			pnt("Last price not found for " + stock)
			information['lastPrice'] = information['price']

		try:
			information['percentChange'] = information['price'] / float(information['lastPrice'])
			if information['percentChange'] > 1.0:
				information['percentChange'] -= 1.0
				information['percentChange'] *= 100.0
			else:
				information['percentChange'] *= 100.0
				information['percentChange'] = 100.0 - information['percentChange']
				information['percentChange'] *= -1.0
			information['percentChange'] = float(format(information['percentChange'], '.3f'))
		except:
			information['percentChange'] = 0.0

		try:
			information['daysSinceTrade'] = stockInfo[stock]['daysSinceTrade']
		except:
			pnt("daysSinceTrade for " + stock + " does not exist. assuming 0")

		try:
			information['performance'] = loadList(information['performance'], stockInfo[stock]['performance'])
			if not oneTime['forceTrade']:
				information['performance'] = information['performance'][-1:] + information['performance'][:-1] #rotate
		except:
			pnt("performance not found for " + stock)

		try:
			information['performance'][0] = information['percentChange']
			information['performanceNum'] = 0
			for i in range(misc['performanceDays']):
				if information['performance'][i] == DEFAULT_PERFORMANCE:
					continue
				information['performanceNum'] += information['performance'][i]
			information['performanceNum'] = information['performanceNum']/misc['performanceDays'] #average
		except:
			information['performanceNum'] = 0.0
		
		try:
			if information['performanceNum'] > misc['performanceNormalThreshold']:
				information['confidence'] = 1
			elif information['performanceNum'] < misc['performanceLowConfidenceThreshold']:
				information['confidence'] = 0.1
			else:
				value = -information['performanceNum'] + abs(misc['performanceNormalThreshold'])
				value = 1/pow(2, value)
				information['confidence'] = value
		except:
			pnt("confidence not found for " + stock + ". Assuming 0.1")

		stockInfo[stock] = information
		order += 1
	pnt("Exited updateStockInfo")
	indentNum -= 1
def sortByParameter(param): #changes 'order' in stockInfo
	global indentNum
	global stockInfo
	indentNum += 1
	pnt("Entered sortByParameter")
	pnt("param " + param)

	try:
		lowestVal = 9999999.0
		higherVal = 9999999.0
		order = 1
		#find lowest value
		nextStock = ''
		for stock in stockInfo:
			if stockInfo[stock][param] < lowestVal:
				lowestVal = stockInfo[stock][param]
				nextStock = stock
			stockInfo[stock]['order'] = -1
		stockInfo[nextStock]['order'] = 0

		#work up from there
		counter = 0
		while True:
			counter += 1
			if counter > 1000:
				stop()
			if order > len(stockInfo)-1:
				break;
			for stock in stockInfo:
				if stockInfo[stock]['order'] == -1: #stock order not set
					if stockInfo[stock][param] >= lowestVal and stockInfo[stock][param] < higherVal:
						higherVal = stockInfo[stock][param]
						nextStock = stock
			lowestVal = higherVal
			higherVal = 9999999.0
			stockInfo[nextStock]['order'] = order
			order += 1
	except Exception as e:
		pnt("error")
		pnt("Exited sortByParameter")
		indentNum -= 1
		raise ValueError(e)
	pnt("Exited sortByParameter")
	indentNum -= 1
def wait(seconds):
	time.sleep(seconds)
def stop():
	pnt("Stop")
	while True:
		wait(60)
def getInput(): #returns user input
	return input("-->")
def getTime(): #returns date and time as string
	Anow = datetime.now()
	Aweekday = Anow.weekday()
	Ahour = Anow.hour
	Aminute = Anow.minute
	Aday = Anow.day
	Amonth = Anow.month
	Ayear = Anow.year
	printout = str(Amonth) + "/" + str(Aday) + "/" + str(Ayear) + "  "
	if Ahour < 10:
		printout += "0"
	printout += str(Ahour)
	if Aminute < 10:
		printout += "0"
	printout += str(Aminute)
	return printout

#onstart
@timeoutable() #specifies function to be able to time out
def onstart():
	if hour == TRADE_HOUR:
		try:
			scriptDir = os.path.dirname(__file__)
			open(os.path.join(scriptDir, "log.txt"), "w").close() #clear contents of file
		except:
			pass
	pnt("Program start")
	value = ""
	try:
		value = sys.argv[1]
	except:
		pnt("No input arg")
	if value == "setup":
		pnt("Setup is input arg")
		startup(1)
	elif value == "test":
		pnt("Test is input arg")
		startup(2)
	elif value == 'reset':
		pnt("Reset is input arg")
		startup(3)
	elif value == 'trade':
		pnt("Trade is input arg")
		startup(4)
	elif value == 'getprices':
		pnt("getprices is input arg")
		startup(5)
	else:
		pnt("Normal startup")
		startup(0)
	save()
	logout()
	pnt("Program end")
if __name__ == "__main__":
	result = onstart(timeout=30*60) #30 minutes timeout in seconds
	if result != "None":
		pnt("Timed out. Shutting down")
	else:
		pnt("Shut down correctly")
		pnt("")
		pnt("")