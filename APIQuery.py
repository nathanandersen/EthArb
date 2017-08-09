import krakenex #pip install krakenex
import time
import gdax #pip install gdax
#import bitfinex.client #pip install git+git://github.com/streblo/bitfinex-python-client.git
#why doesnt this work ^
#gives error: Command "python setup.py egg_info" failed with error code 1 in /private/tmp/pip-93bybdva-build/
#

#for Kraken
k = krakenex.API()
k.load_key('kraken.key')
c = krakenex.Connection()

#for GDAX
GDAXpublic_client = gdax.PublicClient()

#for Bitfinex
#BFXpublic_client = bitfinex.client.Public()

# initialization:
kcurr = 'XETHZUSD'
gcurr = 'ETH-USD'
availablecapital = 100

# transaction IDs for closing extra trades:
mainTXID = ''
closeTXID = ''
stoplossTXID = ''


#def __init__ (key,secret,conn):
    # better and more secure to use k.load_key('path to txt file with key')
    #self.key = vLpfAS8iwTrZ8G1iifZzHi9jJ4FtnPFgJPj606l2gQG/JufNub+POY9c
    #self.secret = 'hTafJRP8ON8+uqRR6B1Jn5XraoqR8U+q7/x7cF4MVGLhUJOfBDnh3LRnBo0imKhQoSqxkldhGv3DzPLvKNCsOg=='
    #self.conn = c

def krakenPrice():
    firstPrice_Kraken = k.query_public('Depth', {'pair': kcurr, 'count': '10'})
    #get ask and bid, average and return number
    bestbid = float(firstPrice_Kraken['result']['XETHZUSD']['bids'][0][0])
    bestask = float(firstPrice_Kraken['result']['XETHZUSD']['asks'][0][0])
    return (bestask+bestbid)/2

def GDAXPrice():
    orderbook = GDAXpublic_client.get_product_order_book(gcurr, level=1)
    #this probably won't work but worth a short
    bestbid = float(orderbook['bids'][0][0])
    bestask = float(orderbook['asks'][0][0])
    return (bestask+bestbid)/2

#def bitfinexPrice():
#    return BFXpublic_client.ticker(ETHUSD)['last_trade']

# constant variables for price checking and trading:
avgExchangesPrice = GDAXPrice()
tradeVol = (availablecapital/avgExchangesPrice)
posTradePriceGap = 1.2
negTradePriceGap = -1.2
tradeCounter = 0
madeTrade = False


def realPriceGap():
    return krakenPrice() - GDAXPrice()

def positionsClosed():
# potential better/safer way to do this is to get trade ID from ledger, then      #
# check if position with that ID is closed. However would cost 2 pts instead of 0 #
    if (mainTXID == ''):
        return True
    elif (len(k.query_private('OpenPositions')['result']) == 0):
        noPositions = True
        return noPositions

def gapDirection():
    if realPriceGap() >= posTradePriceGap:
        return 1 # kraken higher than GDAX, so sell short
    elif realPriceGap() <= negTradePriceGap:
        return 0 # kraken lower than GDAX, so buy long


def checkClose():
    order = k.query_private('QueryOrders', {'txid': closeTXID})
    #if trade has closed, return True
    if (order['result'][closeTXID]['status'] == 'closed'):
        return True
    else: return False

def checkStopLoss():
    order = k.query_private('QueryOrders', {'txid': stoplossTXID})
    #if trade has closed, return True
    if (order['result'][stoplossTXID]['status'] == 'closed'):
        return True
    else: return False

def posTrade():
    # buy at best-ish Kraken price
    mainposition = k.query_private('AddOrder', { 'pair': 'ETHUSD',
                                  'type': 'buy',
                                  'ordertype': 'limit',
                                  'price': (krakenPriceAvg + .5),
                                  'volume': (tradeVol),
                                  'leverage': 4 })
    mainTXID = mainposition['result']['txid'][0]
    # order that position should close at
    closeposition = k.query_private('AddOrder', {'pair': 'ETHUSD',
                                                 'type': 'sell',
                                                 'ordertype': 'limit',
                                                 'price': avgExchangesPrice,
                                                 'volume': tradeVol,
                                                 'leverage': 4 })
    closeTXID = closeposition['result']['txid'][0]
    # stop loss that expires in 10 mins after placed
    stoploss = k.query_private('AddOrder', { 'pair': 'ETHUSD',
                                  'type': 'sell',
                                  'ordertype': 'stop-loss-limit',
                                  'price': (krakenPriceAvg - 1.5),
                                  'price2': (krakenPriceAvg - 1.5),
                                  'volume': tradeVol,
                                  'leverage': 4,
                                  'expiretm': '+600',
                                 # 'validate': 'True'
                                  })
    mainTXID = mainposition['result']['txid'][0]
    closeTXID = closeposition['result']['txid'][0]
    stoplossTXID = stoploss['result']['txid'][0]

def negTrade():
    # short at best-ish Kraken price
    mainposition = k.query_private('AddOrder', { 'pair': 'ETHUSD',
                                  'type': 'sell',
                                  'ordertype': 'limit',
                                  'price': (krakenPrice() - .5),
                                  'volume': (tradeVol),
                                  'leverage': 4 })

    # order that position should close at
    closeposition = k.query_private('AddOrder', {'pair': 'ETHUSD',
                                                 'type': 'buy',
                                                 'ordertype': 'limit',
                                                 'price': avgExchangesPrice,
                                                 'volume': tradeVol,
                                                 'leverage': 4 })

    # stop loss that expires in 10 mins after placed
    stoploss = k.query_private('AddOrder', { 'pair': 'ETHUSD',
                                  'type': 'buy',
                                  'ordertype': 'stop-loss-limit',
                                  'price': (krakenPrice() + 1.5),
                                  'price2': (krakenPrice() + 1.5),
                                  'volume': tradeVol,
                                  'leverage': 4,
                                  'expiretm': '+600',
                                 # 'validate': 'True'
                                  })
    mainTXID = mainposition['result']['txid'][0]
    closeTXID = closeposition['result']['txid'][0]
    stoplossTXID = stoploss['result']['txid'][0]

def closeExtraOrders():
    #checks if position has closed, and cancels other open order
    if (closeTXID != ''):
        if (checkClose() == True):
            k.query_private('CancelOrder', {stoplossTXID})
    if (stoplossTXID != ''):
        if (checkStopLoss() == True):
            k.query_private('CancelOrder', {closeTXID})

def makeTrade():

    # gets Kraken and GDAX price, then computes difference. If difference #
    # is above the threshhold to trade, then makes use of either posTrade #
    # or negTrade to open a position with stop loss and a closing price   #

    if ((gapDirection() == 0) & (positionsClosed() == True)):
        #tradeCounter+=1
        print('Making trade...')
        print(posTrade())
        madeTrade = True
    elif (gapDirection() == 1 & positionsClosed() == True):
        #tradeCounter+=1
        print(negTrade())
        madeTrade = True

    # -TODO- print PNL after order is closed

if __name__ == '__main__':
    while True:
        print('Price Difference: ' + str(realPriceGap()))
        makeTrade()
        closeExtraOrders()
        if madeTrade == True:
            print('Trade #' + tradeCounter + ' has been made')
        time.sleep(4)
