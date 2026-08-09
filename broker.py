import os, uuid, requests, random
from datetime import datetime, timedelta, timezone

class PaperBroker:
    """Safe demo broker. No real orders leave this application."""
    def __init__(self):
        self.balance = float(os.environ.get("PAPER_STARTING_BALANCE","10000"))
        self._orders=[]; self._positions={}
        self.prices={"AAPL":220.0,"MSFT":510.0,"NVDA":180.0,"TSLA":320.0,"SPY":640.0,"EURUSD":1.1670,"GBPUSD":1.3450,"USDJPY":147.5,"XAUUSD":3400.0,"BTCUSD":115000.0}
    def quote(self,symbol):
        p=self.prices.get(symbol,100.0)
        return {"symbol":symbol,"bid":round(p-0.01,5),"ask":round(p+0.01,5),"last":p,"timestamp":datetime.now(timezone.utc).isoformat()}
    def account(self):
        return {"mode":"paper","balance":self.balance,"equity":self.balance,"currency":"USD","buying_power":self.balance,"broker":"PaperBroker"}
    def positions(self): return list(self._positions.values())
    def orders(self): return self._orders
    def place_order(self,d):
        q=self.quote(d["symbol"].upper()); side=d["side"].lower(); qty=float(d["qty"])
        price=float(d.get("price") or q["ask"] if side=="buy" else d.get("price") or q["bid"])
        oid=str(uuid.uuid4())
        order={"id":oid,"symbol":d["symbol"].upper(),"side":side,"type":d["type"].lower(),"qty":qty,"price":price,"status":"filled","created_at":datetime.now(timezone.utc).isoformat(),"sl":d.get("sl"),"tp":d.get("tp")}
        self._orders.insert(0,order)
        key=order["symbol"]; signed=qty if side=="buy" else -qty
        old=self._positions.get(key,{"symbol":key,"qty":0,"avg_price":price,"side":"long"})
        newqty=old["qty"]+signed
        if newqty==0: self._positions.pop(key,None)
        else:
            avg=((old["qty"]*old["avg_price"])+(signed*price))/newqty if old["qty"] and signed>0 else price
            self._positions[key]={"symbol":key,"qty":newqty,"avg_price":round(avg,5),"side":"long" if newqty>0 else "short"}
        return order
    def cancel_order(self,oid):
        for o in self._orders:
            if o["id"]==oid and o["status"]=="open": o["status"]="cancelled"; return o
        raise ValueError("Order not found or already filled.")
    def history(self,symbol,tf):
        q=self.quote(symbol); base=q["last"]; out=[]; now=datetime.now(timezone.utc)
        n=100
        for i in range(n):
            t=now-timedelta(minutes=(n-i)*5)
            drift=(random.random()-0.5)*base*0.01
            base=max(0.0001,base+drift)
            o=base-(random.random()-0.5)*base*0.004
            c=base+(random.random()-0.5)*base*0.004
            hi=max(o,c)*(1+random.random()*0.003); lo=min(o,c)*(1-random.random()*0.003)
            out.append({"time":int(t.timestamp()*1000),"open":o,"high":hi,"low":lo,"close":c,"volume":random.randint(100,10000)})
        return out

class AlpacaBroker:
    def __init__(self):
        self.key=os.environ["ALPACA_API_KEY"]; self.secret=os.environ["ALPACA_SECRET_KEY"]
        live=os.environ.get("ALPACA_LIVE","false").lower()=="true"
        self.base="https://api.alpaca.markets" if live else "https://paper-api.alpaca.markets"
        self.h={"APCA-API-KEY-ID":self.key,"APCA-API-SECRET-KEY":self.secret}
    def _r(self,m,path,**kw):
        r=requests.request(m,self.base+path,headers=self.h,timeout=15,**kw); r.raise_for_status(); return r.json()
    def account(self): return self._r("GET","/v2/account")
    def positions(self): return self._r("GET","/v2/positions")
    def orders(self): return self._r("GET","/v2/orders",params={"status":"all","limit":100})
    def quote(self,symbol):
        # Latest trade endpoint; market data entitlement may be required.
        return self._r("GET",f"/v2/stocks/{symbol}/trades/latest",params={"feed":"iex"})
    def history(self,symbol,tf):
        return self._r("GET",f"/v2/stocks/{symbol}/bars",params={"timeframe":"5Min","limit":100,"feed":"iex"}).get("bars",[])
    def place_order(self,d):
        payload={"symbol":d["symbol"].upper(),"qty":str(d["qty"]),"side":d["side"].lower(),"type":d["type"].lower(),"time_in_force":d.get("time_in_force","day")}
        if d.get("price") is not None: payload["limit_price"]=str(d["price"])
        return self._r("POST","/v2/orders",json=payload)
    def cancel_order(self,oid): return self._r("DELETE",f"/v2/orders/{oid}")

class OandaBroker:
    def __init__(self):
        self.token=os.environ["OANDA_TOKEN"]; self.account_id=os.environ["OANDA_ACCOUNT_ID"]
        live=os.environ.get("OANDA_LIVE","false").lower()=="true"
        self.base="https://api-fxtrade.oanda.com" if live else "https://api-fxpractice.oanda.com"
        self.h={"Authorization":f"Bearer {self.token}","Content-Type":"application/json"}
    def _r(self,m,path,**kw):
        r=requests.request(m,self.base+path,headers=self.h,timeout=15,**kw); r.raise_for_status(); return r.json()
    def account(self): return self._r("GET",f"/v3/accounts/{self.account_id}")["account"]
    def positions(self): return self._r("GET",f"/v3/accounts/{self.account_id}/openPositions")["positions"]
    def orders(self): return self._r("GET",f"/v3/accounts/{self.account_id}/pendingOrders")["orders"]
    def quote(self,symbol):
        x=self._r("GET","/v3/accounts/"+self.account_id+"/pricing",params={"instruments":symbol})["prices"][0]
        return {"symbol":symbol,"bid":float(x["bids"][0]["price"]),"ask":float(x["asks"][0]["price"]),"timestamp":x["time"]}
    def history(self,symbol,tf):
        gran={"1m":"M1","5m":"M5","15m":"M15","1h":"H1","4h":"H4","1D":"D"}.get(tf,"M5")
        return self._r("GET",f"/v3/instruments/{symbol}/candles",params={"granularity":gran,"count":100})["candles"]
    def place_order(self,d):
        units=str(d["qty"] if d["side"].lower()=="buy" else -float(d["qty"]))
        order={"order":{"instrument":d["symbol"].upper(),"units":units,"type":"MARKET"}}
        if d.get("sl"): order["order"]["stopLossOnFill"]={"price":str(d["sl"])}
        if d.get("tp"): order["order"]["takeProfitOnFill"]={"price":str(d["tp"])}
        return self._r("POST",f"/v3/accounts/{self.account_id}/orders",json=order)
    def cancel_order(self,oid): return self._r("PUT",f"/v3/accounts/{self.account_id}/orders/{oid}/cancel")

def get_broker():
    mode=os.environ.get("BROKER_MODE","paper").lower()
    if mode=="alpaca": return AlpacaBroker()
    if mode=="oanda": return OandaBroker()
    return PaperBroker()
