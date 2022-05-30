import yfinance as yf
import json
from replit import db
import datetime
from datetime import date
import time
import random


#########################
# Portfolio is a list of stocks
# Each stock stored as json in the db
# The key is the stock's ticker
# The value in JSON is formatted as: 
# ticker: {
#     Company: string -> Name of the company the stock represents ownership of
#     Quantity: int   -> quantity of this stock owned
#     Prices: [float] -> list of prices each stock bought for
#     Dates: [Date]   -> date each stock bought
# }
# 
# DB Key: stock:ticker
#########################

#########################
# Database Functions: 
#########################

def getStockInPortfolio(ticker):
    if ("stock:"+ticker) in db.prefix("stock:"):
        stockAsJsonString = db["stock:"+ticker]
        stockAsDict = json.loads(stockAsJsonString)
        return stockAsDict
    return None


def saveStockToDB(ticker, dataAsDict):
    dataAsString = json.dumps(dataAsDict)
    db["stock:"+ticker] = dataAsString


def saveStockToPortfolio(ticker, price, companyName):
    if(("stock:"+ticker) in db.prefix("stock:")):
        data = getStockInPortfolio(ticker)
        data["Quantity"] = int(data["Quantity"]) + 1
        data["Prices"] = data["Prices"] + [price]
        data["Dates"] = data["Dates"]  + [getToday()]
    else: 
        data = {}
        data["Company"] = companyName
        data["Quantity"] = 1
        data["Prices"] = [price]
        data["Dates"] = [getToday()]
    saveStockToDB(ticker, data)


def removeStockFromPortfolio(key, salePrice):
    if key not in db.prefix("stock:"):
        return (None, None)
    ticker = key.split(":")[1]
    data = getStockInPortfolio(ticker)
    purchasePrice = data["Prices"][0]
    buyDate = data["Dates"][0]
    if(data["Quantity"] == 1): # sold last share, remove from db
        del db[key]
    else: #still have shares after sale, update db
        data["Quantity"] = int(data["Quantity"]) - 1
        data["Prices"].pop(0)
        data["Dates"].pop(0)
        saveStockToDB(ticker, data)
    netCash = salePrice - purchasePrice
    daysHeld = dateDifference(buyDate)
    return (netCash, daysHeld)


def getRandomStockFromDB():
    if(len(db.prefix("stock:")) == 0):
        return None, None
    key = random.choice(db.prefix("stock:"))
    ticker = key.split(":")[1]
    stock = getStockInPortfolio(ticker)
    return (key, stock)
  

def updateCashFlow(amount):
    oldNetCash = db["cashflow"]
    newNetCash = oldNetCash + amount #amount is negative on purchase
    db["cashflow"] = newNetCash
    

def getPortfolio():
    output = "Last Trade: " + db["lastTrade"] + "\n"
    output += "Net Cashflow: " + formatNumber(db["cashflow"], True, True) + "\n"
    output += "Stocks I own:\n"
    for key in db.prefix("stock:"):
        if(key == "lastTrade" or key == "cashflow"):
            continue
        ticker = key.split(":")[1]
        stockAsDict = getStockInPortfolio(ticker)
        output += str(stockAsDict["Quantity"]) + " share(s) of " + stockAsDict["Company"] + " (" + ticker.strip() + ")\n" 
    return output


def getNetCashflow():
    cashflow = db["cashflow"]
    return "My current Net Cash Flow is     " + formatNumber(cashflow, True, True)


def getPortfolioValue():
    value = 0.00
    for key in db.prefix("stock:"):
        if(key == "lastTrade" or key == "cashflow"):
            continue
        ticker = key.split(":")[1]
        data = getStockInPortfolio(ticker)
        quantity = data["Quantity"]
        stock = yf.Ticker(ticker)
        price = getCurrentPrice(stock)
        value += (price * quantity) #sum value 
    netWorth = value + db["cashflow"]
    output = "My current Portfolio's Value is " + formatNumber(value, True, True)
    output += "My current Net Worth is            " + formatNumber(netWorth, True, True)
    return output


def getPortfolioWithValue():
    output = "Last Trade:         " + db["lastTrade"] + "\n"
    output += "Net Cashflow:    " + formatNumber(db["cashflow"], True, True) + "\n"
    value = 0.00
    stockList = ""
    for key in db.prefix("stock:"):
        if(key == "lastTrade" or key == "cashflow"):
            continue
        ticker = key.split(":")[1]
        stockAsDict = getStockInPortfolio(ticker)
        quantity = stockAsDict["Quantity"]
        stock = yf.Ticker(ticker)
        price = getCurrentPrice(stock)
        stockList += str(quantity) + " share(s) of " + stockAsDict["Company"] + " (" + ticker.strip() + ") currently valued at " + formatNumber(price, True, False) + "\n" 
        value += (price * quantity)
    netWorth = value + db["cashflow"]
    output += "Portfolio Value: " + formatNumber(value, True, True) + "\n"
    output += "Net Worth:        " + formatNumber(netWorth, True, True) + "\n"
    output += "Stocks I own:\n"
    output += stockList
    return output
  

def resetDB():
    for key in db.prefix("stock:"):
        del db[key]
    db["cashflow"] = 0.00
    db["lastTrade"] = getToday()


def printDB():
    for key in db.keys():
        print(key + ": " + str(db[key]))

#########################
# Stock functions: 
#########################

def getCurrentPrice(stock):
    info = stock.info
    currentPrice = info["currentPrice"]
    return float(currentPrice)


def getCompanyName(stock):
    info = stock.info
    name = info["shortName"]
    return name


def getStockInfo(stock):
    info = stock.info
    infoKeys = ["shortName", "sector", "longBusinessSummary", "volume", "trailingPE", "marketCap", "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "averageVolume", "dividendYield", "beta", "trailingEps"]
    companyInfo = ""
    for key in infoKeys:
        try: 
            keyString = formatStockInfoKey(key)
            valueString = formatStockInfoValue(info, key)
            companyInfo += keyString + ": " + valueString + "\n"
        except: 
            pass
    return companyInfo


def formatStockInfoKey(key):
    if(key == "shortName"):
        return "Company"
    if(key == "longBusinessSummary"):
        return "Business Summary"
    if(key == "trailingPE"):
        return "Price-Earnings Ratio"
    if(key == "marketCap"):
        return "Market Cap"
    if(key == "fiftyTwoWeekHigh"):
        return "52 Week High"
    if(key == "fiftyTwoWeekLow"):
        return "52 Week Low"
    if(key == "averageVolume"):
        return "Average Volume"
    if(key == "dividendYield"):
        return "Dividend Yield"
    if(key == "trailingEps"):
        return "Earnings Per Share"
    return key.capitalize()


def formatStockInfoValue(info, key):
    if(key == "longBusinessSummary"):
        summary = str(info[key].split(".")[0]) + "."
        if(len(summary) > 150):
            summary = summary[:147] + "..."
        return summary
    if(key == "trailingPE"):
        return formatNumber(info[key], True, False)
    if(key == "volume"):
        return formatNumber(info[key], False, False)
    if(key == "marketCap"):
        return formatNumber(info[key], True, False)
    if(key == "fiftyTwoWeekHigh"):
        return formatNumber(info[key], True, False)
    if(key == "fiftyTwoWeekLow"):
        return formatNumber(info[key], True, False)
    if(key == "averageVolume"):
        return formatNumber(info[key], False, False)
    if(key == "fiftyTwoWeekLow"):
        return formatNumber(info[key], True, False)
    if(key == "dividendYield"):
        yieldAsFloat = float(info[key]) * 100
        return formatNumber(yieldAsFloat, False, False) + "%"
    if(key == "trailingEps"):
        return formatNumber(info[key], True, False)
    return str(info[key])


def getRandomStockTicker():
    f = open("nasdaq_stocks.csv")
    list_of_tickers = f.readlines()
    f.close()
    return random.choice(list_of_tickers)


#########################
# Utility functions
#########################

# returns current date in PST
def getToday():
  hour = int(time.localtime(time.time())[3])
  today = date.today()
  if(hour < 8): #midnight PST at 8am UTC
      today = today - datetime.timedelta(1)
  return str(today)


def dateDifference(otherDateStr):
    otherDate = datetime.datetime.strptime(otherDateStr,"%Y-%m-%d" )
    todayStr = getToday()
    today = datetime.datetime.strptime(todayStr,"%Y-%m-%d" )
    delta = today - otherDate
    return delta.days


def formatNumber(number: float, dollar = True, plusSign = True):
    sign = ""
    if(number < 0):
        sign = "-" 
    elif(plusSign):
        sign = "+"
    value = abs(number)
    formatString = "{:,}" #add commas
    if(value >= 0.01 or value == 0.0): #round to the penny
        value = round(value, 2)
        formatString = "{:,.2f}" #print exactly two decimal 
    dollarSign = ""
    if(dollar):
        dollarSign = "$"
    return sign + dollarSign + formatString.format(value) 
    

#########################
# Buy or Sell functions: 
#########################

def buyStock():
    stock = None
    while stock is None:
        ticker = getRandomStockTicker()
        stock = yf.Ticker(ticker)
        try: 
            companyName = getCompanyName(stock)
            currentPrice = getCurrentPrice(stock)
            if companyName is None or currentPrice is None:
                stock = None
        except:  #can't use stock, invalid data
            stock = None
    updateCashFlow(-currentPrice)
    saveStockToPortfolio(ticker, currentPrice, companyName)
    message = "buy one stock of " + companyName + " (" + ticker + ") for " + formatNumber(currentPrice, True, False) + "\n\n"
    message += "Company Info:\n"
    message += getStockInfo(stock)
    return message


def sellStock():
    key, stock = getRandomStockFromDB()
    if(key == None):
        return "ERROR: NO stocks in DB"
    currentPrice = getCurrentPrice(yf.Ticker(key.split(":")[1]))
    updateCashFlow(currentPrice)
    netCash, daysHeld = removeStockFromPortfolio(key, currentPrice)
    message = "sell one stock of " + stock["Company"] + " for " + formatNumber(currentPrice, True, False) + "\n\n"
    message += "I held the stock for " + str(daysHeld) + " days and net " + formatNumber(netCash, True, True) + "\n"
    return message
  
#########################
# Daily Trade Functions
#########################
  
def dailyTrade():
    if(len(db.prefix("stock:")) == 0):
        # no stocks owned, buy one
        return buyStock()
    # flip a coin
    num = random.randint(1, 3) #exclusive upper bound
    if(num == 1):
        return buyStock()
    else: 
        return sellStock()


async def tryDailyTrade(force = "No"): 
    if(db["lastTrade"] == getToday() and force != "Yes"): #already made a trade today
        return False
    hour = int(time.localtime(time.time())[3])
    if(hour < 15 and force != "Yes"): #don't trade before 8AM PST or after 4PM PST
        return False
    channel = bot.get_channel() #daily-trade
    message = "Hello fellow traders!\n\nAfter looking through infinitely many possible futures, for my daily trade today I have decided to "
    message += dailyTrade()
    message += "\n" + getNetCashflow()
    message += "\n" + getPortfolioValue()
    msg = await channel.send(message) 
    await msg.add_reaction('\U0001F4C8') #up chart
    await msg.add_reaction('\U0001F4C9') #down chart
    db["lastTrade"] = getToday() #success, update last trade date
    return True
  
  
#########################
# Testing
#########################


# print(str(getToday()))
# resetDB()
# print(buyStock())
# print(printDB())
# print("*****")
# print(buyStock())
# print(getPortfolio())
# print(printDB())
# print("*****")
# print(sellStock())
# print(getPortfolio())
# print(getNetCashflow())
# print(printDB())
# resetDB()

# ticker = getRandomStockTicker()

# print(str(getToday()))

# stock = yf.Ticker("MSFT")

# print(getStockInfo(stock))

# print(getCurrentPrice(stock))

#########################
# Discord Setup
#########################

import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from flask import Flask
from threading import Thread
from itertools import cycle

app = Flask('')

@app.route('/')
def main():
  return "Your Bot Is Ready"


def run():
  app.run(host="0.0.0.0", port=8000)


def keep_alive():
  server = Thread(target=run)
  server.start()


load_dotenv('secret.env')
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='$')

status = cycle(['with Python','JetHub'])

@bot.event
async def on_ready():
  change_status.start()
  called_hourly.start()
  print("Your bot is ready")


@tasks.loop(hours=1)
async def change_status():
    await bot.change_presence(activity=discord.Game("the Stock Market"))
  

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)


#########################
# Discord Commands
#########################

@bot.command(name='stock', help="Responds with information about a given stock ticker")
async def stockInformation(ctx, ticker):
    try: 
        stock = yf.Ticker(ticker)
        response = "Ticker: " + ticker + "\n"
        response += "Current Price: " + formatNumber(getCurrentPrice(stock), True, False) + "\n"
        response += getStockInfo(stock)
        await ctx.send(response)
    except: 
        await ctx.send("Invalid stock ticker")


@bot.command(name='price', help="Responds with the current price for a given stock ticker")
async def stockPrice(ctx, ticker):
    try: 
        stock = yf.Ticker(ticker)
        response = "The current price of " + ticker + " is " + formatNumber(getCurrentPrice(stock), True, False) + "\n"
        await ctx.send(response)
    except: 
        await ctx.send("Invalid stock ticker")



@bot.command(name='portfolio', help="Responds with information about the bot's current portfolio from its daily trading")
async def portfolio(ctx):
    response = getPortfolio()
    await ctx.send(response)


@bot.command(name='portfolioValue', help="Responds with bot's current portfolio with the current market value of shares owned and total portfolio value")
async def portfolioValue(ctx):
    response = getPortfolioWithValue()
    await ctx.send(response)


@bot.command(name='cashflow', help="Responds with the bot's current net cashflow from its daily trading")
async def cashflow(ctx):
    response = getNetCashflow()
    await ctx.send(response)


@commands.has_role("Retard")
@bot.command(name='doDailyTrade', help="Responds with information about a given stock ticker")
async def doDailyTrade(ctx, force = "No"):
    success = await tryDailyTrade(force)
    if not success:
        await ctx.send("Failed to do a daily trade")


@commands.has_role("Retard")
@bot.command(name='resetPortfolio', help="Resets portfolio by dropping all stocks and resetting net cash flow. Must pass YES as argument to confirm")
async def resetPortfolio(ctx, confirmation):
    if(confirmation == "YES"):
        resetDB()
  

#########################
# Discord Daily Timer
#########################

@tasks.loop(hours=3)
async def called_hourly():
    await tryDailyTrade()


@called_hourly.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")


# Run Discord Bot:
main()
keep_alive()
bot.run(TOKEN)