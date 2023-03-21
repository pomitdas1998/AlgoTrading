import pandas as pd
import pandas_ta as ta
from smartapi import SmartConnect 
import pyotp

#create object of call
obj = SmartConnect(api_key="WxUYle42")

#login api call
data = obj.generateSession("P714156","9717",pyotp.TOTP("65EVYN5N6YQMX7OL2FKSPRRVKM").now())
refreshToken= data['data']['refreshToken']

#fetch the feedtoken
feedToken=obj.getfeedToken()
# print(feedToken)

try:
    historicParam={
    "exchange": "NSE",
    "symboltoken": "3045",
    "interval": "FIVE_MINUTE",
    "fromdate": "2023-01-23 09:15", 
    "todate": "2023-02-23 15:30"
    }

    candel_data = obj.getCandleData(historicParam)
    columns = ["time","open","high","low","close","volume"]
    df = pd.DataFrame(candel_data["data"],columns=columns)

except Exception as e:
    print("Historic Api failed: {}".format(e.message))

#calculate supertrend and added in df 
df["sup_trnd"] = ta.supertrend(high=df['high'], low=df['low'],close=df['close'],period=7,multiplier=3)["SUPERT_7_3.0"]
# print(df.tail(30))

#VWAP
df["Dates"] = pd.to_datetime(df["time"])
df.set_index('Dates',inplace = True)
df['VWAP'] = ta.vwap(df['high'],df['low'],df['close'],df['volume'])
df.reset_index(inplace = True)
# print(df.tail(30))

#calculating candle below VWAP or not
n=0
df['below']=0
df['above']=0
for i in range(n,len(df)):
    # CE side --->Close Price must be above or greater than VWAP
    if df['close'][i] >  df['VWAP'][i]:
            df['above'][i] = 1
    # PE side --->Close Price must be below VWAP
    if df['close'][i] <  df['VWAP'][i]:
        df['below'][i] = 1

#calculating candle below supertrend or not
n=6
df['buy']=0
df['sell']=0
for i in range(n,len(df)):
    # CE side --->Close Price must be above or greater than supertrend
    if df['close'][i-1] <= df['sup_trnd'][i-1] and df['close'][i] > df['sup_trnd'][i]:
        df['buy'][i] = 1
    # PE side --->Close Price must be below supertrend
    if df['close'][i-1] > df['sup_trnd'][i-1]  and df['close'][i] < df['sup_trnd'][i]:
        df['sell'][i]  = 1

#position
df["PE"]=0
df["CE"]=0
df['stop_loss_pe']=0
df['stop_loss_ce']=0
for i in range(6,len(df)):
    #pe position
    if df['below'][i] == 1 and df['sell'][i] == 1:

        df["PE"][i]=1
        #stop loss for pe side
        df['stop_loss_pe'][i] = df["high"].loc[i-5:i].max()
    
    #ce position
    if df['above'][i] == 1 and df['buy'][i] == 1:
       
        df["CE"][i]=1
        #stop loss for e side
        df['stop_loss_ce'][i] = df["low"].loc[i-5:i].min()

#exit condition
df['ce_exit'] = 0
df['pe_exit'] = 0
for i in range(6,len(df)):
    #CE exit condition
    if df['close'][i] < df['sup_trnd'][i]:
        df['ce_exit'][i] = 1
    #PE exit condition
    if df['close'][i] > df['sup_trnd'][i]:
        df['pe_exit'][i] = 1

#initiate CE amd PE trade
trade = []
for i in range(6,len(df)):
    if df['CE'][i] == 1:
        CE_entery = df['close'][i]
        stoploss = df['stop_loss_ce'][i]
        time = df['time'][i]
        for j in range(i,len(df)):
            if df['ce_exit'][j] == 1:
                exit = df['time'][j]
                break

        x = {"CE_entery":CE_entery,"stoploss":stoploss,"Entry_time":time,'exit_time':exit}
        trade.append(x )
    if df['PE'][i] == 1:
        PE_entery = df['close'][i]
        stoploss = df['stop_loss_pe'][i]
        time = df['time'][i]
        for j in range(i,len(df)):
            if df['pe_exit'][j] == 1:
                exit = df['time'][j]
                break
        x = {"PE_entery":PE_entery,"stoploss":stoploss,"Entry_time":time,"exit_time":exit}
        trade.append(x)

print(trade)


#add data in jsonfile
json = df.to_json('json1_file.json',indent =1,orient="records")

trade = pd.DataFrame(trade)
json = trade.to_json('output_file.json',indent =1, orient="records")









