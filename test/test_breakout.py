from algos import Breakout
import pprint


trade = Breakout(ticker = 'TSLA', 
                 triggerlevel = 210,
                 stoploss = None ,
                 target1 = None,
                 target2 = None, 
                 qty = None, 
                 ordertype = None,
                 status = "",
                 profit =0, 
                 handle ="")

print(vars(trade))

out = trade.execute(215)
if out is not None:
    print(vars(out))
print(trade.status)


out = trade.execute(272)
if out is not None:
    print(vars(out))
print(trade.status)


out = trade.execute(273.1)
if out is not None:
    print(vars(out))
print(trade.status)

out = trade.execute(199)
if out is not None:
    print(vars(out))

print(trade.status)