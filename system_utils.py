from datetime import datetime, timedelta
import pytz
import math

def get_current_cst_time():
    time = datetime.now(pytz.timezone('America/Chicago')).strftime("%Y-%m-%d %H:%M:%S")
    return time

def get_current_cst_time_minutes(delta = None):
    if delta is not None:
        toi = (datetime.now(pytz.timezone('America/Chicago')) - delta)
        toi_str = toi.strftime("%Y-%m-%d %H:%M")
    else:
        toi = datetime.now(pytz.timezone('America/Chicago'))
        toi_str = toi.strftime("%Y-%m-%d %H:%M")
    return toi, toi_str

def get_current_day(offset = 0):
    date = datetime.now(pytz.timezone('America/Chicago'))
    date = date - timedelta(days= offset)
    date_str = date.strftime("%Y-%m-%d")
    return date_str

def create_file_todays_date(prepend_name = '',append_name = '',ext = '.txt'):
    timestr = get_current_day()
    logFileName = prepend_name+timestr+ append_name+ ext
    return logFileName

def get_current_cst_time_timestamp():
    time = datetime.now(pytz.timezone('America/Chicago'))
    return time

def get_est_time_from_timestamp(timestamp_seconds):
    utc_datetime = datetime.utcfromtimestamp(timestamp_seconds)

    # set the timezone to UTC, and then convert to desired timezone
    out = utc_datetime.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone('America/New_York'))
    return out



def find_true_variable(var_list):
    for key,value in var_list.items():
        if value:
            return key
    
    return 'None'

def time_difference(t1,t2, threshold_seconds = 60):
    d1 = datetime.strptime(t1, "%Y-%m-%d %H:%M:%S")
    d2 = datetime.strptime(t2, "%Y-%m-%d %H:%M:%S")
    delta = (d1-d2).seconds
    elapsed_threshold =  (delta > threshold_seconds)

    return delta, elapsed_threshold

def check_continue_trading(TRADING_HOUR_START = '', TRADING_HOUR_END = ''):
    continue_loop = True
    print("Trading Hour Start : {} CST, Trading Hour End : {} CST" .format(TRADING_HOUR_START, TRADING_HOUR_END))
    if (TRADING_HOUR_START != '') and (TRADING_HOUR_END != ''):
        now_min = get_current_cst_time_minutes()
        if TRADING_HOUR_START < now_min <TRADING_HOUR_END:
            continue_loop = True
        else:
            continue_loop = False

    return continue_loop

def round_price(price_input, round_multiple = 0.1):
    price_rounded = math.ceil(price_input/ round_multiple) * round_multiple
    return price_rounded

def logOrderToFile(order_info_str):
    #timestr = datetime.now().strftime("%Y-%m-%d")
    timestr = get_current_day()
    log_file = timestr+'.txt'
    file_obj = open(log_file, 'a')
    file_obj.write(order_info_str + '\n')
    file_obj.close()