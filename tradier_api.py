from tradier_pwd import *
import requests
import numpy
import pandas as pd
from pandas.io.json import json_normalize
#from datetime import datetime, timedelta, timezone
import datetime
import math
import pytz
from system_utils import *
import json
import math
#from sim_data import positions_response

eastern = pytz.timezone('US/Eastern')
sandbox = False
EXECUTE_TRADE = False


if sandbox:
    quotes_url = 'https://sandbox.tradier.com/v1/markets/quotes'
    optionchain_url = 'https://sandbox.tradier.com/v1/markets/options/chains'
    expirations_url = 'https://sandbox.tradier.com/v1/markets/options/expirations'
else:
    quotes_url = 'https://api.tradier.com/v1/markets/quotes'
    optionchain_url = 'https://api.tradier.com/v1/markets/options/chains'
    expirations_url = 'https://api.tradier.com/v1/markets/options/expirations'
    orderexec_url = 'https://api.tradier.com/v1/accounts/'+ account_id +'/orders'
    timesales_url = 'https://api.tradier.com/v1/markets/timesales'
    positions_url = 'https://api.tradier.com/v1/accounts/'+ account_id +'/positions'
    gains_url     = 'https://api.tradier.com/v1/accounts/'+account_id+'/gainloss'
    history_url = 'https://api.tradier.com//v1/markets/history'

def get_all_open_positions(symbol = None):
    try:
        response = requests.get(positions_url,
            params={},
            headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
        )
        json_response = response.json()
        #print(json_response)
        #Sim
        #json_response = positions_response
        
        if json_response['positions'] != 'null':
            
            data = json_response['positions']['position']
            if isinstance(data, dict): #single element
                df = pd.DataFrame({k: [v] for k, v in data.items()})
            else:
                df = pd.DataFrame.from_dict(data)

            current_prices = []
            for index, row in df.iterrows():
                option_symbol   = row['symbol']
                qty             = row['quantity']
                current_price = get_option_quote(option_symbol)['mid_raw']*100
                current_prices.append(current_price)
            #Rearrange columns: Move cost basis to end
            cols = df.columns.tolist()
            cols = cols[1:] + [cols[0]]
            df = df[cols]
            df['current_price'] = current_prices
            df['gain']          = (df['current_price'] * df['quantity']) - df['cost_basis']

 
            #print(df)
            if symbol is not None:
                out = df[df['symbol'].str.contains(symbol)]
            else:
                out = df
            return out
        else:
            return None
    except Exception as error:
        print("Error in Function get_all_open_positions :", error)
        print(json_response)
        return None

def close_all_open_positions(symbol = None, simulate = False):
    try:
        open_positions = get_all_open_positions(symbol)
        #print(open_positions)
        if not open_positions.empty:
            for index, row in open_positions.iterrows():
                option_symbol   = row['symbol']
                qty             = row['quantity']
                print(get_option_quote(option_symbol))
                option_price = get_option_quote(option_symbol)['mid_raw']
                option_sell_price = math.floor(option_price * 100)/100.0
                print(" Closing {} @ {}".format(option_symbol,option_sell_price))
                json_response, status_code = sellOptionSymbol(symbol, option_symbol, qty, option_price = option_sell_price , simulated= simulate)

        return None
    
    except Exception as error:
        print("Error in function close_open_positions :", error)

def getGainLoss(save = False):
    response = requests.get(gains_url,
        params={},
        headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
    )
    json_response = response.json()
    #print(json_response)
    data = json_response["gainloss"]['closed_position']
    #open_data = data = json_response["gainloss"]['open_position']
    #open_df = pd.Dataframe.from_dict(open_data)
    #print(open_df)
    out = pd.DataFrame.from_dict(data)
    if save:
        out.to_csv('Gains.csv')

    #print(json_response)
    return out


def getOptionExpDates(symbol):
    response = requests.get(expirations_url,
        params={'symbol': symbol, 'includeAllRoots': 'false', 'strikes': 'false'},
        headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
    )
    json_response = response.json()
    #print(response.status_code)
    #print(json_response)

    dates = json_response['expirations']['date']
    #print("dates: ", dates)
    #recent_date = dates[0]
    #print(out)
    #out = recent_date
    return dates

def get_best_option_ExpDate(symbol):
    dates = getOptionExpDates(symbol)
    #print(dates)
    dates = dates[:5]
    current_date = datetime.datetime.now()
    distances = [(datetime.datetime.strptime(x, '%Y-%m-%d')+datetime.timedelta(hours=16) - current_date).days for x in dates]
    #print("Distances :", distances)
    index = 0
    for distance in distances:
        if distance >= 1:
            break
        index +=1
    #print("Option Distance :", distance)
    print(dates[index])
    return dates[index]


def get_quotes(symbols):

    only_one_stock = (len(symbols) == 1)
    
    if only_one_stock:
        symbols.append('SPY')
    symbols_str = ','.join(symbols)
    #print(symbols_str)
    response = requests.get(quotes_url,
        params={'symbols': symbols_str},
        headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
        )
    json_response = response.json()
    #print("quotes: ", json_response)
    df = pd.DataFrame(json_response['quotes']['quote'])
    #print(df.columns)
    out = df[['symbol','last','trade_date']].copy()
    out['high'] = out['last']
    out['low']  = out['last']
    if only_one_stock:
        out = out.drop(index=out.index[-1])

    return out

def get_quotes_period(symbols):
    try:
        output = pd.DataFrame()
        symbol_info = {}
        global_symbol = None
        for i,symbol in enumerate(symbols):
            #print(symbol)
            global_symbol = symbol
            if symbol in symbol_info:
                row_of_interest = symbol_info[symbol]
                latest = (output.iloc[row_of_interest]).copy()
                output = output.append(latest, ignore_index = True)
            else:
                df = get_historical_intraday(symbol, period = 1)
                latest = df.iloc[-1]
                output = output.append(latest, ignore_index=True)
                output.at[i,'symbolName'] = symbol
                symbol_info[symbol] = i
        output = output.rename(columns={'close':'last'})
        #print(output)
        output.insert(0,column = 'symbol', value = symbols)
        return output
    except Exception as e:
        print("Error inside function get_quotes_period for {} :",e)
        print(df)
        return None

def get_quotes_data(symbols):
    try:
        output = pd.DataFrame()
        symbol_info = {}
        global_symbol = None
        dfs = {}
        for i,symbol in enumerate(symbols):
            #print(symbol)
            global_symbol = symbol
            if symbol in symbol_info:
                row_of_interest = symbol_info[symbol]
                latest = (output.iloc[row_of_interest]).copy()
                output = output.append(latest, ignore_index = True)
            else:
                df = get_historical_intraday(symbol, period = 1)
                latest = df.iloc[-1]
                output = output.append(latest, ignore_index=True)
                output.at[i,'symbolName'] = symbol
                symbol_info[symbol] = i
                dfs[symbol] = df
        output = output.rename(columns={'close':'last'})
        #print(output)
        output.insert(0,column = 'symbol', value = symbols)
        return output, dfs
    except Exception as e:
        print("Error inside function get_quotes_period for {} :",e)
        print(df)
        return None


def get_option_quote(option_symbol):
    try:
        response = requests.get(quotes_url,
            params={'symbols': option_symbol},
            headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
            )
        json_response = response.json()
        out = json_response['quotes']['quote']
        #print(out)
        bid_price = out['bid']
        ask_price = out['ask']
        mid_price = math.ceil(((bid_price + ask_price)/2.0) * 10)/10
        mid_raw_price = ((bid_price + ask_price)/2.0)
        out_value = {'bid': bid_price, 'ask': ask_price, 'mid': mid_price, 'mid_raw': mid_raw_price}

        return out_value
    except Exception as error:
        print(error)
        print('Error in function get_option_quote :', error)
        raise

def getOptionChain(symbol, expDate):
    #print('Enering Option Chain')
    response = requests.get(optionchain_url,
        params={'symbol': symbol, 'expiration': expDate, 'greeks': 'true'},
        headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
    )
    json_response = response.json()
    #print(response.status_code)
    #print(json_response)
    data = json_normalize(json_response['options']['option'])
    df = pd.DataFrame(data)
    #df.to_csv('Test.csv')
    out = df[['symbol','greeks.delta','strike','type','bid','ask','open_interest', 'volume']]

    return out

def getBestOption(optionChainer, optionSide = 'Call'):
    print('Entered Option Algo')
    optionChain = optionChainer
    if optionSide == 'Call':
        delta_mult = 1
    else:
        delta_mult = -1
 
    #get greeks between delta90 and delta10
    delta20 = optionChain[(optionChain['greeks.delta']*delta_mult <= 1.0) & (optionChain['greeks.delta']*delta_mult >= 0.1)]
    delta20 = delta20[((delta20['strike'] % 5) == 0) ]
    print("delta20_unfiltered:", delta20)

    #Get options between 1$ and 7$
    indexNames = delta20[(delta20['bid'] <= 3.00) | (delta20['bid'] >= 7.0)].index
    delta20_delta_filtered = delta20.drop(indexNames, inplace = False)
    delta20_delta_filtered['spread'] = delta20_delta_filtered['ask'] - delta20_delta_filtered['bid']
    #print("delta20_delta_filtered:", delta20_delta_filtered)

    #Get options with spread < 0.4
    indexNames = delta20_delta_filtered[(delta20_delta_filtered['spread'] >= 0.4)].index
    delta20_spread_filtered = delta20_delta_filtered.drop(indexNames, inplace = False)
    #print("delta20_spread_filtered:", delta20_spread_filtered)

    if not delta20_spread_filtered.empty:
        #Find the strike with highest delta in filtered data
        bestidx = delta20_spread_filtered['greeks.delta'].abs().idxmax()
        out     = delta20_spread_filtered.loc[[bestidx]]
    else:
        #Find the one with lowest spreads
        best_spread         = delta20_delta_filtered['spread'].min()
        print(best_spread)
        delta20_goodspread  = delta20_delta_filtered[delta20_delta_filtered['spread'] == best_spread]
        bestidx             = delta20_goodspread['greeks.delta'].abs().idxmax()
        out                 = delta20.loc[[bestidx]]
    #return alternate
    return out

def getBestOption_volume(optionChainer, optionSide = 'Call'):
    optionChain = optionChainer
    if optionSide == 'Call':
        delta_mult = 1
    else:
        delta_mult = -1
 
    #get greeks between delta90 and delta10
    #delta20 = optionChain[(optionChain['greeks.delta']*delta_mult <= 1.0) & (optionChain['greeks.delta']*delta_mult >= 0.1)]
    delta20 = optionChain[(optionChain['greeks.delta']*delta_mult <= 0.9) & (optionChain['greeks.delta']*delta_mult >= 0.1)]
    delta20 = delta20[((delta20['strike'] % 5) == 0) ]
    #print("delta20_unfiltered:", delta20)

    #Get options between 1$ and 7$
    indexNames = delta20[(delta20['bid'] <= 2.0) | (delta20['bid'] >= 7.0)].index
    delta20_delta_filtered = delta20.drop(indexNames, inplace = False)
    delta20_delta_filtered['spread'] = delta20_delta_filtered['ask'] - delta20_delta_filtered['bid']
    #print("delta20_delta_filtered:", delta20_delta_filtered)

    bestidx             = delta20_delta_filtered['volume'].idxmax()
    #bestidx             = delta20_delta_filtered[delta20_delta_filtered['volume'] == best_volume]
    out                 = delta20.loc[[bestidx]]
    #print("Option Volume :", out['volume'])
    #print(out)
    logOrderToFile("Option Volume : {}".format( out['volume']))
    #return alternate
    return out



def executeOptionBuyOrder(option_order_info):
    #print(option_order_info)
    response = requests.post(orderexec_url,
    data= option_order_info,
    headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
    )
    json_response = response.json()
    #print(response.status_code)
    #print(json_response)
    return json_response, response.status_code

def executeOptionSellOrder(option_order_info):
    #print(option_order_info)
    response = requests.post(orderexec_url,
    data= option_order_info,
    headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
    )
    json_response = response.json()
    #print(response.status_code)
    #print(json_response)
    return json_response, response.status_code
    
def sellOptionSymbol(symbol,option_symbol, option_qty, option_price = None, simulated = False):
    try:
        currentDT = get_current_cst_time_timestamp()
        if option_price is None:
            json_order_info = {'class': 'option', 'symbol': symbol, 
                'option_symbol': option_symbol, 
                'side': 'sell_to_close', 
                'quantity': option_qty, 'type': 'market', 'duration': 'day',
                'timestamp': currentDT}
        else:
            json_order_info = {'class': 'option', 'symbol': symbol, 
                'option_symbol': option_symbol, 
                'side': 'sell_to_close', 
                'quantity': option_qty, 'type': 'limit', 'duration': 'day', 'price': option_price,
                'timestamp': currentDT}
        if ((not simulated) and (option_qty >0)):
            json_response, status_code = executeOptionSellOrder(json_order_info)
            return json_response, status_code
        else:
            return None, None
    except Exception as e:
        print("Error in sellOptionSymbol :", e.message)

def buyOptionSymbol(symbol,option_symbol, option_qty, option_price = None, simulated = False):
    currentDT = get_current_cst_time_timestamp()
    if option_price is None:
        json_order_info = {'class': 'option', 'symbol': symbol, 
            'option_symbol': option_symbol, 
            'side': 'buy_to_open', 
            'quantity': option_qty, 'type': 'market', 'duration': 'day',
            'timestamp': currentDT}
    else:
        json_order_info = {'class': 'option', 'symbol': symbol, 
            'option_symbol': option_symbol, 
            'side': 'buy_to_open', 
            'quantity': option_qty, 'type': 'limit', 'duration': 'day', 'price': option_price,
            'timestamp': currentDT}
    if ((not simulated) and (option_qty >0)):
        json_response, status_code = executeOptionBuyOrder(json_order_info)
        return json_response
        
def algo_create_option_order(symbol, optionSide = "Call", exp_date = None, strike = None, allocatedAmount = 500, min_contract_qty = 0):
    print("Trading symbol: ", symbol)
    #Get Options Expirations
    if exp_date is None:
        exp_date = get_best_option_ExpDate(symbol)

    opex  = getOptionChain(symbol, exp_date)
    #print(opex)
    if strike is None:
        best  = getBestOption(opex, optionSide)
        best  = getBestOption_volume(opex, optionSide)
    else:
        #%%
        if optionSide == 'Call':
            bests = opex[(opex['strike'] >= strike)]
            best = bests[bests['greeks.delta'] >0].iloc[0:1]

        elif optionSide == 'Put':
            bests = opex[(opex['strike'] <= strike)]
            best = bests[bests['greeks.delta'] < 0].iloc[-1:]

    
    print("Option Selected :", best)   
    option_symbol = best['symbol'].values[0]
    bid_price = best['bid'].values[0]
    ask_price = best['ask'].values[0]
    spread = (ask_price - bid_price)
    mid_price = (bid_price + ask_price)/2.0
    if spread >= 0.4:
        option_price = round_price(mid_price,0.1)
    else:
        option_price = round_price(mid_price,0.05)

    #Round option price multiple of 10cents
    option_delta = round(best['greeks.delta'].values[0],2)
    option_strike = round(best['strike'].values[0],1)

    option_qty = int(allocatedAmount/(option_price *100))
    if option_qty < min_contract_qty:
        option_qty = min_contract_qty

    #currentDT = get_current_cst_time()
    currentDT = get_current_cst_time_timestamp()
    text_order_info = " >>> Bought {} {} Option {} @ {} (Delta {}) at time: {} >>>".format(option_qty, optionSide, option_symbol, option_price, option_delta, currentDT)
    #print(text_order_info)

    
    json_order_info = {'class': 'option', 'symbol': symbol, 
        'option_symbol': option_symbol, 
        'side': 'buy_to_open', 
        'quantity': option_qty, 
        'type': 'limit', 
        'duration': 'day', 
        'price': option_price,
        'strike': option_strike,
        'timestamp': currentDT}
        #print(option_order_info)

    return json_order_info, text_order_info

def get_historical_intraday(symbol, period = 5, start_time = None, stop_time = None, calc_atr = False, ignore_time = False):
    
    #offset = timedelta(days=2,hours=14, minutes = 30)
    offset = datetime.timedelta(days = 0)
    try:
        symbol = symbol.upper()
        interval = str(period)+'min'
        stop_time_str = stop_time
        start_time_str = start_time
        interval = 'daily'

        #print("History Data Start Time : {}, End Time :{}".format(start_time, stop_time))
        params=     {    
                    'symbol': symbol, 
                    'interval': interval, 
                    'start': start_time_str, 
                    'end': stop_time_str, 
                    'session_filter': 'open'
                    }

        headers = {'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
        response = requests.get(history_url, params = params, headers = headers)
        #response = requests.get(timesales_url, params = params, headers = headers)
        #print(response)
        json_response = response.json()
        #print(json_response)
        df = None
        if json_response['series'] is None:
            msg = ('Invalid arguments to API Call for get_historical_intraday(): Check Symbol or time, symbol : {}'.format(symbol))
            raise Exception(msg)
        else:
            df = pd.DataFrame(json_response['series']['data'])
            #print(df)
            return df
        #df.to_csv('data.csv')

    except Exception as e:
        print("Error in function get_historical_intraday", e)
        print(json_response)
        
        print(df)
        if df is not None:
            df.to_csv('APIData.csv')
        return None

def get_historical(symbol, start_day = None, stop_day = None):
    
    #offset = timedelta(days=2,hours=14, minutes = 30)
    offset = datetime.timedelta(days = 0)
    try:
        symbol = symbol.upper()
        interval = 'daily'

        #print("History Data Start Time : {}, End Time :{}".format(start_time, stop_time))
        params=     {    
                    'symbol': symbol, 
                    'interval': interval, 
                    'start': start_day, 
                    'end': stop_day, 
                    }

        headers = {'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
        response = requests.get(history_url, params = params, headers = headers)
        #response = requests.get(timesales_url, params = params, headers = headers)
        #print(response)
        json_response = response.json()
        print(json_response)
        df = None
        if json_response is None:
            msg = ('Invalid arguments to API Call for get_historical_intraday(): Check Symbol or time, symbol : {}'.format(symbol))
            raise Exception(msg)
        else:
            df = pd.DataFrame(json_response['history']['day'])
            #print(df)
            return df
        #df.to_csv('data.csv')

    except Exception as e:
        print("Error in function get_historical_intraday", e)
        print(json_response)
        
        print(df)
        if df is not None:
            df.to_csv('APIData.csv')
        return None

def get_candle_info(symbol,ts, period = 5):

    if ts is None:
        raise  Exception('Invalid Input Timestamp given for get_candle_attime() function : {} '.format(t))
    
    try:
        #Round to nereast N minutes
        t = get_est_time_from_timestamp(ts)
        t = t - datetime.timedelta(minutes = (t.minute) % period , seconds = t.second, microseconds = t.microsecond)
        search_time = int(t.timestamp())
        print("Search Time :", search_time)
        print("EST Time :", t)
        t = t.replace(tzinfo = None)
        df = get_historical_intraday(symbol, period = period, stop_time = t + datetime.timedelta(minutes = period))
        #print(df)
        data = atr(df,14)
        #data = df
        df.to_csv('data.csv')

        #Find nearest candle to requested timestamp
        #print('Search Time: {}'.format(search_time))
        out = data[data['timestamp'] == search_time]
        #print(out)
        
        if out.empty:
            #print(out)
            print('Empty Dataframe at searched Index')
            raise Exception('Cannot Find Candle Info at time t : {}'.format(t))
        else:
            latest_candle_info = out.iloc[0]
            return latest_candle_info.to_dict()

        #replace timetsamp to local
        #latest_candle_info = get_candleinfo_by_index(out, index = 0)
        #latest_candle_info['symbol'] = symbol

 
    except Exception as e:
        print(" Error in tradier_api.py at function get_candle_info", e)
    

def average_true_range(df, n):
    """
    
    :param df: pandas.DataFrame
    :param n: 
    :return: pandas.DataFrame
    """
    i = 0
    TR_l = [0]
    while i < df.index[-1]:
        TR = max(df.loc[i + 1, 'high'], df.loc[i, 'close']) - min(df.loc[i + 1, 'low'], df.loc[i, 'close'])
        TR_l.append(TR)
        i = i + 1
    TR_s = pd.Series(TR_l)
    ATR = pd.Series(TR_s.ewm(span=n, min_periods=n).mean(), name='ATR_' + str(n))
    df = df.join(ATR)
    return df

#----------------------------------------------------------------------#
#----------ATR Function------------------------------------------------#
#https://stackoverflow.com/questions/40256338/calculating-average-true-range-atr-on-ohlc-data-with-python/42251464#42251464
#----------------------------------------------------------------------#
def wwma(values, n):
    """
     J. Welles Wilder's EMA 
    """
    return values.ewm(alpha=1/n, adjust=False).mean()

def atr(df, n=14):
    data = df.copy()
    high = data['high']
    low = data['low']
    close = data['close']
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = wwma(tr, n)
    ATR = pd.Series(atr, name='ATR_' + str(n))
    #print("ATR :", atr)
    df = df.join(ATR)
    return df

def get_premarket_data(symbol, date = None, period = 1):
    current_time = datetime.datetime.strptime(date, '%Y-%m-%d')
    # central_tz = pytz.timezone('America/Chicago')
    # current_time = current_time.replace(tzinfo = central_tz)
    # start_time  = current_time.replace(hour = 6, minute = 00, second = 0, microsecond = 0)
    # stop_time   = current_time.replace(hour = 8, minute = 29, second = 0, microsecond = 0)

    current_time = current_time.replace(tzinfo = eastern)
    start_time  = current_time.replace(hour = 6, minute = 00, second = 0, microsecond = 0)
    stop_time   = current_time.replace(hour = 9, minute = 29, second = 0, microsecond = 0)
    data        = get_historical_intraday(symbol, start_time = start_time, stop_time = stop_time, period = period)
    #print(data)
    #data.to_csv('PreMarketData.csv')

    if data is not None:
        high = data['high'].max()
        low  = data['low'].min()
        premarket_hi_lo = {'High': high, 'Low': low}
    else:
        premarket_hi_lo = {'High': None, 'Low': None}
    #print(premarket_hi_lo)
    return premarket_hi_lo

	
def algo_buy_option(symbol, optionSide = "Call", exp_date = None, strike = None, allocatedAmount = 500, min_contract_qty = 0, simulated = False, ):
    print("Trading symbol: ", symbol)
    #Get Options Expirations
    if exp_date is None:
        exp_date = get_best_option_ExpDate(symbol)

    opex  = getOptionChain(symbol, exp_date)
    #print(opex)
    if strike is None:
        best  = getBestOption(opex, optionSide)
    else:
        #%%
        if optionSide == 'Call':
            bests = opex[(opex['strike'] >= strike)]
            #print(bests)
            best = bests[bests['greeks.delta'] >0].iloc[0:1]
            #print(best)
        elif optionSide == 'Put':
            bests = opex[(opex['strike'] >= strike)]
            best = bests[bests['greeks.delta'] < 0].iloc[0:1]
    
    print("Option Selected :", best)    
    option_symbol = best['symbol'].values[0]
    option_price = round(((best['bid'] + best['ask'])/2.0).values[0], 2)
    option_delta = round(best['greeks.delta'].values[0],2)
    option_strike = round(best['strike'].values[0],1)



    option_qty = int(allocatedAmount/(option_price *100))
    if option_qty < min_contract_qty:
        option_qty = min_contract_qty
    #print("Option Symbol :", option_symbol)
    #print("Option Price :", option_price)
    #print("Option Delta :", option_delta)
    #currentDT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #currentDT = get_current_cst_time()
    currentDT = get_current_cst_time_timestamp()
    text_order_info = " >>> Bought {} {} OPtion {} @ {} (Delta {}) at time: {} >>>".format(option_qty, optionSide, option_symbol, option_price, option_delta, currentDT)
    print(text_order_info)

    
    json_order_info = {'class': 'option', 'symbol': symbol, 
        'option_symbol': option_symbol, 
        'side': 'buy_to_open', 
        'quantity': option_qty, 
        'type': 'limit', 
        'duration': 'day', 
        'price': option_price,
        'strike': option_strike,
        'timestamp': currentDT}
        #print(option_order_info)
    if ((not simulated) and (option_qty >0)) :
        executeOptionBuyOrder(json_order_info)

    return json_order_info, text_order_info



def stock_order(symbol, qty , order_type, order_price, order_direction):
    try:
        stock_order_info = {
            'class': 'equity', 
            'symbol': symbol, 
            'side': order_direction, 
            'quantity': qty, 
            'type': order_type, 
            'duration': 'day', 
            'price': round(order_price,2)
            }

        print('price to buy:', order_price)
        print(stock_order_info)
        response = requests.post(orderexec_url,
        data= stock_order_info,
        headers={'Authorization': 'Bearer '+ TRADIER_API_KEY, 'Accept': 'application/json'}
        )
        
        if response.ok ==True:
            json_response = response.json()
        else:
            raise Exception(response.content)
        return json_response
    except Exception as e:
        #print('Error in Tradier API, stock_order function:',e)
        #raise Exception(e)
        raise

