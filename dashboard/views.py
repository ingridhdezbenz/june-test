from django.shortcuts import render
import requests
from datetime import date, timedelta, datetime
from addict import Dict

# Create your views here.
def home(request):
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
            #price.append([int(x.timestamp[0:-3] + '000'), x.price, x.price, x.price, x.price])
            #volume.append([int(x.timestamp[0:-3] + '000'), x.traded_amount])
            acum_volume = acum_volume + x.traded_amount
            price_lst.append(x.price)
            
            
        #else:
            #x.timestamp[0:-3] + '000'
            
    
    price = price[::-1]
    volume = volume[::-1]

    context = {"price":price, "volume":volume, "exportData":exportData, "exportDataRaw":exportDataRaw}

    return render(request, 'dashboard/home.html', context=context)

def bitso(request):
    volume = []
    exportData = []

    response = requests.get('https://api.bitso.com/v3/ohlc?book=xrp_mxn&time_bucket=1800')
    data = response.json()
    dictionary = Dict(data)

    for x in dictionary.payload:
        volume.append([x.bucket_start_time, float(x.volume)])
        exportData.append([datetime.fromtimestamp(x.bucket_start_time/1000.0).strftime('%Y-%m-%d %H:%M:%S'), float(x.volume)])

    context = {"volume":volume, "exportData":exportData}

    return render(request, 'dashboard/bitso.html', context=context)

def bitstamp(request):
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

    context = {"volume":volume, "exportData":exportData, "exportDataRaw":exportDataRaw}

    return render(request, 'dashboard/bitstamp.html', context=context)