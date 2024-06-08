# Changelog 0.7
"""
cleaner code
lots of other new shit i forgor to document
"""
#recommended cron timing below. Program is able to handle other cron timings, buy why would you change it? There's no need for it
#5 12,16 * * *
#full command to be pasted into cron
#5 12,16 * * * bash -c "source /home/myVenv/bin/activate && /home/myVenv/bin/python3 /home/AUTOTRAYDR.py"

import robin_stocks.robinhood as rs #i forgor what this one does :(
import sys #save terminal to txt
import json #save file
import time #time.sleep reduces CPU usage by waiting N seconds
import os #gets relative filepath
import pyotp #auto 2factor if you choose
from stopit import threading_timeoutable as timeoutable #prevents program from running FOREVER
from datetime import datetime #get time

stockList = ['AMCX', 'AMD', 'AMZN', 'ARM', 'AVGO', #developer stocklist teehee
			'CATX', 'CIFR', 'CLSD', 'CLSK', 'COST', 'CRWD', 
			'DELL', 'DJT', 'DTST', 
			'GME', 'GE', 'GLD', 'GOOGL',  
			'LLY', 'LMT', 'LRCX', 
			'META', 'MSFT', 'MSTR', 'MU', 
			'NFLX', 'NKTX', 'NVDA', 
			'PAA', 
			'QCOM', 
			'SLV', 'SMCI', 
			'TM', 'TSLA', 'TSM', 
			'V', 'VINC', 
			'XOM',
			'ZJYL']
cryptoList = ['AVAX', 'BTC', 'DOGE', 'ETH', 'SHIB', 'UNI']
skipSetup = False #overrides setup if dev prefs were loaded
TRADE_PARAM_DISABLED = 7050
numAllCompanies = 35
indentNum = 1
defconLevel = 0
"""
DEFCON levels
0 - Program will execute trades and perform as designed
1 - Program will NOT execute trades, but it will do everything else
2 - Program pretends to do everything. Values don't get changed
"""

#Saved data
VERSION_NUMBER = 0.6
stockInfo = {}
lcAmount = 0.0
budget = {
	"brokerage": 0.0, #actual value of brokerage
	"dailyBudgetPerStock": 0.0,
	"dailyBudgetTotal": 0.0,
	"weeklyBudgetPerStock": 0.0,
	"weeklyBudgetTotal": 0.0,
	"monthlyBudgetTotal": 0.0,
}
tradeParams = {}
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
	"username": "",
	"password": "",
	"auto2factor": False,
	"auto2FactorCode": "",
}
#/Saved data
"""
#TODO stock info pnt in placeOrder should be formatted. too many decimals
#TODO encrypt passswords
WIP trade fail
"""

#startup/shutdown
def splash():
	global indentNum
	indentNum += 1
	pntDev("Entered splash")
	financesSplash()
	pnt("Sorted by percent change")
	pnt("Buy bottom " + str(tradeParams['pcBottomNum']) + " stocks, $" + str(tradeParams['pcBottomBudget']) + " each. Only if stock's percent change is less than -" + str(tradeParams['pcBottomThreshold']) + "%")
	pnt("Buy top " + str(tradeParams['pcTopNum']) + " stocks, $" + str(tradeParams['pcTopBudget']) + " each")
	pnt("Sell $" + str(tradeParams['pcTopSellBudget']) + " of each stock when percent change is greater than +" + str(tradeParams['pcTopSellThresh']) + "%")
	pnt("Sorted by equity")
	pnt("Buy bottom " + str(tradeParams['equityBottomNum']) + " stocks, $" + str(tradeParams['equityBottomBudget']) + " each")
	pnt("Sorted by last bought")
	pnt("Buy " + str(tradeParams['ageOldestNum']) + " stocks (When older than " + str(tradeParams['ageOldestThreshold']) + " days), $" + str(tradeParams['ageOldestBudget']) + " each")
	maxBudget = ((tradeParams['pcBottomNum']*tradeParams['pcBottomBudget'])
		+(tradeParams['pcTopNum']*tradeParams['pcTopBudget'])
		+(tradeParams['equityBottomNum']*tradeParams['equityBottomBudget'])
		+(tradeParams['ageOldestNum']*tradeParams['ageOldestBudget'])
	)
	remainingFunds = float(format(budget['dailyBudgetTotal']-maxBudget, '.3f'))
	pnt("Daily remaining funds: $" + str(remainingFunds) + " (You should have around a dollar's worth of margin here. Do NOT try to optimize this below $0.10)")
	if remainingFunds < 0.0:
		pnt("Buy orders exceed daily budget. Buy less shit, or work harder")
	pntDev("Exited splash")
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
	"""
	pntDev("Entered startup")
	pntDev("Startup condition " + str(condition))
	number = 0
	whileNum = 0
	while True:
		number += 1
		if number >= 4:
			stop()
		if whileNum >= 4:
			stop()
		try:
			load() #calls setup if error
			if condition == 1 and not skipSetup:
				setup(0)
			login()
			break
		except:
			pntDev("Error in startup loop")
			whileNum += 1

	if condition == 0 or condition == 1:
		oneTime['forceReset'] = False
		oneTime['forceTrade'] = False
		mainLoop()
	elif condition == 2:
		pntDev("Program disarmed")
		tempArmed = defconLevel
		defconLevel = 2
		pnt("Testing weekend...")
		pntDev("Testing weekend...")
		oneTime['testWeekend'] = True
		oneTime['testTrade'] = False
		oneTime['testReset'] = False
		mainLoop()
		login()
		pnt("Testing trade...")
		pntDev("Testing trade...")
		oneTime['testWeekend'] = False
		oneTime['testTrade'] = True
		oneTime['testReset'] = False
		mainLoop()
		login()
		pnt("Testing reset...")
		pntDev("Testing reset...")
		oneTime['testWeekend'] = False
		oneTime['testTrade'] = False
		oneTime['testReset'] = True
		mainLoop()
		oneTime['testReset'] = False
		pnt("Testing complete")
		pntDev("Testing complete")
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
	pntDev("Exited startup")
	indentNum -= 1
def login(): #calls setup if error
	global indentNum
	global accountInfo
	indentNum += 1
	pntDev("Entered login")
	pnt("Logging in...")
	try:
		wait(1)
		if accountInfo['auto2factor']:
			totp = pyotp.TOTP(accountInfo['auto2FactorCode']).now()
			login = rs.login(accountInfo['username'], accountInfo['password'], mfa_code=totp)
		else: #no 2factor bypass
			login = rs.login(accountInfo['username'], accountInfo['password'])

		pntDev("Login successful")
		pnt("Welcome, " + str(accountInfo['username']))
		pntDev("Exited login")
		indentNum -= 1
	except Exception as e:
		print(e)
		pntDev("Error logging in. Invalid accountInfo")
		pnt("ERROR-INVALIDLOGIN")
		pnt("Error logging in. Check spelling of your username and password")
		pnt("User- " + accountInfo['username'])
		pnt("Pass- " + accountInfo['password'])
		setup(1)
		pntDev("Exited login")
		indentNum -= 1
		raise ValueError("Error logging in. Check spelling of your username and password")
def logout():
	global indentNum
	indentNum += 1
	pntDev("Entered logout")
	pnt("Logging out...")
	wait(1)
	rs.logout()
	pntDev("Exited logout")
	indentNum -= 1

#main
def mainLoop():
	global indentNum
	global budget
	global oneTime
	indentNum += 1
	pntDev("Entered mainLoop")
	
	now = datetime.now()
	weekday = now.weekday()
	hour = now.hour
	minute = now.minute
	day = now.day
	month = now.month
	year = now.year

	isweekend = weekday > 4 and not oneTime['weekendCheck'] #skip weekends
	if oneTime['forceWeekend'] or isweekend or oneTime['testWeekend']:
		pnt("Weekend")
		pntDev("Weekend")
		if defconLevel != 2:
			oneTime['weekendCheck'] = True

	istrade = weekday <= 4 and hour == 12 and not oneTime['tradeCheck'] #trade on weekday at noon
	if oneTime['forceTrade'] or istrade or oneTime['testTrade']:
		getStockPrices()
		save()
		trade()
		if defconLevel != 2:
			oneTime['tradeCheck'] = True
			oneTime['resetCheck'] = False

	isreset = hour == 16 and weekday <= 4 and not oneTime['resetCheck'] #reset at 1600 on weekdays
	if oneTime['forceReset'] or isreset or oneTime['testReset']:
		reset()
		if defconLevel != 2:
			oneTime['resetCheck'] = True #reset on trade day

	pntDev("Exited mainLoop")
	indentNum -= 1
def tradeParameter(stocksBought, num, shoppingCart, condition, isBottom):
	global indentNum
	global stockInfo
	indentNum += 1
	pntDev("Entered tradeParameter")
	pntDev("Condition " + str(condition))
	"""
	Condition: unique code to be run for
	0 = buy bottom equity
	1 = buy oldest
	2 = buy bottom pc
	3 = buy top pc
	4 = sell top pc w/ only threshold
	"""

	if num == TRADE_PARAM_DISABLED:
		pntDev("Exited tradeParameter")
		indentNum -= 1
		return

	newShoppingCart = shoppingCart
	localBought = []
	bottomNum = num
	topNum = numAllCompanies - num
	isBreak = False
	while not isBreak:
		if topNum > numAllCompanies or bottomNum > numAllCompanies:
			pntDev("Made it to the bottom of the list. no more companies qualify for this parameter")
			break
		for stock in stockInfo:
			if len(localBought) >= num:
				if not isBreak:
					pntDev("Bought enough stocks")
				isBreak = True
				break
			if condition == 1:
				if stockInfo[stock]['daysSinceTrade'] < tradeParams['ageOldestThreshold']:
					bottomNum += 1
					topNum += 1
					pntDev("Not old enough " + stock)
					continue
			elif condition == 2:
				if stockInfo[stock]['percentChange'] > tradeParams['pcBottomThreshold']:
					bottomNum += 1
					topNum += 1
					pntDev("PC not below threshold " + stock)
					continue
				if stockInfo[stock]['percentChange'] < -10.0:
					newShoppingCart += 10
				elif stockInfo[stock]['percentChange'] < -8.0: 
					newShoppingCart += 8
				elif stockInfo[stock]['percentChange'] < -5.0:
					newShoppingCart += 5
				elif stockInfo[stock]['percentChange'] < -3.0: 
					newShoppingCart += 2

			alreadyBought = False
			for stockb in localBought:
				if stockb == stock:
					pntDev("Already bought " + stock)
					alreadyBought = True
			if alreadyBought:
				continue
			if stockInfo[stock]['order'] < 0: #ignore LC
				pntDev(stock + " is LC")
				continue
			if stockInfo[stock]['order'] > bottomNum and isBottom: #stay within bounds
				continue
			if stockInfo[stock]['order'] < topNum and not isBottom:
				continue

			pntDev(stock + " candidate for trade")

			if budget['moneyLeftDaily'] >= budget['weeklyBudgetTotal']: #buy more if idle money
				newShoppingCart += budget['moneyLeftDaily'] * 0.01
				pntDev("Added $" + str(budget['moneyLeftDaily'] * 0.01) + " to shopping cart because of excess money")

			if checkOrderValid(stock, newShoppingCart, True):
				number = 0
				while number != 3:
					if placeOrder(stock, newShoppingCart, True):
						pntDev("Success")
						stocksBought.append(stock)
						localBought.append(stock)
						break
					else:
						number += 1
						#getStockPrices() may be unneccessary
						pntDev("Retrying " + str(number))
				if number == 3:
					pntDev("Timed out. Adding stock to bought list to prevent infinite loop")
					stocksBought.append(stock)
					localBought.append(stock)
			else:
				pntDev("Invalid order")
				isBreak = True

	pntDev("Exited tradeParameter")
	indentNum -= 1
	return stocksBought
def trade():
	global indentNum
	global stockInfo
	global budget
	global tradeParams
	indentNum += 1
	pntDev("Entered trade")

	stocksBought = [] #ensures N number of stocks are bought

	#buy bottom equity
	sortByParameter('equity')
	pntDev("buy bottom equity")
	stocksBought = tradeParameter(
		stocksBought, 
		tradeParams['equityBottomNum'], 
		tradeParams['equityBottomBudget'], 
		0,
		True,
	)

	#buy oldest
	sortByParameter('daysSinceTrade')
	pntDev("buy oldest")
	stocksBought = tradeParameter(
		stocksBought, 
		tradeParams['ageOldestNum'], 
		tradeParams['ageOldestBudget'], 
		1, 
		True,
	)
	"""
	#sell top pc threshold
	sortByParameter('percentChange')
	pntDev("sell top pc threshold")
	if tradeParams['pcTopSellThresh'] != TRADE_PARAM_DISABLED:
		for stock in stockInfo:
			if stockInfo[stock]['percentChange'] >= tradeParams['pcTopSellThresh']:
				if checkOrderValid(stock, tradeParams['pcTopSellBudget'], False):
					placeOrder(stock, tradeParams['pcTopSellBudget'], False)
	"""
	#buy bottom pc
	pntDev("buy bottom pc")
	stocksBought = tradeParameter(
		stocksBought, 
		tradeParams['pcBottomNum'], 
		tradeParams['pcBottomBudget'], 
		2, 
		True, 
	)

	#buy top pc
	pntDev("buy top pc")
	stocksBought = tradeParameter(
		stocksBought, 
		tradeParams['pcTopNum'], 
		tradeParams['pcTopBudget'], 
		3, 
		False,
	)

	#low confidence
	pntDev("lc")
	for stock in stockInfo:
		if stockInfo[stock]['order'] != -50: #skip normal stocks
			continue
		if stockInfo[stock]['lcAmount'] >= 1.0:
			pntDev(stock + " lcAmount >= $1.00")
			if checkOrderValid(stock, 1.0, True):
				placeOrder(stock, 1.0, True)
		else:
			pntDev(stock + " lcAmount = $" + str(stockInfo[stock]['lcAmount']))
	pntDev("No more lc stocks to buy")

	pntDev("Exited trade")
	indentNum -= 1
def reset():
	global indentNum
	global budget
	global stockInfo
	global oneTime
	indentNum += 1
	pntDev("Entered reset")
	
	pntDev("Resetting oneTime...")
	oneTime['testWeekend'] = False
	oneTime['testTrade'] = False
	oneTime['testReset'] = False
	oneTime['forceWeekend'] = False
	oneTime['forceTrade'] = False
	oneTime['forceReset'] = False
	oneTime['weekendCheck'] = False
	oneTime['tradeCheck'] = False
	pntDev("Reset oneTime")

	pntDev("Verifying integrity of stockInfo")
	for stock in stockInfo:
		try:
			value = stockInfo[stock]['daysSinceTrade']
			valuea = stockInfo[stock]['lowConfidence']
			valueb = stockInfo[stock]['lcBudget']
		except:
			pntDev(stock + " missing data")
			getStockPrices()
	pntDev("Verified integrity of stockInfo")
	
	pntDev("Incrementing daysSinceTrade...")
	if defconLevel != 2:
		for stock in stockInfo:
			stockInfo[stock]['daysSinceTrade'] += 1
	else:		
		pntDev("daysSinceTrade not incremented")
	pntDev("Incremented daysSinceTrade")

	pntDev("Getting brokerage balance...")
	wait(1)
	userProf = rs.account.build_user_profile()
	budget['moneyLeftDaily'] = 0.0
	budget['brokerage'] = float(userProf['cash'])
	budget["moneyLeftTotal"] = float(userProf['cash'])
	pntDev("Got brokerage balance")

	pntDev("Filling LC stocks...")
	for stock in stockInfo:
		if not stockInfo[stock]['lowConfidence']:
			continue
		if budget['moneyLeftTotal'] > lcAmount:
			pntDev("Tried to allocate " + str(lcAmount) + " to LC stock")
			continue
		if defconLevel != 2:
			if budget['moneyLeftTotal'] > stockInfo[stock]['lcBudget'] + lcAmount:
				stockInfo[stock]['lcBudget'] += lcAmount
				budget['moneyLeftTotal'] -= stockInfo[stock]['lcBudget']
			else:
				pntDev("Tried to allocate money to lc stock with insufficient funds")
		else:
			pntDev("Not filled")
	pntDev("Filled LC stocks")

	pntDev("Filling moneyLeftDaily with excess...")
	if budget['moneyLeftTotal'] > budget['monthlyBudgetTotal']:
		pntDev("Added difference of (moneyLeftTotal-monthlyBudgetTotal) to moneyLeftDaily because of excess money")
		if defconLevel != 2:
			value = budget['moneyLeftTotal'] - budget['monthlyBudgetTotal']
			budget['moneyLeftDaily'] += value
			budget['moneyLeftTotal'] -= value
		else:
			pntDev("I lied")
	else:
		pntDev("No excess")
	pntDev("Filled moneyLeftDaily with excess")

	pntDev("Filling moneyLeftDaily with normal amount")
	if budget['moneyLeftTotal'] > budget['dailyBudgetTotal']:
		if defconLevel != 2:
			pntDev("moneyLeftDaily refilled with " + str(budget['dailyBudgetTotal']))
			pntDev("moneyLeftTotal refilled with " + str(budget['dailyBudgetTotal']))
			budget['moneyLeftDaily'] += budget['dailyBudgetTotal']
			budget['moneyLeftTotal'] -= budget['dailyBudgetTotal']
		else:
			pntDev("moneyLeftDaily refilled with " + str(budget['dailyBudgetTotal']) + " but not really")
			pntDev("moneyLeftTotal refilled with " + str(budget['dailyBudgetTotal']) + " but not really")
	else:
		pnt("Program tried to add $" + str(budget['dailyBudgetTotal']) + " to daily budget with $" + str(budget['moneyLeftTotal']) + " left")
	pntDev("Filled moneyLeftDaily with normal amount")

	pntDev("Exited reset")
	indentNum -= 1
		
#save/load
def save():
	global indentNum
	global stockInfo
	global budget
	global tradeParams
	global oneTime
	indentNum += 1
	pntDev("Entered save")

	pnt("Saving...")
	scriptDir = os.path.dirname(__file__)
	absFilePath = os.path.join(scriptDir, "savedLogin.txt")
	with open(absFilePath, "w") as fp:
		json.dump(accountInfo, fp)
		pntDev("Saved savedLogin.txt")

	jsonData = {
		'VERSION_NUMBER': VERSION_NUMBER,
		'stockInfo': stockInfo,
		'budget': budget,
		'tradeParams': tradeParams,
		'oneTime': oneTime,
	}
	with open(os.path.join(scriptDir, "data.txt"), "w") as fp:
		json.dump(jsonData, fp)
		pntDev("Saved data.txt")
	pntDev("Exited save")
	indentNum -= 1
def load(): #calls setup and returns if error
	global indentNum
	global accountInfo
	global stockInfo
	global oneTime
	global budget
	global tradeParams
	global numAllCompanies
	indentNum += 1
	pntDev("Entered load")

	try:
		scriptDir = os.path.dirname(__file__)
		relPath = "savedLogin.txt"
		absFilePath = os.path.join(scriptDir, relPath)
		with open(absFilePath, "r") as fp:
			accountInfo = json.load(fp)
			pntDev("Loaded savedLogin.txt")
	except:
		pnt("Failed to load savedLogin.txt. Either file doesn't exist, or incorrect user/pass")
		setup(1)
		pntDev("Exited load with savedLogin.txt error")
		indentNum -= 1
		raise ValueError("Failed to load savedLogin.txt. Either file doesn't exist, or incorrect user/pass")

	try:
		jsonData = {}
		scriptDir = os.path.dirname(__file__)
		with open(os.path.join(scriptDir, "data.txt"), "r") as fp:
			jsonData = json.load(fp)
			pntDev("Loaded data.txt")
	except:
		pnt("Failed to load data.txt")
		setup(2)
		pntDev("Exited load with data.txt error")
		indentNum -= 1
		raise ValueError("Failed to load data.txt")

	if VERSION_NUMBER != jsonData['VERSION_NUMBER']:
		pnt("Saved data from v" + str(jsonData['VERSION_NUMBER']) + "Current: v" + str(VERSION_NUMBER))
		upgradeFiles()

	try:
		stockInfo = jsonData['stockInfo']
	except:
		pntDev("Error loading stockInfo. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		budget = jsonData['budget']
	except:
		pntDev("Error loading budget. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		tradeParams = jsonData['tradeParams']
	except:
		pntDev("Error loading tradeParams. Recommend deleting data.txt and re-running program manually")
		stop()
	try:
		oneTime = jsonData['oneTime']
	except:
		pntDev("Error loading oneTime. Recommend deleting data.txt and re-running program manually")
		stop()
	
	numAllCompanies = len(stockInfo)
	
	pntDev("Exited load")
	indentNum -= 1

#setup
def propagateDevPrefs():
	global indentNum
	global stockInfo
	global budget
	global tradeParams
	global skipSetup
	indentNum += 1
	pntDev("Entered propagateDevPrefs")

	pntDev("Developer prefs loading...")
	pnt("Good morning, petty officer")

	pntDev("Loading stocks")
	stockInfo = {}
	for stock in stockList:
		stockInfo[stock] = {}
		stockInfo[stock]['isCrypto'] = False
	for crypto in cryptoList:
		stockInfo[crypto] = {}
		stockInfo[crypto]['isCrypto'] = True
		
	stockInfo['AMCX']['lowConfidence'] = True
	stockInfo['GME']['lowConfidence'] = True
	pntDev("Loaded stocks")

	pntDev("Setting budget")
	budget['monthlyBudgetTotal'] = 525.0
	budget['weeklyBudgetTotal'] = 0.0
	budget['dailyBudgetTotal'] = 0.0
	budget['dailyBudgetPerStock'] = 0.0
	budget['weeklyBudgetPerStock'] = 0.0
	try:
		value = budget['moneyLeftDaily']
		value = budget['moneyLeftTotal']
	except:
		budget['moneyLeftDaily'] = 0.0
		budget['moneyLeftTotal'] = 0.0
	budget = calculateBudget(budget)
	financesSplash()
	pntDev("Set budget")

	pntDev("Loading trade params")
	tradeParams = {}
	tradeParams['pcBottomThreshold'] = -0.5
	tradeParams['pcBottomNum'] = 4
	tradeParams['pcBottomBudget'] = 1.0
	tradeParams['pcTopNum'] = 3
	tradeParams['pcTopBudget'] = 1.0
	tradeParams['equityBottomNum'] = 5
	tradeParams['equityBottomBudget'] = 1.0
	tradeParams['ageOldestNum'] = 3
	tradeParams['ageOldestThreshold'] = 7
	tradeParams['ageOldestBudget'] = 1.0
	tradeParams['pcTopSellThresh'] = 4.5
	tradeParams['pcTopSellBudget'] = 1.0
	pntDev("Loaded trade params")

	calculateRemainingBudget()
	skipSetup = True
	pntDev("Exited propagateDevPrefs")
	indentNum -= 1
	return 5 #exit
def setupMainMenu(errorCode):
	global indentNum
	indentNum += 1
	pntDev("Entered mainMenu")
	if errorCode != 0:
		pntDev("Error code " + str(errorCode))
	if errorCode == 1:
		pntDev("Exited mainMenu")
		indentNum -= 1
		return 4 #go to account


	pnt("What would you like to edit?")
	pnt("1 - Stocks/Crypto")
	pnt("2 - Budget")
	pnt("3 - Trade parameters")
	pnt("4 - Account")
	pnt("5 - Exit")
	selection = getInput()
	if selection == "1":
		pntDev("Exited mainMenu")
		indentNum -= 1
		return 1
	elif selection == "2":
		pntDev("Exited mainMenu")
		indentNum -= 1
		return 2
	elif selection == "3":
		pntDev("Exited mainMenu")
		indentNum -= 1
		return 3
	elif selection == "4":
		pntDev("Exited mainMenu")
		indentNum -= 1
		return 4
	elif selection == "5":
		pntDev("Exited mainMenu")
		indentNum -= 1
		return 5
	elif selection == "secret":
		pntDev("Exited mainMenu")
		indentNum -= 1
		return propagateDevPrefs()
	pntDev("Exited mainMenu")
	indentNum -= 1
def setupStocks(errorCode):
	global indentNum
	global stockInfo
	global numAllCompanies
	indentNum += 1
	pntDev("Entered setupStocks")
	pnt("What stocks do you want to invest in?")
	pnt("Type the ticker name for each stock one at a time. (Eg: NVDA)")
	pnt("0 - Finished")
	pnt("1 - Change between inputting stocks, and cryptocurrencies")
	pnt("2 - Remove the last stock")
	pnt("3 - Remove all stocks")
	pnt("4 - Edit low confidence budget")
	if errorCode != 2 and errorCode != 3:
		pnt("99 - Return to main manu")

	if len(stockInfo) > 0:
		pnt("Current stocks:")
		for stock in stockInfo:
			if stockInfo[stock]['lowConfidence']:
				pnt(stock + " Lc")
			else:
				pnt(stock)

	inputStocks = True
	while True:
		pntDev("Restarted stock input while True loop")
		if inputStocks:
			pnt("Accepting stocks. Do NOT input crypto")
		else:
			pnt("Accepting cryptocurrencies. Do NOT input stocks")
		selection = getInput()
		if selection == "1":
			pntDev("Swapped between crypto/stocks")
			inputStocks = not inputStocks
		elif selection == "2":
			pntDev("Stock removed")
			stockInfo.popitem()
			pnt("\nStocks")
			pntDev("Exited setupStocks")
			indentNum -= 1
			return 1 #restart
		elif selection == "3":
			pntDev("All stocks removed")
			stockInfo.clear()
			pntDev("Exited setupStocks")
			indentNum -= 1
			return 1
		elif selection == "4":
			pntDev("Editing low confidence mode")
			pnt("Low confidence mode keeps a budget for each stock with this enabled")
			try:
				pnt("Every weekday, it will add $" + str(lcAmount) + " to the budgets of each stock. This should be <$0.15")
			except:
				pnt("Every weekday, it will add $X.XX to the budgets of each stock. This should be <$0.15")
			pnt("When a stock's budget exceeds $1.00, it will place a buy order")
			pnt("What will the budget for each stock daily be?")
			lcAmount = getInput()

		elif selection == "0":
			if len(stockInfo) > 0:
				pntDev("Broke stock input while True loop 2")
				break
			else:
				pnt("Add a stock first, guy")
		elif selection == "99":
			try:
				value = lcAmount
			except:
				lcAmount = 0.05

			if len(stockInfo) > 0:
				if errorCode == 2 or errorCode == 3:
					pnt("You can't exit to the main menu. data.txt couldn't be loaded, so repopulate the shit")
				pntDev("Exited setupStocks")
				indentNum -= 1
				return 0
			else:
				pnt("Add a stock first, guy")
		elif selection == "secret":
			numbera = propagateDevPrefs()
			save()

			pntDev("Exited setupStocks")
			indentNum -= 1
			return -1
		else:
			stockInfo[selection] = {}
			if inputStocks:
				pntDev("Stock " + selection + " added")
				stockInfo[selection]['isCrypto'] = False
			else:
				pntDev("Crypto " + selection + " added")
				stockInfo[selection]['isCrypto'] = True

			pnt("Do you have low confidence in this stock?")
			pnt("LC mode keeps a virtual budget for each LC stock. It adds $0.XX to each stock's budget daily, then buys when it exceeds $1.00")
			pnt("This should be used for a stock that is not expected to perform well")
			if getInput() == "y":
				pnt("Low confidence enabled for " + selection)
				stockInfo[selection]['lowConfidence'] = True
			else:
				pnt("Low confidence disabled for " + selection)
				stockInfo[selection]['lowConfidence'] = False
	numAllCompanies = len(stockInfo)
	pntDev("Exited setupStocks")
	indentNum -= 1
	return 0
def setupBudget(errorCode):
	global indentNum
	global budget
	indentNum += 1
	pntDev("Entered setupBudget")

	while True:
		pnt("How would you like to define a budget?")
		pnt("1 - Monthly total")
		pnt("2 - Weekly total")
		pnt("3 - Daily total")
		pnt("4 - Weekly per stock")
		pnt("5 - Daily per stock")
		pnt("6 - Skip to funds remaining")
		if errorCode != 4:
			pnt("99 - Return to main menu")
		selection = getInput()

		if selection == "99":
			if errorCode == 4:
				pnt("Fuck off. I got an error loading the fucking budget, so put your data in again and stop complaining")
			else:
				pntDev("Exited setupBudget")
				indentNum -= 1
				return 0
		if selection != "6" and selection != "99":
			pnt("Reset budget values")
			pntDev("Reset budget values")
			budget['monthlyBudgetTotal'] = 0.0
			budget['weeklyBudgetTotal'] = 0.0
			budget['dailyBudgetTotal'] = 0.0
			budget['dailyBudgetPerStock'] = 0.0
			budget['weeklyBudgetPerStock'] = 0.0
			try:
				value = budget['moneyLeftDaily']
				value = budget['moneyLeftTotal']
			except:
				pnt("Reset moneyLeftDaily and moneyLeftTotal")
				pntDev("Reset moneyLeftDaily and moneyLeftTotal")
				budget['moneyLeftDaily'] = 0.0
				budget['moneyLeftTotal'] = 0.0
			pnt("With how much money?")
		if selection == "1":
			pnt("Editing monthlyBudgetTotal")
			budget['monthlyBudgetTotal'] = float(getInput())
		elif selection == "2":
			pnt("Editing weeklyBudgetTotal")
			budget['weeklyBudgetTotal'] = float(getInput())
		elif selection == "3":
			pnt("Editing dailyBudgetTotal")
			budget['dailyBudgetTotal'] = float(getInput())
		elif selection == "4":
			pnt("Editing weeklyBudgetPerStock")
			budget['weeklyBudgetPerStock'] = float(getInput())
		elif selection == "5":
			pnt("Editing dailyBudgetPerStock")
			budget['dailyBudgetPerStock'] = float(getInput())
		elif selection == "6":
			pntDev("Editing moneyLeftTotal")
			pnt("How much money is currently in your Robinhood brokerage? (This money must not go down except by action of this program, otherwise it will attempt to spend money that doesn't exist)")
			pnt("This program assumes deposits are made on the 1st of the month. If you don't want to wait until then, fill this out. Otherwise, put 0")
			
			budget['moneyLeftTotal'] = float(getInput())
			pntDev("Reset moneyLeftDaily")
			pnt("Reset balance for tomorrow")
			budget['moneyLeftDaily'] = 0.0
			
			pnt("Keep in mind, this program does not include weekends, so these values may be lower than expected")
			budget = calculateBudget(budget)
			financesSplash()
		elif selection == "99":
			budget = calculateBudget(budget)
			if errorCode == 4:
				pntDev("Exited setupBudget")
				indentNum -= 1
				return 5
			else:
				pntDev("Exited setupBudget")
				indentNum -= 1
				return 0
		else:
			pntDev("Invalid input, dumbass")	
def setupTradeParams(errorCode):
	global indentNum
	global budget
	indentNum += 1
	pntDev("Entered tradeParams")
	
	monthlyRemaining = budget['monthlyBudgetTotal']
	weeklyRemaining = budget['weeklyBudgetTotal']
	dailyRemaining = budget['dailyBudgetTotal']
	while True:
		pnt("Which trade parameter do you want to edit?")
		pnt("To disable a trade parameter, set ALL of its associated values to " + str(TRADE_PARAM_DISABLED))
		if errorCode == 0:
			pnt("Sorted by percent change:")
			pnt("1 - Buy greatest NEGATIVE percent change: " + str(tradeParams['pcBottomNum']) + "/$" + str(tradeParams['pcBottomBudget']) + ", " + str(tradeParams['pcBottomThreshold']) + "% Threshold")
			pnt("2 - Buy greatest POSITIVE percent change: " + str(tradeParams['pcTopNum']) + "/$" + str(tradeParams['pcTopBudget']))
			pnt("3 - Sell N dollars at positive percent change threshold: $" + str(tradeParams['pcTopSellBudget']) + ", " + str(tradeParams['pcTopSellThresh']) + "% Threshold")
			pnt("Sorted by equity:")
			pnt("4 - Buy lowest equity: " + str(tradeParams['equityBottomNum']) + "/$" + str(tradeParams['equityBottomBudget']))
			pnt("Sorted by age:")
			pnt("5 - Buy most stale: " + str(tradeParams['ageOldestNum']) + "/$" + str(tradeParams['ageOldestBudget']) + ", When older than " + str(tradeParams['ageOldestThreshold']) + " days")
		else:
			pnt("Sorted by percent change:")
			pnt("1 - Buy greatest NEGATIVE percent change")
			pnt("2 - Buy greatest POSITIVE percent change")
			pnt("3 - Sell N dollars at positive percent change threshold")
			pnt("Sorted by equity:")
			pnt("4 - Buy lowest equity")
			pnt("Sorted by age:")
			pnt("5 - Buy most stale (Bought greater than N days ago)")
		if errorCode == 5:
			pnt("99 - Finished")
			pnt("All trade parameters are disabled")
			tradeParams['pcBottomNum'] = 0
			tradeParams['pcBottomBudget'] = 0.0
			tradeParams['pcBottomThreshold'] = 0.0
			tradeParams['pcTopNum'] = 0
			tradeParams['pcTopBudget'] = 0.0
			tradeParams['pcTopSellThresh'] = 0.0
			tradeParams['pcTopSellBudget'] = 0.0
			tradeParams['equityBottomNum'] = 0
			tradeParams['equityBottomBudget'] = 0.0
			tradeParams['ageOldestNum'] = 0
			tradeParams['ageOldestBudget'] = 0.0
			tradeParams['ageOldestThreshold'] = 0.0
		else:
			pnt("99 - Return to main menu")
		selection = getInput()
		if selection == "99":
			pntDev("Editing 99")
			#error checking
			allVals = 0
			value = 0
			if tradeParams['pcBottomNum'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['pcBottomBudget'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['pcBottomThreshold'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 3:
				pnt("Hey guy, not all values associated with 'Buy greatest NEGATIVE percent change' are enabled/disabled")
				continue
			value = 0
			if tradeParams['pcTopNum'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['pcTopBudget'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 2:
				pnt("Hey guy, not all values associated with 'Buy greatest POSITIVE percent change' are enabled/disabled")
				continue
			value = 0
			if tradeParams['pcTopSellThresh'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['pcTopSellBudget'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 2:
				pnt("Hey guy, not all values associated with 'Sell N dollars at positive percent change threshold' are enabled/disabled")
				continue
			value = 0
			if tradeParams['equityBottomNum'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['equityBottomBudget'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 2:
				pnt("Hey guy, not all values associated with 'Buy lowest equity' are enabled/disabled")
				continue
			value = 0
			if tradeParams['ageOldestNum'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['ageOldestBudget'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams['ageOldestThreshold'] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 3:
				pnt("Hey guy, not all values associated with 'Buy most stale' are enabled/disabled")
				continue

			if allVals == 12: #all off
				pnt("What the actual fuck. Do you even realize that you have set EVERY parameter to be turned off? Just delete this program from your fucking VPS and save youself 4 bucks a goddamn month")
			else:
				if errorCode == 5:
					pntDev("Exited tradeParams")
					indentNum -= 1
					return 5
				else:
					pntDev("Exited tradeParams")
					indentNum -= 1
					return 0
		elif selection == "1":
			pntDev("Editing 1")
			calculateRemainingBudget()
			pnt("When sorted by percent change, how many stocks do you want to buy from? Starting from the greatest negative percent change")
			tradeParams['pcBottomNum'] = int(getInput())
			pnt("How much money do you want to invest into the " + str(tradeParams['pcBottomNum']) + " stocks EACH? (Minimum $1.00)")
			tradeParams['pcBottomBudget'] = float(getInput())
			pnt("At what negative percent change or greater do you want to buy? Enter a negative number")
			tradeParams['pcBottomThreshold'] = float(getInput())
		elif selection == "2":
			pntDev("Editing 2")
			calculateRemainingBudget()
			pnt("When sorted by percent change, how many stocks do you want to buy from? Starting from the greatest positive percent change")
			tradeParams['pcTopNum'] = int(getInput())
			pnt("How much money do you want to invest into the " + str(tradeParams['pcTopNum']) + " stocks EACH? (Minimum $1.00)")
			tradeParams['pcTopBudget'] = float(getInput())
		elif selection == "3":
			pntDev("Editing 3")
			calculateRemainingBudget()
			pnt("At what positive percent change or greater do you want to trigger a sell?")
			tradeParams['pcTopSellThresh'] = float(getInput())
			pnt("How much, in dollars, of each stock do you want to sell?")
			tradeParams['pcTopSellBudget'] = float(getInput())
		elif selection == "4":
			pntDev("Editing 4")
			calculateRemainingBudget()
			pnt("When sorted by equity, how many stocks do you want to buy from? Starting from the lowest amount")
			tradeParams['equityBottomNum'] = int(getInput())
			pnt("How much money do you want to invest into the " + str(tradeParams['equityBottomBudget']) + " stocks EACH? (Minimum $1.00)")
			tradeParams['equityBottomBudget'] = float(getInput())
		elif selection == "5":
			pntDev("Editing 5")
			calculateRemainingBudget()
			pnt("When sorted by last bought, how many stocks do you want to buy? Starting from the oldest trade. These stocks have not been bought the longest")
			tradeParams['ageOldestNum'] = int(getInput())
			pnt("Uhhhh i dont know how to explain this one")
			pnt("When sorted by last bought, oldest to most recent, buy " + str(tradeParams['ageOldestNum']) + " stocks that were bought more than N days ago")
			pnt("This value is a threshold. Once a stock was bought more than N days ago, this section can now buy from it")
			pnt("Solve for N")
			tradeParams['ageOldestThreshold'] = int(getInput())
			pnt("How much money do you want to invest into the " + str(budget("ageOldestNum")) + " stocks EACH? (Minimum $1.00)")
			tradeParams['ageOldestBudget'] = float(getInput())
def setupAccount(errorCode):
	global indentNum
	global accountInfo
	indentNum += 1
	pntDev("Entered setupAccount")
	selection = "0"
	if errorCode == 1 or errorCode == 6:
		selection = "1"
	while True:
		if errorCode == 0:
			pnt("1 - Username/Password")
			pnt("2 - Automatic 2factor authentication: " + str(accountInfo['auto2factor']))
			pnt("99 - Return to main menu")
			selection = getInput()

		if selection == "1":
			pnt("What is the username/email associated with your account?")
			accountInfo['username'] = getInput()
			pnt("What is the password associated with your account?")
			accountInfo['password'] = getInput()
			if errorCode == 1:
				selection = "2"
			elif errorCode == 6:
				pntDev("Exited setupAccount")
				indentNum -= 1
				return 5
		elif selection == "2":
			pnt("Do you want to enable automatic 2 factor authentication?")
			pnt("NOTE: to use this feature, you will have to sign into your robinhood account and turn on two factor authentication. Robinhood will ask you which two factor authorization app you want to use. Select “other”. Robinhood will present you with an alphanumeric code.")
			pnt("y - Yes")
			pnt("n - No")
			selection = getInput()
			if selection == "y":
				accountInfo['auto2factor'] = True
				pnt("What is the code?")
				accountInfo['auto2FactorCode'] = getInput()
			elif selection == "n":
				pass
			if errorCode == 1:
				pntDev("Exited setupAccount")
				indentNum -= 1
				return 5
		elif selection == "99":
			indentNum -= 1
			pntDev("Exited setupAccount")
			return 0
	pntDev("Exited setupAccount")
	indentNum -= 1
	return 0
def setup(errorCode):
	global indentNum
	indentNum += 1
	"""
	Error Codes
	0 - no error
	1 - load savedLogin.txt failed
	2 - load data.txt failed
	3 - load stockInfo failed
	4 - load budget failed
	5 - load tradeParams failed
	6 - invalid login
	"""
	pntDev("Entered setup")
	pntDev("Error code: " + str(errorCode))
	number = 0
	if errorCode == 1:
		number = setupAccount(errorCode)
	elif errorCode == 2:
		number = setupStocks(errorCode)
		if number == -1: #dev prefs selected
			pntDev("Exited setup")
			indentNum -= 1
			return
		number = setupBudget(errorCode)
		number = setupTradeParams(errorCode)
	elif errorCode == 3:
		number = setupStocks(errorCode)
	elif errorCode == 4:
		number = setupBudget(errorCode)
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
			pntDev("Exited setup")
			indentNum -= 1
			return

#print
def pntMajorAction(string): #prints sparknotes of what program does when it's active
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "Summary.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + (" " * indentNum*2) + str(string) + "\n")
	file.close()
	pnt(string)

	filesize = os.path.getsize(os.path.join(scriptDir, "Summary.txt"))
	if filesize >= 3000000000: # 3 gigabytes
		print("File size excessive. deleted Summary.txt")
		os.remove(os.path.join(scriptDir, "Summary.txt"))
def pnt(string): #prints to terminal and log file
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "Log.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + (" " * indentNum*2) + str(string) + "\n")
	file.close()
	print(string)

	filesize = os.path.getsize(os.path.join(scriptDir, "Log.txt"))
	if filesize >= 3000000000: # 3 gigabytes
		print("File size excessive. deleted Log.txt")
		os.remove(os.path.join(scriptDir, "Log.txt"))
def pntDev(string): #prints to developer log file
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "Dev.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + (" " * indentNum*2) + str(string) + "\n")
	file.close()

	filesize = os.path.getsize(os.path.join(scriptDir, "Dev.txt"))
	if filesize >= 3000000000: # 3 gigabytes
		print("File size excessive. deleted Dev.txt")
		os.remove(os.path.join(scriptDir, "Dev.txt"))
def calculateRemainingBudget(): 
	global indentNum
	indentNum += 1
	pntDev("Entered calculateRemainingBudget")
	
	monthlyRemaining = budget['monthlyBudgetTotal']
	weeklyRemaining = budget['weeklyBudgetTotal']
	dailyRemaining = budget['dailyBudgetTotal']
	if tradeParams['pcBottomNum'] != TRADE_PARAM_DISABLED:
		dailyRemaining -= tradeParams['pcBottomNum']*tradeParams['pcBottomBudget']
		weeklyRemaining -= tradeParams['pcBottomNum']*tradeParams['pcBottomBudget']*5
		monthlyRemaining -= tradeParams['pcBottomNum']*tradeParams['pcBottomBudget']*5*52/12
	if tradeParams['pcTopNum'] != TRADE_PARAM_DISABLED:
		dailyRemaining -= tradeParams['pcTopNum']*tradeParams['pcTopBudget']
		weeklyRemaining -= tradeParams['pcTopNum']*tradeParams['pcTopBudget']*5
		monthlyRemaining -= tradeParams['pcTopNum']*tradeParams['pcTopBudget']*5*52/12
	if tradeParams['equityBottomNum'] != TRADE_PARAM_DISABLED:
		dailyRemaining -= tradeParams['equityBottomNum']*tradeParams['equityBottomBudget']
		weeklyRemaining -= tradeParams['equityBottomNum']*tradeParams['equityBottomBudget']*5
		monthlyRemaining -= tradeParams['equityBottomNum']*tradeParams['equityBottomBudget']*5*52/12
	if tradeParams['ageOldestNum'] != TRADE_PARAM_DISABLED:
		dailyRemaining -= tradeParams['ageOldestNum']*tradeParams['ageOldestBudget']
		weeklyRemaining -= tradeParams['ageOldestNum']*tradeParams['ageOldestBudget']*5
		monthlyRemaining -= tradeParams['ageOldestNum']*tradeParams['ageOldestBudget']*5*52/12

	pnt("Monthly: $" + str(format(monthlyRemaining, '.2f')))
	pnt("Weekly: $" + str(format(weeklyRemaining, '.2f')))
	pnt("Daily: $" + str(format(dailyRemaining, '.2f')))

	pntDev("Exited calculateRemainingBudget")
	indentNum -= 1
def financesSplash():
	global indentNum
	global budget
	indentNum += 1
	pntDev("Entered financesSplash")
	pnt("Yearly payments to brokerage: $" + str(format(budget['monthlyBudgetTotal']*12, '.2f')))
	pnt("Monthly payments to brokerage: $" + str(format(budget['monthlyBudgetTotal'], '.2f')))
	pnt("Weekly budget total: $" + str(budget['weeklyBudgetTotal']))
	pnt("Weekly budget per stock: $" + str(budget['weeklyBudgetPerStock']))
	pnt("Daily budget total: $" + str(budget['dailyBudgetTotal']) + " (Excluding weekends)")
	pnt("Daily budget per stock: $" + str(budget['dailyBudgetPerStock']) + " (Excluding weekends)")
	pntDev("Exited financesSplash")
	indentNum -= 1

#helper
def placeOrder(stock, shoppingCart, buy): #returns false if trade fails
	global indentNum
	global budget
	indentNum += 1
	pntDev("Entered placeOrder")

	pnt(stock + " " + str(format(stockInfo[stock]['percentChange'], '.3f')) + "%" + " Remaining: $" + str(budget['moneyLeftDaily']) + "/$" + str(budget['moneyLeftTotal']))
	pntDev(stock + " " + str(format(stockInfo[stock]['percentChange'], '.3f')) + "%" + " Remaining: $" + str(budget['moneyLeftDaily']) + "/$" + str(budget['moneyLeftTotal']))

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
		pntMajorAction(stock + " bought for $" + str(shoppingCart))
		pntDev(stock + " bought for $" + str(shoppingCart))
	else:
		if defconLevel == 0:
			if stockInfo[stock]['isCrypto']:
				rs.orders.order_sell_crypto_by_price(stock, shoppingCart, shoppingCart+0.1)
			else:
				rs.orders.order_sell_fractional_by_price(stock, shoppingCart)
		else:
			pnt("Didn't sell shit")
		pntMajorAction(stock + " sold for $" + str(shoppingCart))
		pntDev(stock + " sold for $" + str(shoppingCart))

	wait(30)
	newUserProf = rs.account.build_user_profile()
	newBrokerage = float(newUserProf['cash'])

	if oldBrokerage == newBrokerage: #fail
		if defconLevel != 0:
			pnt("No way to tell if trade failed or succeeded")
			pntDev("Exited placeOrder")
			indentNum -= 1
			return True
		else:
			pntDev("Trade failed " + stock + " $" + str(shoppingCart))
			pntMajorAction("Trade failed " + stock + " $" + str(shoppingCart))
			orders = rs.orders.get_all_open_stock_orders() #WIP cancel all pending orders if fail
			pntDev(orders)
			pntDev("Exited placeOrder")
			indentNum -= 1
			return False
			
	else: #success
		if buy:
			if defconLevel != 2:
				stockInfo[stock]['daysSinceTrade'] = 0
				if stockInfo[stock]['lowConfidence']:
					stockInfo[stock]['lcBudget'] -= shoppingCart
				else:
					budget['moneyLeftDaily'] -= shoppingCart
			else:
				pnt("Didn't negate shit")
		else:
			if defconLevel != 2:
				stockInfo[stock]['daysSinceTrade'] = 0
				if stockInfo[stock]['lowConfidence']:
					stockInfo[stock]['lcBudget'] += shoppingCart
				else:
					budget['moneyLeftDaily'] += shoppingCart
			else:
				pnt("Didn't add shit")

		pntDev("Exited placeOrder")
		indentNum -= 1
		return True
def checkOrderValid(stock, shoppingCart, buy): #returns true if should buy/sell
	global indentNum
	indentNum += 1
	pntDev("Entered checkOrderValid")

	if buy:
		if budget['moneyLeftDaily'] < 1.0:
			pntDev("Not enough money $" + str(budget['moneyLeftDaily']))
			pntDev("Exited checkOrderValid")
			indentNum -= 1
			return False

		loweredPrice = False #if wanting to buy too much, lower price
		while shoppingCart > budget['moneyLeftDaily'] and budget['moneyLeftDaily'] > 1.0:
			shoppingCart -= 0.01
			loweredPrice = True
		if loweredPrice:
			pntDev("Insufficient funds initially. Shopping cart lowered to $" + str(shoppingCart))
			pnt("Insufficient funds initially. Shopping cart lowered to $" + str(shoppingCart))

		pntDev("Valid buy")

		pntDev("Exited checkOrderValid")
		indentNum -= 1
		return True
	else:
		if stockInfo[stock]['equity'] < shoppingCart:
			pntDev("Insufficient equity to sell")
			pnt("ATTEMPTED TO SELL $" + str(shoppingCart) + " OF " + stock + ". INSUFFICIENT EQUITY")
			pntDev("Exited checkOrderValid")
			indentNum -= 1
			return False

		pntDev("Valid sell")

		pntDev("Exited checkOrderValid")
		indentNum -= 1
		return True
def getStockPrices(): #puts new data in stockInfo
	global indentNum
	global stockInfo
	indentNum += 1
	pntDev("Entered getStockPrices")

	pnt("Getting prices...")
	wait(1)
	dictionary = rs.account.build_holdings(with_dividends=True)
	wait(1)
	cryptoDict = rs.crypto.get_crypto_positions()
	pntDev("Got dictionary")
	order = 0
	for stock in stockInfo:
		information = {
			"isCrypto": False,
			"price": 0.0,
			"lastPrice": 0.0,
			"equity": 0.0,
			"percentChange": 0.0,
			"daysSinceTrade": 0,
			"lowConfidence": False,
			"lcBudget": 0.0,
			"order": 0,
		}
		information['isCrypto'] = stockInfo[stock]['isCrypto']
		information['price'] = 0.0
		information['equity'] = 0.0
		information['percentChange'] = 0.0
		information['order'] = order

		if stockInfo[stock]['isCrypto']:
			wait(1)
			markPrice = rs.crypto.get_crypto_quote(stock)
			information['price'] = float(markPrice['mark_price'])
			for item in cryptoDict:
				if item['currency']['code'] == stock:
					information['equity'] = float(item['quantity']) * information['price']
		else:
			info = dictionary[stock]
			information['price'] = float(info['price'])
			information['equity'] = float(info['equity'])
		
		try:
			information['lastPrice'] = stockInfo[stock]['price']
		except:
			pntDev("Last price not found for " + stock)
			pnt("Last price not found for " + stock)
			information['lastPrice'] = information['price']

		information['percentChange'] = information['price'] / float(information['lastPrice'])
		if information['percentChange'] > 1.0:
			information['percentChange'] -= 1.0
			information['percentChange'] *= 100.0
		else:
			information['percentChange'] *= 100.0
			information['percentChange'] = 100.0 - information['percentChange']
			information['percentChange'] *= -1.0
		information['percentChange'] = float(format(information['percentChange'], '.3f'))
		
		try:
			avalue = stockInfo[stock]['daysSinceTrade']
		except:
			pntDev("daysSinceTrade for " + stock + " does not exist. Resetting to default value")
			pnt("daysSinceTrade for " + stock + " does not exist. Resetting to default value")
			information['daysSinceTrade'] = 0

		try:
			aval = stockInfo[stock]['lowConfidence']
		except:
			pntDev("lowConfidence not found for " + stock + ". Assuming FALSE")
			pnt("lowConfidence not found for " + stock + ". Assuming FALSE")
			information['lowConfidence'] = False

		stockInfo[stock] = information
		order += 1
	pntDev("Exited getStockPrices")
	indentNum -= 1
def sortByParameter(param): #changes 'order' in stockInfo
	global indentNum
	global stockInfo
	indentNum += 1
	pntDev("Entered sortByParameter")

	pntDev("Parameter: " + param)
	lowestVal = 9999999.0
	higherVal = 9999999.0
	order = 1
	#find lowest value
	nextStock = ''
	for stock in stockInfo:
		if stockInfo[stock]['lowConfidence']: #skip low confidence
			stockInfo[stock]['order'] = -50
			continue
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
	pntDev("Exited sortByParameter")
	indentNum -= 1

#misc
def wait(seconds):
	time.sleep(seconds)
def stop():
	pnt("Stop")
	pntDev("Stop")
	while True:
		wait(1)
def calculateBudget(budget): #returns calculated values
	global indentNum
	indentNum += 1
	pntDev("Entered calculateBudget")
	if budget['weeklyBudgetPerStock'] != 0.0:
		pntDev("weeklyBudgetPerStock is " + str(budget['weeklyBudgetPerStock']))
		budget['weeklyBudgetTotal'] = numAllCompanies*float(budget['weeklyBudgetPerStock'])
		budget['dailyBudgetTotal'] = float(budget['weeklyBudgetTotal'])/5
		budget['dailyBudgetPerStock'] = float(budget['weeklyBudgetPerStock'])/5
		budget['monthlyBudgetTotal'] = float(budget['weeklyBudgetTotal'])*52/12

	elif budget['weeklyBudgetTotal'] != 0.0:
		pntDev("weeklyBudgetTotal is " + str(budget['weeklyBudgetTotal']))
		budget['weeklyBudgetPerStock'] = float(budget['weeklyBudgetTotal'])/numAllCompanies
		budget['dailyBudgetTotal'] = float(budget['weeklyBudgetTotal'])/5
		budget['dailyBudgetPerStock'] = float(budget['weeklyBudgetPerStock'])/5
		budget['monthlyBudgetTotal'] = float(budget['weeklyBudgetTotal'])*52/12

	elif budget['dailyBudgetTotal'] != 0.0:
		pntDev("dailyBudgetTotal is " + str(budget['dailyBudgetTotal']))
		budget['dailyBudgetPerStock'] = float(budget['dailyBudgetTotal'])/numAllCompanies
		budget['weeklyBudgetPerStock'] = float(budget['dailyBudgetPerStock'])*5
		budget['weeklyBudgetTotal'] = numAllCompanies*float(budget['weeklyBudgetPerStock'])
		budget['monthlyBudgetTotal'] = float(budget['weeklyBudgetTotal'])*52/12

	elif budget['dailyBudgetPerStock'] != 0.0:
		pntDev("dailyBudgetPerStock is " + str(budget['dailyBudgetPerStock']))
		budget['weeklyBudgetPerStock'] = float(budget['dailyBudgetPerStock'])*5
		budget['weeklyBudgetTotal'] = numAllCompanies*float(budget['weeklyBudgetPerStock'])
		budget['dailyBudgetTotal'] = float(budget['weeklyBudgetTotal'])/5
		budget['monthlyBudgetTotal'] = float(budget['weeklyBudgetTotal'])*52/12

	elif budget['monthlyBudgetTotal'] != 0.0:
		pntDev("monthlyBudgetTotal is " + str(budget['monthlyBudgetTotal']))
		budget['weeklyBudgetTotal'] = float(budget['monthlyBudgetTotal'])*12/52
		budget['dailyBudgetTotal'] = float(budget['weeklyBudgetTotal'])/5
		budget['dailyBudgetPerStock'] = float(budget['dailyBudgetTotal'])/numAllCompanies
		budget['weeklyBudgetPerStock'] = float(budget['dailyBudgetPerStock'])*5

	pntDev("Exited calculateBudget")
	indentNum -= 1
	return budget
def upgradeFiles(): #files saved are from previous version, convert them to current version
	global indentNum
	indentNum += 1
	pnt("upgrading files")
	pnt("user input or whatever")
	pnt("Complete")
	indentNum -= 1
	#contents of this function change with each release starting after 1.0
def getInput(): #returns user input
	return input("-->")
def getTime(): #returns date and time as string
	now = datetime.now()
	weekday = now.weekday()
	hour = now.hour
	minute = now.minute
	day = now.day
	month = now.month
	year = now.year
	printout = str(month) + "/" + str(day) + "/" + str(year) + "  "
	if hour < 10:
		printout += "0"
	printout += str(hour)
	if minute < 10:
		printout += "0"
	printout += str(minute)
	return printout

#onstart
@timeoutable() #specifies function to be able to time out
def onstart():
	pnt("Program start")
	pntDev("Program start")
	value = ""
	try:
		value = sys.argv[1]
	except:
		pntDev("No input arg")

	if value == "setup":
		pntDev("Setup is input arg")
		startup(1)
	elif value == "test":
		pntDev("Test is input arg")
		startup(2)
	elif value == 'reset':
		pntDev("Reset is input arg")
		startup(3)
	elif value == 'trade':
		pntDev("Trade is input arg")
		startup(4)
	else:
		pntDev("Normal startup")
		startup(0)

	#shutdown
	save()
	logout()
	pntDev("Program end")
	pnt("")
	pntDev("")
if __name__ == "__main__":
	result = onstart(timeout=30*60) #30 minutes timeout in seconds
	if result == "None":
		pntDev("Timed out. Shutting down")