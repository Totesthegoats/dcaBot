'''
Created on 23 August  2021

@author: Totes
'''
import argparse
import logging
import math
import os
import sys
import time
from typing import Tuple

import tweepy
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

root = logging.getLogger()
log_level = None
FORMAT = "[%(filename).20s:%(lineno).4s - %(funcName).20s] %(levelname)s - %(message)s"
try:
    log_level = os.environ['LOG_LEVEL']
    root.setLevel(log_level)
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(log_level)
except Exception as e:
    log_level = logging.INFO
    root.setLevel(log_level)
    stream = logging.StreamHandler(sys.stdout)
    stream.setLevel(log_level)
    root.info("Log level set by default, value given was not valid")

log = logging.getLogger(__name__)

DCA_TIME_FRAME = {
    "day": 86400,
    "week": 604800,
    "month": 2629746
}


class TwitterApiClient:
    def __init__(self, consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def tweet(self, order):
        self.api.update_status(order)

    def twitterDM(self) -> Tuple:
        # gets the last 10 direct messages
        messages = self.api.list_direct_messages(count=10)
        # set up 3 lists for our variables, this will allow us to get the latest version message we have sent
        amount = []
        time = []
        fiat = []
        # Run a for loop through the message subset,
        # reverse the messages so that you get the last message sent to the bot
        # first
        for message in reversed(messages):
            sender_id = message.message_create["sender_id"]
            if sender_id == "YOURSENDERID":  # you will need to find your own sender ID
                text = message.message_create["message_data"]["text"]
                if "$" in text:  # This will find our buy amount
                    amount.append(text.split("$")[1])
                elif "-" in text:  # this will find our time frame
                    time.append(text.split("-")[1])
                elif "EUR" in text:  # this will find our trading pair
                    fiat.append(text)

        # ensures we get the last message sent, meaning we will be able to change one variable at a time
        dcaAmount = amount[-1]
        timeFrame = time[-1]
        fiatPair = fiat[-1]
        return dcaAmount, timeFrame, fiatPair


class TradingBot:
    def __init__(self, client: Client, twitter_api_client: TwitterApiClient, fiat_pair: str = 'ETHEUR'):
        self.client = client
        self.twitter_api_client = twitter_api_client
        self.fiat_pair = fiat_pair

    def getBalances(self):
        # Makes a request to Biances API for the account balance of what ever you are trading EUR in my case
        # client.API_URL = 'https://testnet.binance.vision/api'
        balance = self.client.get_asset_balance(asset='EUR')  # Change this for your fiat pair
        return balance

    def getMarketPrice(self, tradingPair):
        # This will get the current price for the trading pair that you
        # give the bot at start.
        # client.API_URL = 'https://testnet.binance.vision/api'
        price = self.client.get_symbol_ticker(symbol=tradingPair)
        return price

    def placeBuyOrder(self, quantity, tradingPair):
        # client.API_URL = 'https://testnet.binance.vision/api'
        try:
            order = self.client.create_order(symbol=tradingPair, side='BUY', type='MARKET', quantity=quantity)
            # order = client.create_test_order(symbol=tradingPair, side='BUY', type='MARKET', quantity=quantity)
            toTweet = "Bought " + order["symbol"] + " at " + order["fills"][0]['price']
            self.twitter_api_client.tweet(toTweet)
        except BinanceAPIException as e:
            self.twitter_api_client.tweet(e)
            log.error(e)
        except BinanceOrderException as e:
            self.twitter_api_client.tweet(e)
            log.error(e)
        return

    def trade(self, dca_amount):
        # client.API_URL = 'https://testnet.binance.vision/api'
        try:
            currentPrice = float(self.getMarketPrice(self.fiat_pair)['price'])

            log.info("The current price is for the ", self.fiat_pair, "pair is ", currentPrice)

            getBalance = float(self.getBalances()['free'])

            log.info("The current balance for EUR is ", getBalance)

            symbol_info = self.client.get_symbol_info(self.fiat_pair)
            step_size = 0.0
            for f in symbol_info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])

            if getBalance > 10:
                quantity = dca_amount / currentPrice * 0.995

                precision = int(round(-math.log(step_size, 10), 0))

                quantity = float(round(quantity, precision))

                log.info("buy amount ", quantity)
                self.placeBuyOrder(quantity, self.fiat_pair)
                log.info("The new balance for EUR is ", getBalance)

            else:
                log.info("Insufficient funds, bot will try again in an hour")
                time.sleep(3600)
                self.trade(dca_amount)
        except BinanceAPIException as e:
            self.twitter_api_client.tweet(e)
            log.error(e)


def run(bot: TradingBot, dca_amount: float):
    dcaAmount, timeFrame, fiatPair = bot.twitter_api_client.twitterDM()

    log.info("This bot will check the ballence of your account until "
             "money has been lodged, you must set up standing order yourself.")

    log.info("You have chosen to DCA ", DCA_TIME_FRAME[timeFrame.lower()])
    log.info('Press Ctrl-C to stop.')
    # Change this to your fiat crypto pair

    i = 0
    while True:
        i += 1
        log.info(f"Running bot iteration: {i}")
        bot.trade(dca_amount)  # (buyAmount) if set amount
        log.info(f'Iteration {i}')
        time.sleep(DCA_TIME_FRAME[timeFrame])


def main():
    parser = argparse.ArgumentParser(description='Retrieves command line args for DCA bot')
    parser.add_argument('--binance_api_key', metavar='binance_api_key', required=True,
                        help='binance_api_key')
    parser.add_argument('--binance_api_secret', metavar='binance_api_secret', required=True,
                        help='binance_api_secret')
    parser.add_argument('--dca_amount', metavar='dca_amount', required=True,
                        help='amount to send')

    parser.add_argument('--twitter_consumer_key', metavar='twitter_consumer_key', required=True,
                        help='twitter_consumer_key')
    parser.add_argument('--twitter_consumer_secret', metavar='twitter_consumer_secret', required=True,
                        help='twitter_consumer_secret')
    parser.add_argument('--twitter_access_token', metavar='twitter_access_token', required=True,
                        help='twitter_access_token')
    parser.add_argument('--twitter_access_secret', metavar='twitter_access_secret', required=True,
                        help='twitter_access_secret')
    args = parser.parse_args()
    # setup twitter api client
    log.info("setting up twitter api client")
    twitter_api = TwitterApiClient(args.twitter_consumer_key, args.twitter_consumer_secret,
                                   args.twitter_access_token, args.twitter_access_secret)

    # setup trading bot
    log.info("running trading bot")
    trading_bot: TradingBot = TradingBot(Client(api_key=args.binance_api_key,
                                                api_secret=args.binance_api_secret),
                                         twitter_api, args.fiat_pair)

    # run trading bot
    run(trading_bot, float(args.dca_amount))


if __name__ == '__main__':
    main()
