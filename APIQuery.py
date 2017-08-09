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

# Api Key Strings
_K_CURR_ = 'XETHZUSD'
_ADD_ORDER_ = 'AddOrder'
_PAIR_ = 'pair'
_TYPE_ = 'type'
_ETH_CURRENCY_ = 'ETHUSD'
_LEVERAGE_ = 'leverage'
_BUY_ = 'buy'
_SELL_ = 'sell'
_LIMIT_ = 'limit'
_STOP_LOSS_LIMIT_ = 'stop-loss-limit'
_ORDER_TYPE_ = 'ordertype'
_PRICE_ = 'price'
_PRICE_2_ = 'price2'
_VOLUME_ = 'volume'
_EXPIRETM_ = 'expiretm'
_RESULT_ = 'result'
_TXID_ = 'txid'
_CANCEL_ORDER_ = 'CancelOrder'
_DEPTH_ = 'Depth'
_COUNT_ = 'count'
_BIDS_ = 'bids'
_ASKS_ = 'asks'
_OPEN_POSITIONS_ = 'OpenPositions'
_QUERY_ORDERS_ = 'QueryOrders'
_STATUS_ = 'status'
_CLOSED_ = 'closed'

# API Values
_LEVERAGE_VALUE_ = 4
_EXPIRETM_VALUE_ = '+600'
_COUNT_VALUE_ = '10'

_LIMIT_PRICE_DIFF_ = 0.5
_STOP_LOSS_PRICE_DIFF_ = 1.5

# constant variables for price checking and trading:
tradeVol = (availablecapital/GDAXPrice())
_TRADE_VOLUME_ = tradeVol
posTradePriceGap = 1.2
negTradePriceGap = -1.2
tradeCounter = 0
madeTrade = False

#def __init__ (key,secret,conn):
    # better and more secure to use k.load_key('path to txt file with key')
    #self.key = vLpfAS8iwTrZ8G1iifZzHi9jJ4FtnPFgJPj606l2gQG/JufNub+POY9c
    #self.secret = 'hTafJRP8ON8+uqRR6B1Jn5XraoqR8U+q7/x7cF4MVGLhUJOfBDnh3LRnBo0imKhQoSqxkldhGv3DzPLvKNCsOg=='
    #self.conn = c

def krakenPrice():
    firstPrice_Kraken = k.query_public(_DEPTH_, {_PAIR_: kcurr, _COUNT_: _COUNT_VALUE_})
    #get ask and bid, average and return number
    bestbid = float(firstPrice_Kraken[_RESULT_][_K_CURR_][_BIDS_][0][0])
    bestask = float(firstPrice_Kraken[_RESULT_][_K_CURR_][_ASKS_][0][0])
    return (bestask+bestbid)/2

def GDAXPrice():
    orderbook = GDAXpublic_client.get_product_order_book(gcurr, level=1)
    #this probably won't work but worth a short
    bestbid = float(orderbook[_BIDS_][0][0])
    bestask = float(orderbook[_ASKS][0][0])
    return (bestask+bestbid)/2

#def bitfinexPrice():
#    return BFXpublic_client.ticker(ETHUSD)['last_trade']


def kraken_minus_gdax():
    return krakenPrice() - GDAXPrice()

def positionsClosed():
# potential better/safer way to do this is to get trade ID from ledger, then      #
# check if position with that ID is closed. However would cost 2 pts instead of 0 #
    return mainTXID == '' or len(k.query_private(_OPEN_POSITIONS_)[_RESULT_]) == 0


def checkClose():
    order = k.query_private(_QUERY_ORDERS_, {_TXID_: closeTXID})
    #if trade has closed, return True

    return order[_RESULT_][closeTXID][_STATUS_] == _CLOSED_

def checkStopLoss():
    order = k.query_private(_QUERY_ORDERS_, {_TXID_: stoplossTXID})
    #if trade has closed, return True
    return order[_RESULT_][stoplossTXID][_STATUS_] == _CLOSED_

def trade(direction,price,volume):
    return k.query_private(_ADD_ORDER_,{
        _PAIR_: _ETH_CURRENCY_,
        _TYPE_: direction,
        _ORDER_TYPE_: _LIMIT_,
        _PRICE_: price,
        _VOLUME_: volume,
        _LEVERAGE_: _LEVERAGE_VALUE_
    })

def main_position_trade(direction,avg_price,volume):
    if direction not in [_BUY_,_SELL_]:
        raise Exception('Invalid parameter')
    if volume < 1:
        raise Exception('Invalid volume')
    # Check the validity of params

    if direction == 'buy':
        price += _LIMIT_PRICE_DIFF_
    else: # Must be a sell
        price -= _LIMIT_PRICE_DIFF_

    return trade(direction,price,volume)

def close_position_trade(direction,price,volume):
    if direction not in [_BUY_,_SELL_]:
        raise Exception('Invalid parameter')
    if volume < 1:
        raise Exception('Invalid volume')

    return trade(direction,price,volume)

def stop_loss_trade(direction,price,trade_volume):
    if direction not in [_BUY_,_SELL_]:
        raise Exception('Invalid parameter')
    if volume < 1:
        raise Exception('Invalid volume')

    if direction == 'buy':
        price += _STOP_LOSS_PRICE_DIFF_
    else: # Must be a sell
        price -= _STOP_LOSS_PRICE_DIFF_

    return k.query_private(_ADD_ORDER_, { _PAIR_: _ETH_CURRENCY_,
                                  _TYPE_: direction,
                                  _ORDER_TYPE_: _STOP_LOSS_LIMIT_,
                                  _PRICE_: price,
                                  _PRICE_2_: price,
                                  _VOLUME_: trade_volume,
                                  _LEVERAGE_: _LEVERAGE_VALUE_,
                                  _EXPIRETM_: _EXPIRETM_VALUE_,
                                 # 'validate': 'True'
                                  })

def make_trade(direction):
    if direction == _BUY_:
        opp_direction = _SELL_
    else: # Must be _SELL_
        opp_direction = _BUY_

    mainposition = main_position_trade(direction,krakenPrice(),_TRADE_VOLUME_)
    # order that position should close at
    closeposition = close_position_trade(opp_direction,GDAXPrice(),_TRADE_VOLUME_)
    # stop loss that expires in 10 mins after placed
    stoploss = stop_loss_trade(opp_direction,krakenPriceAvg,_TRADE_VOLUME_)

    mainTXID = mainposition[_RESULT_][_TXID_][0]
    closeTXID = closeposition[_RESULT_][_TXID_][0]
    stoplossTXID = stoploss[_RESULT_][_TXID_][0]

def closeExtraOrders():
    #checks if position has closed, and cancels other open order
    if closeTXID != '' and checkClose():
        k.query_private(_CANCEL_ORDER_, {stoplossTXID})
    if stoplossTXID != '' and checkStopLoss():
        k.query_private(_CANCEL_ORDER_, {closeTXID})

def makeTrade():

    # gets Kraken and GDAX price, then computes difference. If difference #
    # is above the threshhold to trade, then makes use of either posTrade #
    # or negTrade to open a position with stop loss and a closing price   #


    if kraken_minus_gdax() <= negTradePriceGap and positionsClosed():
        #tradeCounter+=1
        print('Making trade...')
        print(make_trade(_BUY_))
        madeTrade = True
    elif kraken_minus_gdax() >= posTradePriceGap and positionsClosed():
        #tradeCounter+=1
        print(make_trade(_SELL_))
        madeTrade = True

    # -TODO- print PNL after order is closed

if __name__ == '__main__':
    while True:
        print('Price Difference: ' + str(kraken_minus_gdax()))
        makeTrade()
        closeExtraOrders()
        if madeTrade == True:
            print('Trade #' + tradeCounter + ' has been made')
        time.sleep(4)
