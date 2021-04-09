'''
Created on 30 March 2021

@author: Totes
'''

from itertools import count
import time
import math
import tweepy
import os
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

#real API
api_key  =  os.environ.get('binance_api')
print(api_key)
#
secretKey =  os.environ.get('binance_secret')
print(secretKey)

#Test API keys
#api_key  = testKey

#secretKey =  sTestKey

client = Client(api_key, secretKey)

def tweet(order):
    auth = tweepy.OAuthHandler("CONSUMER_KEY", "CONSUMER_SECRET")
    auth.set_access_token("ACCESS_TOKEN", "ACCESS_TOKEN_SECRET")

    api = tweepy.API(auth)

    api.update_status(order)

def getAllOrdrs(tradingPair):
    #client.API_URL = 'https://testnet.binance.vision/api'
    orders = client.get_all_orders(symbol=tradingPair)
    return orders

def getRecentTrades(tradingPair):
    #client.API_URL = 'https://testnet.binance.vision/api'
    trades = client.get_recent_trades(symbol=tradingPair)
    return trades

def getBalances():
    # Makes a request to Biances API for the account balance of what ever you are trading EUR in my case
    #client.API_URL = 'https://testnet.binance.vision/api'
    balance = client.get_asset_balance(asset = 'EUR')
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

def placeSellOrder(price, tradingPair):
    #client.API_URL = 'https://testnet.binance.vision/api'
    order = client.create_order(symbol=tradingPair, side='SELL', type='MARKET', quantity=100)
    return(order)


def cancleOrders():
    #client.API_URL = 'https://testnet.binance.vision/api'
    print(client.get_open_orders())
    for row in client.get_open_orders():
        client.cancel_order(symbol=row["symbol"], orderId=row['orderId'])
    print(client.get_open_orders())

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
    timeFrame = input("Enter DCA time frame (day, week, month):" )
    dcaTimeFrame = {
        "day": 86400,
        "week": 604800,
        "month": 2629746
    }
    print("This bot will check the ballence of you account until money has been lodged, you must set up standing order yourself.")

    dcaAmount = float(input("Enter how much you want to buy in fiat:"))

    print("You have chosen to DCA ", dcaTimeFrame[timeFrame.lower()])
    print('Press Ctrl-C to stop.')
    # Change this to your fiat crypto pair
    fiatPair = 'ETHEUR'


    for i in count():
        dcaBot(fiatPair, dcaAmount) #(buyAmount) if set amount
        print(f'Iteration {i}')
        time.sleep(dcaTimeFrame[timeFrame])