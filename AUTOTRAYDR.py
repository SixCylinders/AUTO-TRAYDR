# Changelog 0.6
"""
vastly improved setup
generally cleaned up code
startup() now accepts input arguments 'test' 'setup'
save/load greatly improved to better handle errors
setup verifies if dumbass user didn't put in data correctly
defcon variable added to aid testing
"""
import robin_stocks.robinhood as rs #i forgor what this one does :(
import sys #save terminal to txt
import json #save file
import time #time.sleep reduces CPU usage by waiting N seconds
import os #gets relative filepath
import pyotp #auto 2factor if you choose
from datetime import datetime #get time
import time

	#Saved data
numAllCompanies = 35
VERSION_NUMBER = 0.6
stockInfo = {}
stockList = ['AMD', 'AMZN', 'ARM', 'AVGO', #developer stocklist teehee
			'CATX', 'CIFR', 'CLSD', 'CLSK', 'COST', 'CRWD', 
			'DELL', 'DJT', 'DTST', 
			'GE', 'GOOGL',  
			'LLY', 'LMT', 
			'META', 'MSFT', 'MSTR', 'MU', 
			'NFLX', 'NKTX', 'NVDA', 
			'PAA', 
			'QCOM', 
			'SMCI', 'SOUN', 
			'TSLA', 'TSM', 
			'V', 'VINC', 
			'ZJYL']
cryptoList = ['AVAX', 'BTC', 'DOGE', 'ETH', 'SHIB', 'UNI']
budget = {}
tradeParams = {}
oneTime = {
	"testWeekend": False,
	"testTrade": False,
	"testNewMoney": False,
	"testReset": False,

	"weekendCheck": False,
	"priceCheck": False,
	"tradeCheck": False,
	"refilledCheck": False,
}
accountInfo = {
	"username": "",
	"password": "",
	"auto2factor": False,
	"auto2FactorCode": "",
}
	#/Saved data
#constants/important shit
TRADE_PARAM_DISABLED = 7050
PROGRAM_NAME = "AUTO-TRAYDR Version " + str(VERSION_NUMBER)
defconLevel = 0
"""
DEFCON levels
0 - Program will execute trades and perform as designed
1 - Program will NOT execute trades, but it will do everything else
2 - Program pretends to do everything. Values don't get changed
"""
skipSetup = False #overrides setup if dev prefs were loaded
#TODO stock info pnt in placeOrder should be formatted. too many decimals
#helper
def printRemainingBudget(monthly, weekly, daily):
	pntDev("Entered printRemainingBudget")
	pnt("Monthly: $" + str(format(monthly, '.2f')))
	pnt("Weekly: $" + str(format(weekly, '.2f')))
	pnt("Daily: $" + str(format(daily, '.2f')))
	pntDev("Exited printRemainingBudget")
def financesSplash():
	pntDev("Entered financesSplash")
	global budget
	pnt("Yearly payments to brokerage: $" + str(format(budget["monthlyBudgetTotal"]*12, '.2f')))
	pnt("Monthly payments to brokerage: $" + str(format(budget["monthlyBudgetTotal"], '.2f')))
	pnt("Weekly budget total: $" + str(budget["weeklyBudgetTotal"]))
	pnt("Weekly budget per stock: $" + str(budget["weeklyBudgetPerStock"]))
	pnt("Daily budget total: $" + str(budget["dailyBudgetTotal"]) + " (Excluding weekends)")
	pnt("Daily budget per stock: $" + str(budget["dailyBudgetPerStock"]) + " (Excluding weekends)")
	pntDev("Exited financesSplash")
def stop():
	while True:
		time.sleep(5)
		pass
def calculateBudget(budget): #returns calculated values
	pntDev("Entered calculateBudget")
	if budget["weeklyBudgetPerStock"] != 0.0:
		pntDev("weeklyBudgetPerStock is " + str(budget["weeklyBudgetPerStock"]))
		budget["weeklyBudgetTotal"] = numAllCompanies*float(budget["weeklyBudgetPerStock"])
		budget["dailyBudgetTotal"] = float(budget["weeklyBudgetTotal"])/5
		budget["dailyBudgetPerStock"] = float(budget["weeklyBudgetPerStock"])/5
		budget["monthlyBudgetTotal"] = float(budget["weeklyBudgetTotal"])*52/12

	elif budget["weeklyBudgetTotal"] != 0.0:
		pntDev("weeklyBudgetTotal is " + str(budget["weeklyBudgetTotal"]))
		budget["weeklyBudgetPerStock"] = float(budget["weeklyBudgetTotal"])/numAllCompanies
		budget["dailyBudgetTotal"] = float(budget["weeklyBudgetTotal"])/5
		budget["dailyBudgetPerStock"] = float(budget["weeklyBudgetPerStock"])/5
		budget["monthlyBudgetTotal"] = float(budget["weeklyBudgetTotal"])*52/12

	elif budget["dailyBudgetTotal"] != 0.0:
		pntDev("dailyBudgetTotal is " + str(budget["dailyBudgetTotal"]))
		budget["dailyBudgetPerStock"] = float(budget["dailyBudgetTotal"])/numAllCompanies
		budget["weeklyBudgetPerStock"] = float(budget["dailyBudgetPerStock"])*5
		budget["weeklyBudgetTotal"] = numAllCompanies*float(budget["weeklyBudgetPerStock"])
		budget["monthlyBudgetTotal"] = float(budget["weeklyBudgetTotal"])*52/12

	elif budget["dailyBudgetPerStock"] != 0.0:
		pntDev("dailyBudgetPerStock is " + str(budget["dailyBudgetPerStock"]))
		budget["weeklyBudgetPerStock"] = float(budget["dailyBudgetPerStock"])*5
		budget["weeklyBudgetTotal"] = numAllCompanies*float(budget["weeklyBudgetPerStock"])
		budget["dailyBudgetTotal"] = float(budget["weeklyBudgetTotal"])/5
		budget["monthlyBudgetTotal"] = float(budget["weeklyBudgetTotal"])*52/12

	elif budget["monthlyBudgetTotal"] != 0.0:
		pntDev("monthlyBudgetTotal is " + str(budget["monthlyBudgetTotal"]))
		budget["weeklyBudgetTotal"] = float(budget["monthlyBudgetTotal"])*12/52
		budget["dailyBudgetTotal"] = float(budget["weeklyBudgetTotal"])/5
		budget["dailyBudgetPerStock"] = float(budget["dailyBudgetTotal"])/numAllCompanies
		budget["weeklyBudgetPerStock"] = float(budget["dailyBudgetPerStock"])*5
	pntDev("Exited calculateBudget")
	return budget
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
def getStockPrices(): #puts new data in stockInfo
	pntDev("Entered getStockPrices")
	global stockInfo
	dictionary = rs.account.build_holdings(with_dividends=True) #comment
	cryptoDict = rs.crypto.get_crypto_positions()
	pntDev("Got dictionary")
	order = 0
	for stock in stockInfo:
		price = 0.0
		equity = 0.0
		pc = 0.0
		if stockInfo[stock]["isCrypto"]:
			markPrice = rs.crypto.get_crypto_quote(stock)
			price = float(markPrice["mark_price"])
			for item in cryptoDict:
				if item['currency']['code'] == stock:
					equity = float(item['quantity']) * price
			try:
				lastPrice = stockInfo[stock]['price']
			except:
				pntDev("Last price not found for " + stock)
				pnt("Last price for " + stock + " could not be found")
				lastPrice = price
		else:
			info = dictionary[stock]
			price = float(info['price'])
			equity = float(info['equity'])
			try:
				lastPrice = stockInfo[stock]['price']
			except:
				pntDev("Last price not found for " + stock)
				pnt("Last price for " + stock + " could not be found")
				lastPrice = price

		pc = price / float(lastPrice)
		wentUp = False
		if pc > 1.0:
			pc -= 1.0
			pc *= 100.0
			wentUp = True
		else:
			pc *= 100.0
			pc = 100.0 - pc
			pc *= -1.0
		pc = float(format(pc, '.3f'))
		
		try:
			stockInfo[stock] = {
				"order": order,
				"isCrypto": stockInfo[stock]["isCrypto"],
				"price": price,
				"lastPrice": lastPrice,
				"equity": equity,
				"percentChange": pc,
				"daysSinceTrade": stockInfo[stock]["daysSinceTrade"],
			}
		except:
			pntDev("daysSinceTrade for " + stock + " does not exist. Resetting to default value")
			stockInfo[stock] = {
				"order": order,
				"isCrypto": stockInfo[stock]["isCrypto"],
				"price": price,
				"lastPrice": lastPrice,
				"equity": equity,
				"percentChange": pc,
				"daysSinceTrade": 0,
			}
		order += 1
	pntDev("Exited getStockPrices")
def upgradeFiles(): #files saved are from previous version, convert them to current version
	pnt("upgrading files")
	pnt("user input or whatever")
	pnt("Complete")
	#contents of this function change with each release starting after 1.0
#setup
def propagateDevPrefs():
	pntDev("Entered loadDevPrefs")
	pntDev("Developer prefs loading...")
	pnt("Very well. Loading developer preferences...")
	pnt("Good morning, petty officer")

	global stockInfo
	stockInfo = {}
	for stock in stockList:
		stockInfo[stock] = {}
		stockInfo[stock]["isCrypto"] = False
	for crypto in cryptoList:
		stockInfo[crypto] = {}
		stockInfo[crypto]["isCrypto"] = True
	pntDev("Dev stocks loaded")

	global budget
	budget["monthlyBudgetTotal"] = 525.0
	budget["weeklyBudgetTotal"] = 0.0
	budget["dailyBudgetTotal"] = 0.0
	budget["dailyBudgetPerStock"] = 0.0
	budget["weeklyBudgetPerStock"] = 0.0
	try:
		value = budget["moneyLeftDaily"]
		value = budget["moneyLeftTotal"]
	except:
		budget["moneyLeftDaily"] = 0.0
		budget["moneyLeftTotal"] = 0.0
	budget = calculateBudget(budget)
	financesSplash()
	pntDev("Dev budget loaded")

	global tradeParams
	tradeParams = {}
	tradeParams["pcBottomThreshold"] = -1.0
	tradeParams["pcBottomNum"] = 5
	tradeParams["pcBottomBudget"] = 1.0
	tradeParams["pcTopNum"] = 3
	tradeParams["pcTopBudget"] = 1.00
	tradeParams["equityBottomNum"] = 5
	tradeParams["equityBottomBudget"] = 1.0
	tradeParams["ageOldestNum"] = 3
	tradeParams["ageOldestThreshold"] = 7
	tradeParams["ageOldestBudget"] = 1.0
	tradeParams["pcTopSellThresh"] = 4.5
	tradeParams["pcTopSellBudget"] = 2.0
	pntDev("Dev tradeParams loaded")

	monthlyRemining = budget["monthlyBudgetTotal"]
	weeklyRemaining = budget["weeklyBudgetTotal"]
	dailyRemaining = budget["dailyBudgetTotal"]
	dailyRemaining -= tradeParams["pcBottomNum"]*tradeParams["pcBottomBudget"]
	weeklyRemaining -= tradeParams["pcBottomNum"]*tradeParams["pcBottomBudget"]*5
	monthlyRemining -= tradeParams["pcBottomNum"]*tradeParams["pcBottomBudget"]*5*52/12
	dailyRemaining -= tradeParams["pcTopNum"]*tradeParams["pcTopBudget"]
	weeklyRemaining -= tradeParams["pcTopNum"]*tradeParams["pcTopBudget"]*5
	monthlyRemining -= tradeParams["pcTopNum"]*tradeParams["pcTopBudget"]*5*52/12
	dailyRemaining -= tradeParams["equityBottomNum"]*tradeParams["equityBottomBudget"]
	weeklyRemaining -= tradeParams["equityBottomNum"]*tradeParams["equityBottomBudget"]*5
	monthlyRemining -= tradeParams["equityBottomNum"]*tradeParams["equityBottomBudget"]*5*52/12
	dailyRemaining -= tradeParams["ageOldestNum"]*tradeParams["ageOldestBudget"]
	weeklyRemaining -= tradeParams["ageOldestNum"]*tradeParams["ageOldestBudget"]*5
	monthlyRemining -= tradeParams["ageOldestNum"]*tradeParams["ageOldestBudget"]*5*52/12
	pntDev("Remaining budget calculated")

	pnt("Remaining:")
	printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
	pnt("Daily remaining funds: $" + str(dailyRemaining) + " (You should have around a dollar's worth of margin here. Do NOT try to optimize this below $0.10)")
	if dailyRemaining <= 0.05:
		pnt("Buy orders exceed daily budget. Buy less shit, or work harder")
		pnt("There is a hard-coded $0.05 margin for daily remaining funds, which you cannot go below. Values displayed are rounded, and do not show all decimal points")
	global skipSetup
	skipSetup = True
	pntDev("Exited loadDevPrefs")
	return 5 #exit
def setupMainMenu(errorCode):
	pntDev("Entered main menu")
	if errorCode != 0:
		pntDev("Error code " + str(errorCode))
	if errorCode == 1:
		return 4 #go to account


	pnt("What would you like to edit?")
	pnt("1 - Stocks/Crypto")
	pnt("2 - Budget")
	pnt("3 - Trade parameters")
	pnt("4 - Account")
	pnt("5 - Exit")
	selection = getInput()
	if selection == "1":
		return 1
	elif selection == "2":
		return 2
	elif selection == "3":
		return 3
	elif selection == "4":
		return 4
	elif selection == "5":
		return 5
	elif selection == "secret":
		return propagateDevPrefs()
	pntDev("Exited main menu")
def setupStocks(errorCode):
	pntDev("Entered stock menu")
	pnt("What stocks do you want to invest in?")
	pnt("Type the ticker name for each stock one at a time. (Eg: NVDA)")
	pnt("0 - Finished")
	pnt("1 - Change between inputting stocks, and cryptocurrencies")
	pnt("2 - Remove the last stock")
	pnt("3 - Remove all stocks")
	if errorCode != 2 and errorCode != 3:
		pnt("99 - Return to main manu")
	global stockInfo
	if len(stockInfo) > 0:
		pnt("Current stocks:")
		for stock in stockInfo:
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
			return 1 #restart
		elif selection == "3":
			pntDev("All stocks removed")
			stockInfo.clear()
			return 1
		elif selection == "0":
			if len(stockInfo) > 0:
				pntDev("Broke stock input while True loop 2")
				break
			else:
				pnt("Add a stock first, guy")
		elif selection == "99":
			if len(stockInfo) > 0:
				if errorCode == 2 or errorCode == 3:
					pnt("You can't exit to the main menu. data.txt couldn't be loaded, so repopulate the shit")
				pntDev("Broke stock input while True loop 2")
				return 0
			else:
				pnt("Add a stock first, guy")
		elif selection == "secret":
			propagateDevPrefs()
			save(False)
			return -1
		else:
			stockInfo[selection] = {}
			if inputStocks:
				pntDev("Stock " + selection + " added")
				stockInfo[selection]["isCrypto"] = False
			else:
				pntDev("Crypto " + selection + " added")
				stockInfo[selection]["isCrypto"] = True
	global numAllCompanies
	numAllCompanies = len(stockInfo)
	pntDev("Exited stock menu")
	return 0
def setupBudget(errorCode):
	pntDev("Entered budget menu")

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
				return 0
		if selection != "6" and selection != "99":
			pnt("With how much money?")
			pnt("Reset budget values")
			pntDev("Reset budget values")
			global budget
			budget["monthlyBudgetTotal"] = 0.0
			budget["weeklyBudgetTotal"] = 0.0
			budget["dailyBudgetTotal"] = 0.0
			budget["dailyBudgetPerStock"] = 0.0
			budget["weeklyBudgetPerStock"] = 0.0
			budget["moneyLeftDaily"] = 0.0
			budget["moneyLeftTotal"] = 0.0
		if selection == "1":
			pnt("Editing monthlyBudgetTotal")
			budget["monthlyBudgetTotal"] = float(getInput())
		elif selection == "2":
			pnt("Editing weeklyBudgetTotal")
			budget["weeklyBudgetTotal"] = float(getInput())
		elif selection == "3":
			pnt("Editing dailyBudgetTotal")
			budget["dailyBudgetTotal"] = float(getInput())
		elif selection == "4":
			pnt("Editing weeklyBudgetPerStock")
			budget["weeklyBudgetPerStock"] = float(getInput())
		elif selection == "5":
			pnt("Editing dailyBudgetPerStock")
			budget["dailyBudgetPerStock"] = float(getInput())
		elif selection == "6":
			pntDev("Editing moneyLeftTotal")
			pnt("How much money is currently in your Robinhood brokerage? (This money must not go down except by action of this program, otherwise it will attempt to spend money that doesn't exist)")
			pnt("This program assumes deposits are made on the 1st of the month. If you don't want to wait until then, fill this out. Otherwise, put 0")
			pnt("TODO: allow deposits on other days")
			budget["moneyLeftTotal"] = float(getInput())
			pntDev("Reset moneyLeftDaily")
			pnt("Reset balance for tomorrow")
			budget["moneyLeftDaily"] = 0.0
			
			pnt("Keep in mind, this program does not include weekends, so these values may be lower than expected")
			budget = calculateBudget(budget)
			financesSplash()
		elif selection == "99":
			budget = calculateBudget(budget)
			pntDev("Exited budget menu")
			if errorCode == 4:
				return 5
			else:
				return 0
		else:
			pntDev("Invalid input, dumbass")	
def setupTradeParams(errorCode):
	pntDev("Entered tradeParams menu")
	
	global budget
	monthlyRemining = budget["monthlyBudgetTotal"]
	weeklyRemaining = budget["weeklyBudgetTotal"]
	dailyRemaining = budget["dailyBudgetTotal"]
	while True:
		pnt("Which trade parameter do you want to edit?")
		pnt("To disable a trade parameter, set ALL of its associated values to " + str(TRADE_PARAM_DISABLED))
		if errorCode == 0:
			pnt("Sorted by percent change:")
			pnt("1 - Buy greatest NEGATIVE percent change: " + str(tradeParams["pcBottomNum"]) + "/$" + str(tradeParams["pcBottomBudget"]) + ", " + str(tradeParams["pcBottomThreshold"]) + "% Threshold")
			pnt("2 - Buy greatest POSITIVE percent change: " + str(tradeParams["pcTopNum"]) + "/$" + str(tradeParams["pcTopBudget"]))
			pnt("3 - Sell N dollars at positive percent change threshold: $" + str(tradeParams["pcTopSellBudget"]) + ", " + str(tradeParams["pcTopSellThresh"]) + "% Threshold")
			pnt("Sorted by equity:")
			pnt("4 - Buy lowest equity: " + str(tradeParams["equityBottomNum"]) + "/$" + str(tradeParams["equityBottomBudget"]))
			pnt("Sorted by age:")
			pnt("5 - Buy most stale: " + str(tradeParams["ageOldestNum"]) + "/$" + str(tradeParams["ageOldestBudget"]) + ", When older than " + str(tradeParams["ageOldestThreshold"]) + " days")
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
			tradeParams["pcBottomNum"] = 0
			tradeParams["pcBottomBudget"] = 0.0
			tradeParams["pcBottomThreshold"] = 0.0
			tradeParams["pcTopNum"] = 0
			tradeParams["pcTopBudget"] = 0.0
			tradeParams["pcTopSellThresh"] = 0.0
			tradeParams["pcTopSellBudget"] = 0.0
			tradeParams["equityBottomNum"] = 0
			tradeParams["equityBottomBudget"] = 0.0
			tradeParams["ageOldestNum"] = 0
			tradeParams["ageOldestBudget"] = 0.0
			tradeParams["ageOldestThreshold"] = 0.0
		else:
			pnt("99 - Return to main menu")
		selection = getInput()
		if selection == "99":
			pntDev("Editing 99")
			#error checking
			allVals = 0
			value = 0
			if tradeParams["pcBottomNum"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["pcBottomBudget"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["pcBottomThreshold"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 3:
				pnt("Hey guy, not all values associated with 'Buy greatest NEGATIVE percent change' are enabled/disabled")
				continue
			value = 0
			if tradeParams["pcTopNum"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["pcTopBudget"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 2:
				pnt("Hey guy, not all values associated with 'Buy greatest POSITIVE percent change' are enabled/disabled")
				continue
			value = 0
			if tradeParams["pcTopSellThresh"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["pcTopSellBudget"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 2:
				pnt("Hey guy, not all values associated with 'Sell N dollars at positive percent change threshold' are enabled/disabled")
				continue
			value = 0
			if tradeParams["equityBottomNum"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["equityBottomBudget"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 2:
				pnt("Hey guy, not all values associated with 'Buy lowest equity' are enabled/disabled")
				continue
			value = 0
			if tradeParams["ageOldestNum"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["ageOldestBudget"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if tradeParams["ageOldestThreshold"] == TRADE_PARAM_DISABLED:
				value += 1
				allVals += 1
			if value != 0 and value != 3:
				pnt("Hey guy, not all values associated with 'Buy most stale' are enabled/disabled")
				continue

			if allVals == 12: #all off
				pnt("What the actual fuck. Do you even realize that you have set EVERY parameter to be turned off? Just delete this program from your fucking VPS and save youself 4 bucks a goddamn month")
			else:
				if errorCode == 5:
					return 5
				else:
					return 0
		elif selection == "1":
			pntDev("Editing 1")
			pnt("When sorted by percent change, how many stocks do you want to buy from? Starting from the greatest negative percent change")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcBottomNum"] = int(getInput())
			pnt("How much money do you want to invest into the " + str(tradeParams["pcBottomNum"]) + " stocks EACH? (Minimum $1.00)")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcBottomBudget"] = float(getInput())
			pnt("At what negative percent change or greater do you want to buy? Enter a negative number")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcBottomThreshold"] = float(getInput())
		elif selection == "2":
			pntDev("Editing 2")
			pnt("When sorted by percent change, how many stocks do you want to buy from? Starting from the greatest positive percent change")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcTopNum"] = int(getInput())
			pnt("How much money do you want to invest into the " + str(tradeParams["pcTopNum"]) + " stocks EACH? (Minimum $1.00)")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcTopBudget"] = float(getInput())
		elif selection == "3":
			pntDev("Editing 3")
			pnt("At what positive percent change or greater do you want to trigger a sell?")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcTopSellThresh"] = float(getInput())
			pnt("How much, in dollars, of each stock do you want to sell?")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["pcTopSellBudget"] = float(getInput())
		elif selection == "4":
			pntDev("Editing 4")
			pnt("When sorted by equity, how many stocks do you want to buy from? Starting from the lowest amount")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["equityBottomNum"] = int(getInput())
			pnt("How much money do you want to invest into the " + str(tradeParams["equityBottomBudget"]) + " stocks EACH? (Minimum $1.00)")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["equityBottomBudget"] = float(getInput())
		elif selection == "5":
			pntDev("Editing 5")
			pnt("When sorted by last bought, how many stocks do you want to buy? Starting from the oldest trade. These stocks have not been bought the longest")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["ageOldestNum"] = int(getInput())
			pnt("Uhhhh i dont know how to explain this one")
			pnt("When sorted by last bought, oldest to most recent, buy " + str(tradeParams["ageOldestNum"]) + " stocks that were bought more than N days ago")
			pnt("This value is a threshold. Once a stock was bought more than N days ago, this section can now buy from it")
			pnt("Solve for N")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["ageOldestThreshold"] = int(getInput())
			pnt("How much money do you want to invest into the " + str(budget("ageOldestNum")) + " stocks EACH? (Minimum $1.00)")
			printRemainingBudget(monthlyRemining, weeklyRemaining, dailyRemaining)
			tradeParams["ageOldestBudget"] = float(getInput())
def setupAccount(errorCode):
	pntDev("Entered account menu")
	global accountInfo
	selection = "0"
	if errorCode == 1 or errorCode == 6:
		selection = "1"
	while True:
		if errorCode == 0:
			pnt("1 - Username/Password")
			pnt("2 - (Coming soon) Automatic 2factor authentication: " + str(accountInfo["auto2factor"]))
			pnt("99 - Return to main menu")
			selection = getInput()

		if selection == "1":
			pnt("What is the username/email associated with your account?")
			accountInfo["username"] = getInput()
			pnt("What is the password associated with your account?")
			accountInfo["password"] = getInput()
			if errorCode == 1:
				selection = "2"
			elif errorCode == 6:
				return 5
		elif selection == "2":
			pnt("Do you want to enable automatic 2 factor authentication?")
			pnt("THIS FEATURE IS UNDER DEVELOPMENT AND DOES NOT WORK")
			pnt("NOTE: to use this feature, you will have to sign into your robinhood account and turn on two factor authentication. Robinhood will ask you which two factor authorization app you want to use. Select “other”. Robinhood will present you with an alphanumeric code.")
			pnt("y - Yes")
			pnt("n - No")
			#selection = getInput()
			pnt("-->n")
			selection = "n"
			if selection == "y":
				accountInfo["auto2factor"] = True
				pnt("What is the code?")
				accountInfo["auto2FactorCode"] = getInput()
			elif selection == "n":
				pass
			if errorCode == 1:
				return 5
		elif selection == "99":
			return 0
	pntDev("Exited account menu")
	return 0
def setup(errorCode):
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
			save(False)
			pntDev("Broke main while True loop 2")
			pntDev("Exited setup")
			return
#startup/shutdown
def splash():
	pntDev("Entered splash")
	pnt(PROGRAM_NAME)
	pnt("[[[Description goes here]]]")
	financesSplash()
	pnt("Sorted by percent change")
	pnt("Buy bottom " + str(tradeParams["pcBottomNum"]) + " stocks, $" + str(tradeParams["pcBottomBudget"]) + " each. Only if stock's percent change is less than -" + str(tradeParams["pcBottomThreshold"]) + "%")
	pnt("Buy top " + str(tradeParams["pcTopNum"]) + " stocks, $" + str(tradeParams["pcTopBudget"]) + " each")
	pnt("Sell $" + str(tradeParams["pcTopSellBudget"]) + " of each stock when percent change is greater than +" + str(tradeParams["pcTopSellThresh"]) + "%")
	pnt("Sorted by equity")
	pnt("Buy bottom " + str(tradeParams["equityBottomNum"]) + " stocks, $" + str(tradeParams["equityBottomBudget"]) + " each")
	pnt("Sorted by last bought")
	pnt("Buy " + str(tradeParams["ageOldestNum"]) + " stocks (When older than " + str(tradeParams["ageOldestThreshold"]) + " days), $" + str(tradeParams["ageOldestBudget"]) + " each")
	maxBudget = ((tradeParams["pcBottomNum"]*tradeParams["pcBottomBudget"])
		+(tradeParams["pcTopNum"]*tradeParams["pcTopBudget"])
		+(tradeParams["equityBottomNum"]*tradeParams["equityBottomBudget"])
		+(tradeParams["ageOldestNum"]*tradeParams["ageOldestBudget"])
	)
	remainingFunds = float(format(budget["dailyBudgetTotal"]-maxBudget, '.3f'))
	pnt("Daily remaining funds: $" + str(remainingFunds) + " (You should have around a dollar's worth of margin here. Do NOT try to optimize this below $0.10)")
	if remainingFunds < 0.0:
		pnt("Buy orders exceed daily budget. Buy less shit, or work harder")
	pntDev("Exited splash")
def startup(condition):
	"""
	Startup conditions
	0 - normal
	1 - user activated setup
	2 - test all mainLoop functions
	"""
	pntDev("Entered startup")
	pntDev("Startup condition " + str(condition))
	pnt(PROGRAM_NAME)
	pntMajorAction("Program start")
	while True:
		if load(): #calls setup if error, returns true
			continue
		if condition == 1 and not skipSetup:
			setup(0)
		if login(): #returns true if error
			continue
		break
	if condition == 0 or condition == 1:
		pntDev("Exited startup")
		mainLoop()
	elif condition == 2:
		pntDev("Program disarmed")
		global defconLevel
		tempArmed = defconLevel
		defconLevel = 2
		global oneTime
		pnt("Testing weekend...")
		pntDev("Testing weekend")
		oneTime["testWeekend"] = True
		oneTime["testTrade"] = False
		oneTime["testNewMoney"] = False
		oneTime["testReset"] = False
		pntDev("Exited startup")
		mainLoop()
		login()
		pntDev("Entered startup")
		pnt("Testing trade...")
		pntDev("Testing trade")
		oneTime["testWeekend"] = False
		oneTime["testTrade"] = True
		oneTime["testNewMoney"] = False
		oneTime["testReset"] = False
		pntDev("Exited startup")
		mainLoop()
		login()
		pntDev("Entered startup")
		pnt("Testing new money...")
		pntDev("Testing new money")
		oneTime["testWeekend"] = False
		oneTime["testTrade"] = False
		oneTime["testNewMoney"] = True
		oneTime["testReset"] = False
		pntDev("Exited startup")
		mainLoop()
		login()
		pntDev("Entered startup")
		pnt("Testing reset...")
		pntDev("Testing reset")
		oneTime["testWeekend"] = False
		oneTime["testTrade"] = False
		oneTime["testNewMoney"] = False
		oneTime["testReset"] = True
		pntDev("Exited startup")
		mainLoop()
		pnt("Testing complete")
		pntDev("Testing complete")
		defconLevel = tempArmed
		return
def login(): #calls setup and returns true if error
	pntDev("Entered login")
	pnt("Logging in...")
	try:
		global accountInfo
		login = rs.login(accountInfo["username"], accountInfo["password"])
		pntDev("Login successful")
		pntDev("Broke while True loop")
		pnt("Welcome, " + str(accountInfo["username"]))
		return False
	except:
		pntDev("Error logging in. Invalid accountInfo")
		pnt("ERROR-INVALIDLOGIN")
		pnt("Error logging in. Check spelling of your username and password")
		pnt("User- " + accountInfo["username"])
		pnt("Pass- " + accountInfo["password"])
		setup(1)
		return True
	pntDev("Exited login")
def logout():
	pntDev("Entered logout")
	pnt("Logging out...")
	rs.logout()
	pntDev("Exited logout")
#print
def pntMajorAction(string): #prints sparknotes of what program does when it's active
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "Summary.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + " " + str(string) + "\n")
	file.close()
	pnt(string)
def pnt(string): #prints to terminal and log file
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "Log.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + " " + str(string) + "\n")
	file.close()
	print(string)
def pntDev(string): #prints to developer log file
	scriptDir = os.path.dirname(__file__)
	file = open(os.path.join(scriptDir, "Dev.txt"), "a")
	if string == "":
		file.write("\n")
	else:
		file.write(getTime() + " " + str(string) + "\n")
	file.close()
#trade logic
def placeOrder(stock, shoppingCart, buy):
	pntDev("Entered placeOrder")
	global budget
	global stockInfo
	pnt(stock + ": " + str(stockInfo[stock]['percentChange']) + "% Equity: $" + str(stockInfo[stock]['equity']) + " Remaining: $" + str(budget["moneyLeftDaily"]) + "/$" + str(budget["moneyLeftTotal"]))
	if buy:
		pntDev("Buy")
		#if wanting to buy too much, lower price
		loweredPrice = False
		while shoppingCart > budget["moneyLeftDaily"] and budget["moneyLeftDaily"] > 1.0:
			shoppingCart -= 0.01
			loweredPrice = True
		if loweredPrice:
			pntDev("Insufficient funds. Shopping cart lowered")
			pntMajorAction("Insufficient funds. Ask price lowered to remaining funds")

		if shoppingCart > budget["moneyLeftDaily"]:
			pntDev("Shopping cart greater than moneyLeftDaily " + str(shoppingCart) + "/" + str(budget["moneyLeftDaily"]))
			pntMajorAction("ATTEMPTED TO BUY $" + str(shoppingCart) + " OF " + stock + ". INSUFFICIENT EQUITY")
		else:
			if defconLevel == 0:
				rs.orders.order_buy_fractional_by_price(stock, shoppingCart)
				pntMajorAction(stock + " bought for $" + str(shoppingCart))
				pntDev(stock + " bought for $" + str(shoppingCart))
				stockInfo[stock]['daysSinceTrade'] = 0
				budget["moneyLeftDaily"] -= shoppingCart
			elif defconLevel == 1:
				pntMajorAction(stock + " bought for $" + str(shoppingCart))
				pntMajorAction("No stock bought")
				pntDev(stock + " bought for $" + str(shoppingCart))
				pntDev("No stock bought")
				stockInfo[stock]['daysSinceTrade'] = 0
				budget["moneyLeftDaily"] -= shoppingCart
			elif defconLevel == 2:
				pntMajorAction(stock + " attempted to buy for $" + str(shoppingCart))
				pntMajorAction("No stock bought. No money negated")
				pntDev(stock + " attempted to buy for $" + str(shoppingCart))
				pntDev("No stock bought. No money negated")
	else:
		pntDev("Sell")
		if stockInfo[stock]["equity"] < shoppingCart:
			pntDev("Insufficient equity to sell")
			pntMajorAction("ATTEMPTED TO SELL $" + str(shoppingCart) + " OF " + stock + ". INSUFFICIENT EQUITY")
		else:
			if defconLevel == 0:
				rs.orders.order_sell_fractional_by_price(stock, shoppingCart)
				pntMajorAction(stock + " sold for $" + str(shoppingCart))
				pntDev(stock + " sold for $" + str(shoppingCart))
				stockInfo[stock]['daysSinceTrade'] = 0
				budget["moneyLeftTotal"] += shoppingCart
			elif defconLevel == 1:
				pntMajorAction(stock + " sold for $" + str(shoppingCart))
				pntMajorAction("No stock sold")
				pntDev(stock + " sold for $" + str(shoppingCart))
				pntDev("No stock sold")
				stockInfo[stock]['daysSinceTrade'] = 0
				budget["moneyLeftTotal"] += shoppingCart
			elif defconLevel == 2:
				pntMajorAction(stock + " sold for $" + str(shoppingCart))
				pntMajorAction("No stock sold. No money added")
				pntDev(stock + " sold for $" + str(shoppingCart))
				pntDev("No stock sold. No money added")
				
	pntDev("Exited placeOrder")
def sortByParameter(info, param):
	pntDev("Entered sortByParameter")
	lowestVal = 9999999.0
	higherVal = 9999999.0
	order = 1
	#find lowest value
	nextStock = ''
	for stock in info:
		if info[stock][param] < lowestVal:
			lowestVal = info[stock][param]
			nextStock = stock
		info[stock]['order'] = -1
	info[nextStock]['order'] = 0
	#work up from there
	counter = 0
	while True:
		counter += 1
		if counter > 100:
			while True:
				pass
		if order > len(info)-1:
			break;
		for stock in info:
			if info[stock]['order'] == -1: #stock order not set
				if info[stock][param] >= lowestVal and info[stock][param] < higherVal:
					higherVal = info[stock][param]
					nextStock = stock
		lowestVal = higherVal
		higherVal = 9999999.0
		info[nextStock]['order'] = order
		order += 1
	pntDev("Exited sortByParameter")
	return info
def trade():
	pntDev("Entered trade")
	global stockInfo
	global budget
	global tradeParams

	stockInfo = sortByParameter(stockInfo, 'percentChange')

	#sell top
	pntDev("Sell top percent change " + str(tradeParams["pcTopSellThresh"]) + "%")
	if tradeParams["pcTopSellThresh"] != TRADE_PARAM_DISABLED:
		pnt("Sell stocks if percent change above " + str(tradeParams["pcTopSellThresh"]) + "%")
		for stock in stockInfo:
			if stockInfo[stock]['percentChange'] >= tradeParams["pcTopSellThresh"]:
				placeOrder(stock, tradeParams["pcTopSellBudget"], False)
		pnt("No more stocks meet threshold values")

	#buy bottom
	pntDev("Buy bottom percent change " + str(tradeParams["pcBottomNum"]))
	if tradeParams["pcBottomNum"] != TRADE_PARAM_DISABLED:
		pnt("Buy " + str(tradeParams["pcBottomNum"]) + " bottom % change")
		for stock in stockInfo:
			if stockInfo[stock]['order'] < tradeParams["pcBottomNum"]:
				if stockInfo[stock]['percentChange'] > tradeParams["pcBottomThreshold"]:
					pntDev(stock + " not considered due to threshold. Buy bottom percent change")
					pnt(stock + " not considered due to threshold")
					continue
				shoppingCart = tradeParams["pcBottomBudget"]
				if stockInfo[stock]['percentChange'] < -10.0:
					shoppingCart += 15
				elif stockInfo[stock]['percentChange'] < -8.0: 
					shoppingCart += 10
				elif stockInfo[stock]['percentChange'] < -5.0:
					shoppingCart += 8
				elif stockInfo[stock]['percentChange'] < -3.0: 
					shoppingCart += 5
				placeOrder(stock, shoppingCart, True)

	#buy top
	pntDev("Buy top percent change " + str(tradeParams["pcTopNum"]))
	#TODO somethings fucked up with this. places orders for too many stocks
	if tradeParams["pcTopNum"] != TRADE_PARAM_DISABLED:
		pnt("Buy " + str(tradeParams["pcTopNum"]) + " top % change")
		for stock in stockInfo:
			if stockInfo[stock]['order'] > numAllCompanies - tradeParams["pcTopNum"] - 1:
				if tradeParams["pcTopSellThresh"] != TRADE_PARAM_DISABLED: #if enabled, dont buy stocks that you sold
					if stockInfo[stock]['percentChange'] >= tradeParams["pcTopSellThresh"]:
						pnt(stock + " skipped due to selling earlier")
						pntDev(stock + " not considered due to selling earlier")
						continue
				placeOrder(stock, tradeParams["pcTopBudget"], True)
	
	stockInfo = sortByParameter(stockInfo, 'equity')

	#buy bottom
	pntDev("Buy bottom equity " + str(tradeParams["equityBottomNum"]))
	if tradeParams["equityBottomNum"] != TRADE_PARAM_DISABLED:
		pnt("Buy " + str(tradeParams["equityBottomNum"]) + " lowest equity")
		for stock in stockInfo:
			if stockInfo[stock]['order'] < tradeParams["equityBottomNum"]:
				placeOrder(stock, tradeParams["equityBottomBudget"], True)
	
	stockInfo = sortByParameter(stockInfo, 'daysSinceTrade')

	#buy oldest
	pntDev("Buy oldest " + str(tradeParams["ageOldestNum"]))
	if tradeParams["ageOldestNum"] != TRADE_PARAM_DISABLED:
		pnt("Buy " + str(tradeParams["ageOldestNum"]) + " oldest stock")
		for stock in stockInfo:
			if stockInfo[stock]['order'] < tradeParams["ageOldestNum"]:
				if stockInfo[stock]['daysSinceTrade'] < tradeParams["ageOldestThreshold"]:
					continue
				#if budget["moneyLeftDaily"] >= budget["weeklyBudgetTotal"]: #buy more if idle money
				#	shoppingCart += budget["weeklyBudgetTotal"] * 0.05
				pnt("V Bought " + str(stockInfo[stock]['daysSinceTrade']) + " business days ago")
				placeOrder(stock, tradeParams["ageOldestBudget"], True)
	pntDev("Exited trade")
#save/load
def save(updatePrices):
	pntDev("Entered save")
	pnt("Saving...")
	scriptDir = os.path.dirname(__file__)
	absFilePath = os.path.join(scriptDir, "savedLogin.txt")
	with open(absFilePath, "w") as fp:
			json.dump(accountInfo, fp)
			pntDev("Saved savedLogin.txt")

	if updatePrices and defconLevel != 2:
		getStockPrices()
	global stockInfo
	global budget
	global tradeParams
	global oneTime
	try:
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
		pntDev("Saved")
	except:
		pntDev("Error in saving")
		pnt("Error in saving. Dunno what caused that")
	pnt("Saving complete")
	pntDev("Exited save")
def load(): #calls setup and returns true if error
	pntDev("Entered load")
	try:
		global accountInfo
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
		return True

	errors = []
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
		return True


	if VERSION_NUMBER != jsonData["VERSION_NUMBER"]:
		pnt("Saved data from v" + str(jsonData["VERSION_NUMBER"]) + "Current: v" + VERSION_NUMBER)
		upgradeFiles()
	try:
		global stockInfo
		stockInfo = jsonData["stockInfo"]
	except:
		errors.append("stockInfo")
	try:
		global budget
		budget = jsonData["budget"]
	except:
		errors.append("budget")
	try:
		global tradeParams
		tradeParams = jsonData["tradeParams"]
	except:
		errors.append("tradeParams")
	try:
		global oneTime
		oneTime = jsonData["oneTime"]
	except:
		errors.append("oneTime")
	global numAllCompanies
	numAllCompanies = len(stockInfo)

	if len(errors) == 0:
		pntDev("Exited load")
		return False
	else:
		if len(errors) == 4:
			setup(2)
			pntDev("Exited load with multi-data error")
			return True
		for error in errors:
			if error == "stockInfo":
				setup(3)
			if error == "budget":
				setup(4)
			if error == "tradeParams":
				setup(5)
			if error == "oneTime":
				pnt("How the fuck did this error get thrown????????? oneTime failed to load")
				pnt("??????????????????")
		pntDev("Exited load with " + str(errors) + " error")
		return True
#
def mainLoop():
	pntDev("Entered mainLoop")
	global oneTime
	now = datetime.now()
	weekday = now.weekday()
	hour = now.hour
	minute = now.minute
	day = now.day
	month = now.month
	year = now.year
	isTesting = oneTime["testWeekend"] or oneTime["testNewMoney"] or oneTime["testTrade"] or oneTime["testReset"] #only use test variables for wickets

	if (weekday > 4 and not oneTime["weekendCheck"]and not isTesting) or (oneTime["testWeekend"] and not oneTime["testNewMoney"] and not oneTime["testTrade"] and not oneTime["testReset"]): #skip weekends
		pntDev("Weekend")
		pnt("Weekend")
		if defconLevel != 2:
			oneTime["weekendCheck"] = True

	if (day == 1 and not oneTime["refilledCheck"]and not isTesting) or (not oneTime["testWeekend"] and oneTime["testNewMoney"] and not oneTime["testTrade"] and not oneTime["testReset"]): #new money added
		pntDev("Payday")
		pnt("Payday")
		if defconLevel == 0 or defconLevel == 1:
			budget["moneyLeftTotal"] += budget["monthlyBudgetTotal"]
			pntDev("$" + str(budget["monthlyBudgetTotal"]) + " should have been added to brokerage")
		elif defconLevel == 2:
			pntDev("$" + str(budget["monthlyBudgetTotal"]) + " should have been added to brokerage")
			pntDev("No money added")
		pnt("This is on YOU to ensure a recurring deposit exists for this amount of money")
		if defconLevel != 2:
			oneTime["refilledCheck"] = True

	if (weekday <= 4 and hour == 12 and not oneTime["tradeCheck"]and not isTesting) or (not oneTime["testWeekend"] and not oneTime["testNewMoney"] and oneTime["testTrade"] and not oneTime["testReset"]): #trade on weekday at noon
		pntDev("Trade day")
		pnt("Trade day")
		save(not oneTime["testTrade"]) #get new prices only when not testing
		trade()
		if defconLevel != 2:
			oneTime["tradeCheck"] = True

	if (hour == 16 and weekday <= 4 and not oneTime["priceCheck"]and not isTesting) or (not oneTime["testWeekend"] and not oneTime["testNewMoney"] and not oneTime["testTrade"] and oneTime["testReset"]): #reset at 1600 on weekdays
		pntDev("Reset")
		pnt("Reset")
		reset()
		save(False)
		if defconLevel != 2:
			oneTime["priceCheck"] = True

	logout()
	pnt("Program end")
	pntDev("Exited mainLoop")
	if defconLevel != 2:
		pntMajorAction("")
		pntDev("")
def reset():
	pntDev("Entered reset")
	global oneTime
	oneTime["testWeekend"] = False
	oneTime["testTrade"] = False
	oneTime["testNewMoney"] = False
	oneTime["testReset"] = False
	pntDev("Reset oneTime")
	global stockInfo
	try:
		if defconLevel != 2:
			for stock in stockInfo:
				stockInfo[stock]["daysSinceTrade"] += 1
			pntDev("Incremented daysSinceTrade")
		else:
			pntDev("daysSinceTrade not incremented")
	except:
		pntDev("Failed to access daysSinceTrade. Probably because of no data")
		save(True)
		reset()
		return
	pnt("Refilling daily budget  with $" + str(budget["dailyBudgetTotal"]))
	pnt("This is a virtual budget. This program uses money already deposited in your brokerage account. You will need to have a recurring deposit for this program to work")
	if budget["moneyLeftTotal"] < budget["dailyBudgetTotal"]:
		pntMajorAction("Program tried to add $" + str(budget["dailyBudgetTotal"]) + " to daily budget with $" + str(budget["moneyLeftTotal"]) + " remaining in brokerage. Most likely, program was started mid-month, and did not register a deposit of funds")
	else:
		if defconLevel != 2:
			pntDev("moneyLeftDaily refilled with " + str(budget["dailyBudgetTotal"]))
			pntDev("moneyLeftTotal refilled with " + str(budget["dailyBudgetTotal"]))
			budget["moneyLeftDaily"] += budget["dailyBudgetTotal"]
			budget["moneyLeftTotal"] -= budget["dailyBudgetTotal"]
		else:
			pntDev("moneyLeftDaily refilled with " + str(budget["dailyBudgetTotal"]) + " but not really")
			pntDev("moneyLeftTotal refilled with " + str(budget["dailyBudgetTotal"]) + " but not really")

	if budget["moneyLeftTotal"] > budget["monthlyBudgetTotal"] * 1.1: #monthly budget with margin
		pntDev("Added 25% of moneyLeftTotal to moneyLeftDaily because of excess money")
		if defconLevel != 2:
			value = budget["monthlyBudgetTotal"] * 0.25
			budget["moneyLeftDaily"] += value
			budget["moneyLeftTotal"] -= value
		else:
			pntDev("I lied")
	pnt("Money left total: " + str(budget["moneyLeftTotal"]))
	pnt("Money left for tomorrow: " + str(budget["moneyLeftDaily"]))
	pntDev("Exited reset")

if __name__ == "__main__":
	try:
		value = sys.argv[1]
		if value == "setup":
			pntDev("Setup is input arg")
			startup(1)
		elif value == "test":
			pntDev("Test is input arg")
			startup(2)
	except:
		pntDev("No input arg")
		startup(0)
#recommended cronjob timing: 5 12,16 * * *