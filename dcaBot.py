'''
Created on 23 August  2021

@author: Totes
'''

import time
import math
import tweepy
import os
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

#real API
api_key  =  os.environ.get('binance_api') # OR add your API KEY here

secretKey =  os.environ.get('binance_secret') # OR add your API SecretKey here

auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")
api = tweepy.API(auth)
#Test API keys
#api_key  = testKey

#secretKey =  sTestKey

client = Client(api_key, secretKey)

# def getAllOrdrs(tradingPair):
#     #client.API_URL = 'https://testnet.binance.vision/api'
#     orders = client.get_all_orders(symbol=tradingPair)
#     return orders

# def getRecentTrades(tradingPair):
#     #client.API_URL = 'https://testnet.binance.vision/api'
#     trades = client.get_recent_trades(symbol=tradingPair)
#     return trades

# def placeSellOrder(price, tradingPair):
#     #client.API_URL = 'https://testnet.binance.vision/api'
#     order = client.create_order(symbol=tradingPair, side='SELL', type='MARKET', quantity=100)
#     return(order)


# def cancleOrders():
#     #client.API_URL = 'https://testnet.binance.vision/api'
#     print(client.get_open_orders())
#     for row in client.get_open_orders():
#         client.cancel_order(symbol=row["symbol"], orderId=row['orderId'])
#     print(client.get_open_orders())

def tweet(order):
    api.update_status(order)

def twitterDM():
  # gets the last 10 direct messages
  messages = api.list_direct_messages(count=10)
  # set up 3 lists for our variables, this will allow us to get the latest version message we have sent
  amount = []
  time = []
  fiat = []
  # Run a for loop through the message subset, reverse the messages so that you get the last message sent to the bot first
  for message in reversed(messages):
    sender_id = message.message_create["sender_id"]
    if sender_id == "YOURSENDERID": #you will need to find your own sender ID
      text = message.message_create["message_data"]["text"]
      if "$" in text: # This will find our buy amount
        amount.append(text.split("$")[1])
      elif "-" in text: # this will find our time frame
        time.append(text.split("-")[1])
      elif "EUR" in text: #  this will find our trading pair
        fiat.append(text)

  # ensures we get the last message sent, meaning we will be able to change one variable at a time
  dcaAmount = amount[-1]
  timeFrame = time[-1]
  fiatPair = fiat[-1]
  return dcaAmount, timeFrame, fiatPair

def getBalances():
    # Makes a request to Biances API for the account balance of what ever you are trading EUR in my case
    #client.API_URL = 'https://testnet.binance.vision/api'
    balance = client.get_asset_balance(asset = 'EUR') # Change this for your fiat pair
    return balance

def getMarketPrice(tradingPair):
    # This will get the current price for the trading pair that you
    # give the bot at start.
    #client.API_URL = 'https://testnet.binance.vision/api'
    price = client.get_symbol_ticker(symbol=tradingPair)
    return price

def placeBuyOrder(quantity, tradingPair):
    #client.API_URL = 'https://testnet.binance.vision/api'
    try:
        order = client.create_order(symbol=tradingPair, side='BUY', type='MARKET', quantity=quantity)
        #order = client.create_test_order(symbol=tradingPair, side='BUY', type='MARKET', quantity=quantity)
        toTweet = "Bought " + order["symbol"] +  " at "+  order["fills"][0]['price']
        tweet(toTweet)
    except BinanceAPIException as e:
        tweet(e)
        print(e)
    except BinanceOrderException as e:
        tweet(e)
        print(e)
    return


def dcaBot(tradingPair, dcaAmount):
    #client.API_URL = 'https://testnet.binance.vision/api'
    try:
        currentPrice = float(getMarketPrice(tradingPair)['price'])

        print("The current price is for the ", tradingPair, "pair is ",  currentPrice)

        getBalance = float(getBalances()['free'])

        print("The current balance for EUR is ",  getBalance)

        symbol_info = client.get_symbol_info(tradingPair)
        step_size = 0.0
        for f in symbol_info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])

        if getBalance > 10:
            quantity = dcaAmount / currentPrice * 0.995

            precision = int(round(-math.log(step_size, 10), 0))

            quantity = float(round(quantity, precision))

            print("buy amount ", quantity)
            placeBuyOrder(quantity, tradingPair)
            print("The new balance for EUR is ", getBalance)

        else:
            print("Inceficent funds, bot will try again in an hour")
            time.sleep(3600)
            dcaBot(tradingPair, dcaAmount)
    except BinanceAPIException as e:
        tweet(e)
        print(e)

if __name__ == '__main__':

    dcaAmount, timeFrame, fiatPair = twitterDM()
    dcaTimeFrame = {
        "day": 86400,
        "week": 604800,
        "month": 2629746
    }
    print("This bot will check the ballence of your account until money has been lodged, you must set up standing order yourself.")

    print("You have chosen to DCA ", dcaTimeFrame[timeFrame.lower()])
    print('Press Ctrl-C to stop.')
    # Change this to your fiat crypto pair

    for i in count():
        dcaBot(fiatPair, dcaAmount) #(buyAmount) if set amount
        print(f'Iteration {i}')
        time.sleep(dcaTimeFrame[timeFrame])
