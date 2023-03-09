

def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e} in {func.__name__}")

            # Handle the error here, e.g. log it or raise a different exception

    return wrapper

class Stock_Long():
    def __init__(self,current_price, **kwargs):
        #def __init__(self, ticker, triggerlevel,stoploss,target1,target2, qty, ordertype,status,profit,handle)
        self.__dict__.update(kwargs)

        if (self.triggerlevel == None) or (self.stoploss == ""):
            self.triggerlevel = current_price

        if (self.stoploss == None) or (self.stoploss == ""):
            self.stoploss = 0.95 * self.triggerlevel

        if (self.target1 == None) or (self.target1 == ""):
            self.target1 = 1.3 * self.triggerlevel
        
        if (self.target2 == None) or (self.target2 == ""):
            self.target2 = 2.0 * self.triggerlevel

        if (self.max_loss == None) or (self.max_loss == ""):
            self.max_loss = 100

        if (self.ordertype ==None) or (self.ordertype == ""):
            self.ordertype = 'LMT'
        
        if (self.profit ==None) or (self.profit == ""):
            self.profit = 0


    def set_max_loss_percent(self, max_loss_percent):
        self.max_loss = max_loss_percent * self.triggerlevel

    def set_max_loss(self, max_loss):
        self.max_loss = max_loss

    @handle_error
    def execute(self, current_price):
        if self.status == "":
            order = self.idle_state_execute(current_price)

        elif self.status == 'PreTarget1':
            order = self.pretarget1_state_execute(current_price)

        elif self.status == 'PreTarget2':
            order = self.pretarget2_state_execute(current_price)

        elif self.status == 'Exit':
            order = None
        return order
    
    @handle_error
    def idle_state_execute(self, current_price):
        pass
        # if current_price > self.triggerlevel:
        #     if (self.ordertype == 'MKT') or (self.ordertype == "Market"):
        #         qty_unrounded = self.max_loss / (current_price - self.stoploss)
        #         self.ordertype = 'market'
        #     else:
        #         qty_unrounded = self.max_loss / (self.triggerlevel - self.stoploss)
        #         self.ordertype = 'limit'
        #     #print(qty_unrounded)
        #     self.qty = round(qty_unrounded)
            
        #     self.rem_qty = self.qty
        #     out = Order(symbol = self.ticker, order_direction= 'buy', order_price= self.triggerlevel, order_type = self.ordertype, qty = self.qty)
        #     self.status = 'PreTarget1'
        #     self.capital_util = self.rem_qty * self.triggerlevel
            
        # else:
        #     out = None
        # return out
    
    @handle_error
    def pretarget1_state_execute(self, current_price):
        out = None
        
        if current_price >= self.target1:
            sell_qty = round(0.5*self.qty)
            out =  Order(symbol = self.ticker, order_direction= 'sell', order_price= self.target1, order_type = self.ordertype, qty = sell_qty)
            self.profit = self.profit + ((self.target1 - self.triggerlevel) * sell_qty)
            self.rem_qty = (self.rem_qty - sell_qty)
            self.status = 'PreTarget2'
        elif current_price <= self.stoploss:
            sell_qty = self.rem_qty
            out =  Order(symbol = self.ticker, order_direction= 'sell', order_price= current_price, order_type = 'market', qty = sell_qty)
            self.profit = self.profit + ((current_price - self.triggerlevel) * sell_qty)
            self.rem_qty = (self.rem_qty - sell_qty)
            self.status = 'Exit'
        self.capital_util = self.rem_qty * self.triggerlevel
        return out
    
    @handle_error
    def pretarget2_state_execute(self, current_price):
        out = None
        
        if current_price >= self.target2:
            sell_qty = self.rem_qty
            out =  Order(symbol = self.ticker, order_direction= 'sell', order_price= self.target1, order_type = self.ordertype, qty = sell_qty)
            self.profit = self.profit + ((self.target2 - self.triggerlevel) * sell_qty)
            self.rem_qty = (self.rem_qty - sell_qty)
            self.status = 'Exit'
        elif current_price <= self.stoploss:
            sell_qty = self.rem_qty
            out =  Order(symbol = self.ticker, order_direction= 'sell', order_price= self.stoploss, order_type = 'market', qty = sell_qty)
            self.profit = self.profit + ((current_price - self.triggerlevel) * sell_qty)
            self.rem_qty = (self.rem_qty - sell_qty)
            self.status = 'Exit'
        self.capital_util = self.rem_qty * self.triggerlevel
        return out
    
    def exit_state_execute(self, current_price):
        pass

class Order:
    def __init__(self, symbol, order_direction, order_type, order_price, qty):
        self.symbol = symbol
        self.order_type = order_type
        self.order_price = order_price
        self.order_direction = order_direction
        self.qty = qty

class Breakout(Stock_Long):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @handle_error
    def idle_state_execute(self, current_price): #only modify the initial buy condition for pullback
        if current_price >= self.triggerlevel:
            if (self.ordertype == 'MKT') or (self.ordertype == "Market"):
                qty_unrounded = self.max_loss / (current_price - self.stoploss)
                self.ordertype = 'market'
            else:
                qty_unrounded = self.max_loss / (self.triggerlevel - self.stoploss)
                self.ordertype = 'limit'
            #print(qty_unrounded)
            if (self.qty =='') or (self.qty is None):
                self.qty = round(qty_unrounded)
            self.qty = round(qty_unrounded)
            self.rem_qty = self.qty
            out = Order(symbol = self.ticker, order_direction= 'buy', order_price= self.triggerlevel, order_type = self.ordertype, qty = self.qty)
            self.status = 'PreTarget1'
            self.capital_util = self.rem_qty * self.triggerlevel
        else:
            out = None
        return out

    

class Pullback(Stock_Long):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @handle_error
    def idle_state_execute(self, current_price): #only modify the initial buy condition for pullback
        if current_price <= self.triggerlevel:
            if (self.ordertype == 'MKT') or (self.ordertype == "Market"):
                qty_unrounded = self.max_loss / (current_price - self.stoploss)
                self.ordertype = 'market'
            else:
                qty_unrounded = self.max_loss / (self.triggerlevel - self.stoploss)
                self.ordertype = 'limit'
            #print(qty_unrounded)
            if (self.qty =='') or (self.qty is None):
                self.qty = round(qty_unrounded)
            self.rem_qty = self.qty
            out = Order(symbol = self.ticker, order_direction= 'buy', order_price= self.triggerlevel, order_type = self.ordertype, qty = self.qty)
            self.status = 'PreTarget1'
            self.capital_util = self.rem_qty * self.triggerlevel
        else:
            out = None
        return out