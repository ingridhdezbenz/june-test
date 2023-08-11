from django.shortcuts import render
import requests
from datetime import date, timedelta, datetime
from addict import Dict
from django.http import JsonResponse
import pandas as pd
import csv

# GET DATA
def getKrakenData(request):
    krakenData = []

    # KRAKEN
    response = requests.get('https://api.kraken.com/0/public/Ticker?pair=USDTEUR')
    data = response.json()
    dictionary = Dict(data)
    usdtEurBid = float(dictionary.result.USDTEUR.b[0])
    krakenData.append(usdtEurBid) # 0
    usdtEurAsk = float(dictionary.result.USDTEUR.a[0])
    krakenData.append(usdtEurAsk) # 1

    response = requests.get('https://api.kraken.com/0/public/Ticker?pair=USDTUSD')
    data = response.json()
    dictionary = Dict(data)
    usdtUsdBid = float(dictionary.result.USDTZUSD.b[0])
    krakenData.append(usdtUsdBid) # 2

    # ALPHA VANTAGE -- KJTZ254G0YEUR0VI
    response = requests.get('https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey=KJTZ254G0YEUR0VI')
    data = response.json()
    eurUsd = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
    krakenData.append(eurUsd) # 3

    # EFFECTIVE RATE
    effectiveRateBid = 1 / usdtEurBid / usdtUsdBid
    krakenData.append(effectiveRateBid) # 4
    effectiveRateAsk = 1 / usdtEurAsk / usdtUsdBid
    krakenData.append(effectiveRateAsk) # 5

    # SELL USDT FOR EUR ON FX
    sellUSDTBid = effectiveRateBid / eurUsd - 1
    krakenData.append(sellUSDTBid) # 6 
    sellUSDTAsk = effectiveRateAsk / eurUsd - 1
    krakenData.append(sellUSDTAsk) # 7

    context = {"krakenData": krakenData}

    return JsonResponse(context)

def getPdaxData():
    price = []
    volume = []
    exportData = []
    exportDataRaw = []

    endTime = date.today() + timedelta(days=1)

    time_change = timedelta(minutes=30)
    today = datetime.strptime((str(endTime) + ' 00:00:00'), '%Y-%m-%d %H:%M:%S')
    new_time = today - time_change

    startTime = endTime - timedelta(days=42)
    endTime = str(endTime) + 'T00:00:00.000Z'
    startTime = str(startTime) + 'T00:00:00.000Z'
    response = requests.get('https://services.pdax.ph/api/exchange/v2/system_trades?from={}&to={}&max=900000'.format(startTime,endTime))
    data = response.json()
    dictionary = Dict(data)

    acum_volume = 0
    price_lst = []

    for x in dictionary.data:
        exportDataRaw.append([datetime.utcfromtimestamp(int(x.timestamp[0:-3])).strftime('%Y-%m-%d %H:%M:%S'), x.price, x.traded_amount])
        while datetime.utcfromtimestamp(int(x.timestamp[0:-3])) < new_time:
            volume.append([int(datetime.timestamp(new_time)*1000), acum_volume])
            if len(price_lst) > 0:
                avg_price = sum(price_lst) / len(price_lst)
            else: 
                avg_price = 0
            price.append([int(datetime.timestamp(new_time)*1000), avg_price, avg_price, avg_price, avg_price])
            exportData.append([new_time.strftime('%Y-%m-%d %H:%M:%S'), acum_volume])
            new_time = new_time - time_change
            acum_volume = 0
            price_lst = []
        if datetime.utcfromtimestamp(int(x.timestamp[0:-3])) > new_time:
            acum_volume = acum_volume + x.traded_amount
            price_lst.append(x.price)
            
    
    price = price[::-1]
    volume = volume[::-1]

    df = pd.DataFrame(exportDataRaw, columns = ['date', 'price', 'volume'])
    df['date'] = pd.to_datetime(df.date, format='%Y-%m-%d %H:%M:%S')
    #df = df.groupby(df.date.dt.day)['volume'].sum()
    #df.groupby(df.date.dt.day).agg({'volume': 'sum', 'price':'first'}).reset_index()
    #df.groupby(pd.Grouper(key='date', freq='1D')).sum()
    df = df.groupby(pd.Grouper(key='date', axis=0, freq='1D')).sum()
    dayVolume = []
    for index, row in df.iterrows():
        dayVolume.append([str(index)[0:-9], row[1]])

    contextList = []
    contextList.append(price)
    contextList.append(volume)
    contextList.append(exportData)
    contextList.append(exportDataRaw)
    contextList.append(dayVolume)

    return contextList

def getBitsoData():
    volume = []
    exportData = []

    response = requests.get('https://api.bitso.com/v3/ohlc?book=xrp_mxn&time_bucket=1800')
    data = response.json()
    dictionary = Dict(data)

    for x in dictionary.payload:
        volume.append([x.bucket_start_time, float(x.volume)])
        exportData.append([datetime.fromtimestamp(x.bucket_start_time/1000.0).strftime('%Y-%m-%d %H:%M:%S'), float(x.volume)])

    contextList = []
    contextList.append(volume)
    contextList.append(exportData)

    return contextList      

def getBitstampData():
    volume = []
    exportData = []
    exportDataRaw = []

    response = requests.get('https://www.bitstamp.net/api/v2/ohlc/xrpeur/?limit=1000&step=1800')
    data = response.json()
    dictionary = Dict(data)

    for x in dictionary.data.ohlc:
        volume.append([int(x.timestamp + '000'), float(x.volume)])
        exportData.append([datetime.fromtimestamp(int(x.timestamp)).strftime('%Y-%m-%d %H:%M:%S'), float(x.volume)])

    response = requests.get('https://www.bitstamp.net/api/v2/transactions/xrpeur/?time=day')
    data = response.json()

    for x in data:
        exportDataRaw.append([datetime.fromtimestamp(int(x['date'])).strftime('%Y-%m-%d %H:%M:%S'), float(x['price']), float(x['amount'])])

    contextList = []
    contextList.append(volume)
    contextList.append(exportData)
    contextList.append(exportDataRaw)

    return contextList

# VIEWS
def home(request):
    pdaxData = getPdaxData()
    bitsoData = getBitsoData()
    bitstampData = getBitstampData()    

    context = {"pdaxVolume": pdaxData[1], "pdaxTable": pdaxData[3], "bitsoVolume": bitsoData[0], "bitsoTable": bitsoData[1], "bitstampVolume": bitstampData[0], "bitstampTable": bitstampData[2]}

    return render(request, 'dashboard/home.html', context=context)

def pdax(request):
    pdaxData = getPdaxData()

    context = {"volume": pdaxData[1], "exportData": pdaxData[2], "exportDataRaw": pdaxData[3], "dayVolume": pdaxData[4]}

    return render(request, 'dashboard/pdax.html', context=context)

def bitso(request):
    bitsoData = getBitsoData()

    file = open("dashboard/static/dashboard/data_btcbitso.csv")
    csvreader = csv.reader(file)
    btcPremium = []
    for row in csvreader:
       btcPremium.append([int(row[0]), (float(row[1]))])

    context = {"volume":bitsoData[0], "exportData":bitsoData[1], "btcPremium":btcPremium}

    return render(request, 'dashboard/bitso.html', context=context)

def bitstamp(request):
    bitstampData = getBitstampData()
    
    context = {"volume":bitstampData[0], "exportData":bitstampData[1], "exportDataRaw":bitstampData[2]}

    return render(request, 'dashboard/bitstamp.html', context=context)