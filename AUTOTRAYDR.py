import robin_stocks.robinhood as rs
import sys #save terminal to txt
import json #save file
import time #time.sleep reduces CPU usage by waiting N seconds
import os #gets relative filepath
from datetime import datetime #get time

#
cryptoWatched = ['AVAX', 'BTC', 'DOGE', 'ETH', 'SHIB', 'UNI']
stockswatched = ['AMD', 'AMZN', 'ARM', 'AVGO', 'CATX', 'CLSD', 
				'COST', 'CRWD', 'DELL', 'GE', 'GOOGL', 'INTC', 
				'LLY', 'LMT', 'META', 'MSFT', 'MSTR', 'MU', 
				'NFLX', 'NVDA', 'PAA', 'QCOM', 'QQQ', 'SMCI', 
				'TSLA', 'TSM', 'V', 'VINC', 'VOO', 'VOOG', 
				'VUG', 'ZJYL']

#
numAllCompanies = len(stockswatched) + len(cryptoWatched)
lastPriceCrypto = {} #yesterdays price
lastPriceStocks = {}
totalMoneyLeft = 0 #money (including safety margin) in brokerage
moneyLeftCrypto = {} #money accrued for each stock
moneyLeftStocks = {}

#
over = True
loop = True
badLastPrice = False
weekendConsole = False
priceConsole = False
canTrade = True
tradedToday = False #has program already run through trade sequence today
refilledBrokerage = True #added money at start of month

#Constants/Inportant shit
PROGRAM_NAME = "AUTO-TRAYDR Version 0.1 \nThis script by Christopher S \nRobinStocks by Joshua M. Fernandes \nBlah blah blah I am not affiliated with or endorsed by RobinStocks blah blah"
credentials = ['DUMMYUSERNAME', 'DUMMYPASSWORD']
WEEKLY_BUDGET_PER_STOCK = 3.0
MONTHLY_BROKERAGE_PAYMENTS = numAllCompanies * WEEKLY_BUDGET_PER_STOCK * 52
DOLLARS_ADDED_DAILY_TO_EACH_STOCK_ON_WEEKDAYS = WEEKLY_BUDGET_PER_STOCK / 5.0

#
def pntMajorAction(string): #prints sparknotes of what program does when it's active
	file = open("C:/Users/chris 2/Documents/MyFiles/RobinStocks/Summary.txt", "a")
	file.write(pntTime() + "\n")
	file.write(str(string) + "\n")
	file.close()
	pnt(string)
def pntTime(): #prints date and time
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
def pnt(string): #prints to terminal and log file
	file = open("C:/Users/chris 2/Documents/MyFiles/RobinStocks/Log.txt", "a")
	file.write(str(string) + "\n")
	file.close()
	print(string)
def trade():
	pnt(pntTime())
	pnt("Entered trade logic")
	global moneyLeftStocks
	global totalMoneyLeft
	dictionary = rs.account.build_holdings(with_dividends=True)
	for stock in stockswatched:
		try:
			stockPrice = dictionary[stock]
			price = float(stockPrice['price'])
			pc = price / lastPriceStocks[stock]
		except:
			pntMajorAction("ERROR-GETPRICE")
			pntMajorAction("   Could not get price of " + stock)
		wentUp = False
		if pc > 1:
			pc -= 1
			pc *= 100
			wentUp = True
		else:
			pc *= 100
			pc = 100 - pc
		pc = format(pc, '.3f')
		pc = float(pc)
		shoppingCart = 0.0 #money program WANTS to spend on a stock
		buy = True
		if not wentUp:
			if pc > 8.0: #buy $5
				if moneyLeftStocks[stock] > 5.0: #spend ALL of budget if greater than $5
					shoppingCart = moneyLeftStocks[stock]
				else:
					shoppingCart = 5.0
			elif pc > 5.0: #buy $2
				if moneyLeftStocks[stock] * 0.5 > 2.0: #spend half of budget if greater than $2
					shoppingCart = moneyLeftStocks[stock] * 0.5
				else:
					shoppingCart = 2.0
			elif pc > 2.0: #buy $1
				shoppingCart = 1.0
		elif wentUp and pc < 1.0: #buy $1 if less than 1% change, and $10 or more in budget
			if moneyLeftStocks[stock] >= 10.0:
				shoppingCart = 1.0
		elif wentUp and pc > 5.0: #sell $1 if it goes up FAST
			buy = False
		#place orders
		if shoppingCart != 0.0:
			if wentUp:
				pnt("   " + stock + " ^ " + str(pc) + " %    Budget: " + str(moneyLeftStocks[stock]))
			else:
				pnt("   " + stock + " v " + str(pc) + " %    Budget: " + str(moneyLeftStocks[stock]))
			if buy:
				if moneyLeftStocks[stock] < shoppingCart:
					pntMajorAction("   <!> ATTEMPTED TO BUY $" + str(shoppingCart) + " OF " + stock + " WITH $" + str(moneyLeftStocks[stock]))
					continue
				pntMajorAction("   <!> BOUGHT $" + str(shoppingCart) + " OF " + stock)
				moneyLeftStocks[stock] -= shoppingCart
				totalMoneyLeft -= shoppingCart
			else:
				pntMajorAction("   <!> SOLD $" + str(shoppingCart) + " OF " + stock)
				moneyLeftStocks[stock] += shoppingCart
				totalMoneyLeft += shoppingCart
	pnt("   Exited trade logic. Returning to main loop...")
	pass
def reset():
	pnt("Resetting...")
	pnt("   Variables...")
	badLastPrice = False
	weekendConsole = False
	priceConsole = False
	canTrade = True
	tradedToday = False
	pnt("   Refilling stock allowances each with " + DOLLARS_ADDED_DAILY_TO_EACH_STOCK_ON_WEEKDAYS + " ...")
	global moneyLeftStocks
	for stock in stockswatched:
		totalMoneyLeft += DOLLARS_ADDED_DAILY_TO_EACH_STOCK_ON_WEEKDAYS #refill allowance for stocks
		moneyLeftStocks[stock] += DOLLARS_ADDED_DAILY_TO_EACH_STOCK_ON_WEEKDAYS #refill allowance for stocks
		pnt(stock + " " + moneyLeftStocks[stock])
		pass
	pnt("   Total (Including safety margin) " + totalMoneyLeft)
	pnt("   Complete")
	pnt("   Stock-----Equity")
	listEquity = rs.account.build_holdings(with_dividends=True)
	for stock in stockswatched:
		try:
			stockEquity = listEquity[stock]
			equity = stockEquity['equity']
			pnt("   " + str(stock) + "  $" + equity)
		except:
			pnt("   Could not get information for " + stock)
			continue
def startup():
	#fill with dummy data
	for stock in stockswatched: 
		lastPriceStocks[stock] = 0.0
		moneyLeftStocks[stock] = 0.0
	#remove old log
	file = open("C:/Users/chris 2/Documents/MyFiles/RobinStocks/Log.txt", "w")
	file.write("")
	file.close()
	pnt(PROGRAM_NAME)
	pnt("This program allots X amount of money to each stock you list, and will buy when: " + 
		"the price goes down, or when it's budget for a particular stock becomes excessive")
	pnt("")
	pnt("Monthly payments to brokerage: " + str(format(MONTHLY_BROKERAGE_PAYMENTS, '.2f')))
	pnt("Weekly budget per stock: " + str(WEEKLY_BUDGET_PER_STOCK))
	pnt("Daily budget per stock: " + str(DOLLARS_ADDED_DAILY_TO_EACH_STOCK_ON_WEEKDAYS))
	pnt("")
	pntMajorAction("Program start")
	login()
def saveCurrentData(): #grabs current stock prices, then saves. used for overriding dummy data, and updating price at 1600
	pnt("Getting current stock prices...")
	global lastPriceStocks
	dictionary = rs.account.build_holdings(with_dividends=True)
	for stock in stockswatched:
		stockPrice = dictionary[stock]
		price = float(stockPrice['price'])
		lastPriceStocks[stock] = price
	pnt("   Complete")
	save()
def save():
	scriptDir = os.path.dirname(__file__)
	pnt("Saving...")
	try:
		pnt("   Today's stock prices...")
		with open(os.path.join(scriptDir, "lastPriceStocks.txt"), "w") as fp:
			json.dump(lastPriceStocks, fp)

		pnt("   Stock allowances...")
		with open(os.path.join(scriptDir, "moneyLeftStocks.txt"), "w") as fp:
			json.dump(moneyLeftStocks, fp)
		
		pnt("   Total money")
		with open(os.path.join(scriptDir, "totalMoneyLeft.txt"), "w") as fp:
			json.dump(totalMoneyLeft, fp)
		
		pnt("   Complete")
	except:
		pnt("ERROR-SAVING")
		pnt("   Encountered a problem. No idea what could have caused that")
def load():
	scriptDir = os.path.dirname(__file__)
	pnt("Loading...")
	try:
		global lastPriceStocks
		
		pnt("   Today's stock prices...")
		with open(os.path.join(scriptDir, "lastPriceStocks.txt"), "r") as fp:
			lastPriceStocks = json.load(fp)
		global moneyLeftStocks
		
		pnt("   Stock allowances...")
		with open(os.path.join(scriptDir, "moneyLeftStocks.txt"), "r") as fp:
			moneyLeftStocks = json.load(fp)
		global totalMoneyLeft
		
		pnt("   Total money")
		with open(os.path.join(scriptDir, "totalMoneyLeft.txt"), "r") as fp:
			totalMoneyLeft = json.load(fp)
		
		pnt("   Complete")
	except:
		pnt("ERROR-LOADING")
		pnt("   Encountered a problem. Saving all files in case one didn't exist")
		save()
def login():
	global credentials
	credentials = ['DUMMYUSERNAME', 'DUMMYPASSWORD']
	scriptDir = os.path.dirname(__file__)
	relPath = "savedLogin.txt"
	absFilePath = os.path.join(scriptDir, relPath)
	pnt("Fetching saved user/pass...")
	badLogin = False
	while True:
		try:
			if badLogin:
				raise ValueError(" ")
			with open(absFilePath, "r") as fp:
				credentials = json.load(fp)
		except:
			pnt("ERROR-SAVEDLOGIN")
			pnt("   Saved credentials not loaded. Due to file not existing or invalid user/pass")
			pnt("Creating new file...")
			pnt(" ")
			credentials[0] = input("   Username/Email: ")
			credentials[1] = input("   Password: ")
			with open(absFilePath, "w") as fp:
				json.dump(credentials, fp)
			badLogin = False
		pnt("   Complete")
		pnt("Logging in...")
		try:
			login = rs.login(credentials[0], credentials[1])
			badLogin = False
			pnt("   Welcome, " + str(credentials[0]))
			break;
		except:
			pnt("ERROR-INVALIDLOGIN")
			pnt("   Error logging in. Check spelling of your username and password")
			pnt("   User- " + credentials[0])
			pnt("   Pass- " + credentials[1])
			badLogin = True
			pnt("Restarting...")
			pnt(" ")
			#startup()
def mainMenu():
	while True:
		print("Start menu")
		print("a = Start program (Close and relaunch program to view menu again)")
		print("b = Other options go here")
		#
		choice = input(">>> ")
		if choice == "a":
			pnt("Starting program...")
			break;
	pnt("\n")
mainMenu()
startup()
#Main program loop
while loop == True:
	if over == True:
		input("WARNING. OVERRIDE IS ACTIVE. TRADE LOGIC WILL BEGIN WHEN YOU PRESS ENTER. SHUT DOWN PROGRAM NOW")
		pass
	now = datetime.now()
	weekday = now.weekday()
	hour = now.hour
	minute = now.minute
	day = now.day
	month = now.month
	year = now.year
	

	if weekday > 4 and not weekendConsole and not over: #skip weekends
		pnt(pntTime())
		pnt("   Weekend, skipping...")
		weekendConsole = True
		continue
	

	if day == 1 and not refilledBrokerage and not over: #new money added
		pnt(pntTime())
		totalMoneyLeft += MONTHLY_BROKERAGE_PAYMENTS
		pnt("   $500 should have been added to brokerage")
		refilledBrokerage = True


	if (weekday <= 4 and hour == 12 and not tradedToday) or over: #trade on weekday at noon
		pnt(pntTime())
		if tradedToday:
			continue
		pnt("   Able to trade")
		load()
		pnt("   Verifying past data is not dummy data...")
		for stock in stockswatched:
			if lastPriceStocks[stock] == 0.0:
				badLastPrice = True
				pnt("   Last price for " + str(stock) + " is " + str(lastPriceStocks[stock]) + ", which matches dummy data. One moment...")
				canTrade = False
				break;
		if not canTrade:
			pnt("   Entered trade bypass logic")
			tradedToday = True #lock program out for the day
			over = False
			saveCurrentData()
			pnt("   Exited trade bypass logic. Restarting main loop...")
			continue
		pnt("   Complete")
		trade()
		tradedToday = True
		over = False
	

	if hour == 16 and weekday <= 4 and not priceConsole: #update price at 1600 on weekdays
		pnt(pntTime())
		pnt("   Saving prices for percent change tomorrow")
		saveCurrentData()
		priceConsole = True
	

	if hour == 23 and weekday <= 4: #reset at 2300 on weekdays
		pnt(pntTime())
		pnt("   Resetting for next trading day...")
		reset()
		pass
	time.sleep(5.0)
rs.logout()
input("Program ended")
