from email.utils import parsedate
from os import access
from re import L
from time import time
from tkinter import Tk
from matplotlib import pyplot as plt, transforms
import pandas as pd
from pip import main
import requests
import time
import json
import math

import subprocess
import pyautogui

import torch
import torchvision.transforms as transforms
import torchvision
from PIL import Image

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


# Class Specific Global Variables
accessToken = ""
refreshToken = ""
signedIn = 0
accountID=""
fundsAvailable=0
accountID_TFSA=""
fundsAvailable_TFSA=0
securities=[]

# Loading Trained Model
model=torchvision.models.googlenet(pretrained=True)
try:
    model.load_state_dict(torch.load('./WealthsimpleBot/model/1.5.pth'),strict=False)
except:
    model.load_state_dict(torch.load('./WealthsimpleBot/model/1.5.pth',map_location=torch.device('cpu')),strict=False)
pass
# Setting Device 
model.to('cpu')
# Setting model to eval mode
model.eval()

class WealthsimpleAPI:
    def readConfigurationFile(fileLocation):
        with open(fileLocation) as f:
            data = json.load(f)
        return data
    def appendToFile(line,filename):
        file= open(filename, "a")
        file.write(line+'\n')
        file.close()
        
    def loginWith2FA(email,password):
        otp=WealthsimpleAPI.getCode()
        WealthsimpleAPI.login(email, password, otp)
        WealthsimpleAPI.getAccounts()

    # Message box func
    def print_msg_box(msg, indent=1, width=None, title=None):
        """Print message-box with optional title."""
        lines = msg.split('\n')
        space = " " * indent
        if not width:
            width = max(map(len, lines))
        box = f'╔{"═" * (width + indent * 2)}╗\n'  # upper_border
        if title:
            box += f'║{space}{title:<{width}}{space}║\n'  # title
            box += f'║{space}{"-" * len(title):<{width}}{space}║\n'  # underscore
        box += ''.join([f'║{space}{line:<{width}}{space}║\n' for line in lines])
        box += f'╚{"═" * (width + indent * 2)}╝'  # lower_border
        print(box)

    def updateAccessToken(access):
        global accessToken
        accessToken = access

    def updateRefreshToken(refresh):
        global refreshToken
        refreshToken = refresh

    def updateSignedInStatus(status):
        global signedIn
        signedIn = status

    def updateAccountID(account):
        global accountID
        accountID=account
    
    def updateFunds(amount):
        global fundsAvailable
        fundsAvailable=amount
    
    def updateAccountID_TFSA(account):
        global accountID_TFSA
        accountID_TFSA=account
    
    def updateFunds_TFSA(amount):
        global fundsAvailable_TFSA
        fundsAvailable_TFSA=amount
    
    def updateSecurities(id):
        global securities
        exists=0
        for i in range(len(securities)):
            if (securities[i]==id):
                print("ID already exists in list")
                exists=1
        if (exists==0):
            securities.append(id)

    def getAvailableFunds():
        return fundsAvailable
        
    def login(email, password, otp):
        url = 'https://trade-service.wealthsimple.com/auth/login'
        myobj = {'email': email, 'password': password, 'otp': otp}
        x = requests.post(url, json=myobj)
        print ("Sign in API CALL:")
        print (x.content)
        print (x.status_code)
        try:
            WealthsimpleAPI.updateAccessToken(x.headers['X-Access-Token'])
            WealthsimpleAPI.updateRefreshToken(x.headers['X-Refresh-Token'])
            WealthsimpleAPI.updateSignedInStatus(1)
            return 1
        except:
            WealthsimpleAPI.updateSignedInStatus(0)
            print("Failed to sign in (Make sure OTP and Username/Password are correct)")
            return -1

    def refreshSession():
        url = "https://trade-service.wealthsimple.com/auth/refresh"
        myobj = {'refresh_token': refreshToken}
        # x = requests.post(url, json=myobj)
        x = requests.post(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        if (x.text == "OK"):
            WealthsimpleAPI.updateSignedInStatus(1)
            return 1
        else:
            WealthsimpleAPI.updateSignedInStatus(0)
            print("Failed to refresh session")
            return -1

    def getAccounts():
        url = 'https://trade-service.wealthsimple.com/account/list'
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        json_object = json.loads(r.text)
        for i in json_object['results']:
            if (i['account_type']=='ca_non_registered'):
                if (i['base_currency']=='CAD'):
                    WealthsimpleAPI.updateAccountID(i['id'])
                    WealthsimpleAPI.updateFunds(i['buying_power']['amount'])
            elif (i['account_type']=='ca_tfsa'):
                if (i['base_currency']=='CAD'):
                    WealthsimpleAPI.updateAccountID_TFSA(i['id'])
                    WealthsimpleAPI.updateFunds_TFSA(i['buying_power']['amount'])



    def getAccountHoldings():
        # Making Requests to find holdings
        url='https://trade-service.wealthsimple.com/account/positions'
        myobj = {"account_id": accountID_TFSA}
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        json_object = json.loads(r.text)
        # Grabbing important data
        allPositions=[]
        for i in json_object['results']:
            if (i['account_id']==accountID):
                result=[]
                result.append(i['stock']['symbol'])
                result.append(i['quantity'])
                result.append(i['market_book_value']['amount'])
                result.append(float(i['market_book_value']['amount'])/float(i['quantity']))
                result.append(i['id'])
                result.append(WealthsimpleAPI.realTimeSecurityPrice(i['id'])[1])
                result.append(float(result[5])*float(result[1]))
                result.append(float(result[6])-float(result[2]))
                result.append(float(result[6])/float(result[2]))
                if (result[8]<1):
                    result[8]=(result[8]-1)*100
                else:
                    result[8]=(result[8]-1)*100
                dict = {'Symbol': result[0], 'Quantity': result[1], 'Price': result[2], 'Average_Price': result[3], 'Security_ID': result[4], 'Current_Price': result[5], 'Value_Now':  round(float(result[6]), 2), 'Profit': round(float(result[7]), 2),'Percent':str(round(float(result[8]), 2))+'%'}
                allPositions.append(dict)
        return allPositions


    def getAccountHoldingsTFSA():
        # Making Requests to find holdings
        url='https://trade-service.wealthsimple.com/account/positions'
        myobj = {"account_id": accountID_TFSA}
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        json_object = json.loads(r.text)
        # Grabbing important data
        allPositions=[]
        for i in json_object['results']:
            if (i['account_id']==accountID_TFSA):
                result=[]
                result.append(i['stock']['symbol'])
                result.append(i['quantity'])
                result.append(i['market_book_value']['amount'])
                result.append(float(i['market_book_value']['amount'])/float(i['quantity']))
                result.append(i['id'])
                result.append(WealthsimpleAPI.realTimeSecurityPrice(i['id'])[1])
                result.append(float(result[5])*float(result[1]))
                result.append(float(result[6])-float(result[2]))
                result.append(float(result[6])/float(result[2]))
                if (result[8]<1):
                    result[8]=(result[8]-1)*100
                else:
                    result[8]=(result[8]-1)*100
                dict = {'Symbol': result[0], 'Quantity': result[1], 'Price': result[2], 'Average_Price': result[3], 'Security_ID': result[4], 'Current_Price': result[5], 'Value_Now':  round(float(result[6]), 2), 'Profit': round(float(result[7]), 2),'Percent':str(round(float(result[8]), 2))+'%'}
                allPositions.append(dict)
        return allPositions

    def getSecurityID(ticker):
        foundSecurity=0
        secureID=-1
        url = 'https://trade-service.wealthsimple.com/securities?query='+ticker
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        json_object = json.loads(r.text)
        for i in json_object['results']:
            # if (i['currency']=='CAD'):
            foundSecurity=1
            secureID=i['id']
            WealthsimpleAPI.updateSecurities(secureID)
        if (foundSecurity==0):
            print ("Failed to find Security")
        return secureID

    def getInfoByID(id):
        url = 'https://trade-service.wealthsimple.com/securities/'+id
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        json_object = json.loads(r.text)
        return json_object

    def placeLimitOrder(securityID,quantity,price):
        global accountID
        url = 'https://trade-service.wealthsimple.com/orders'
        myobj = {'security_id': securityID, 'limit_price': price, 'quantity': quantity,'order_type':"buy_quantity","order_sub_type": "limit","time_in_force":"day","account_id": accountID}
        r = requests.post(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        print (r.text)

        #         POST https://trade-service.wealthsimple.com/orders
        # {
        #     {
        #         "security_id": "sec-s-76a7155242e8477880cbb43269235cb6",
        #         "limit_price": 5.00,
        #         "quantity": 100,
        #         "order_type": "buy_quantity",
        #         "order_sub_type": "limit",
        #         "time_in_force": "day"
        #     }
        # }

    def shootLimitOrder(securityID,price,quantity,accountIDtoUse):
        url = 'https://trade-service.wealthsimple.com/orders'
        myobj = {'security_id': securityID, 'limit_price': price, 'quantity': quantity,'order_type':"buy_quantity","order_sub_type": "limit","time_in_force":"day","account_id": accountIDtoUse}
        r = requests.post(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        print (r.text)

    def shootMarketOrder(securityID,price,quantity,accountIDtoUse):
        url = 'https://trade-service.wealthsimple.com/orders'
        myobj = {'security_id': securityID, 'limit_price': price, 'quantity': quantity,'order_type':"buy_quantity","order_sub_type": "market","time_in_force":"day","account_id": accountIDtoUse}
        r = requests.post(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        if (r.status_code==201):
            print ("Completed market order")
            return 1
        else:
            print ("Something went wrong")
            return -1
        # print (r.text)
    
    
    def shootMarketOrderRegularAccount(securityID,price,quantity):
        url = 'https://trade-service.wealthsimple.com/orders'
        myobj = {'security_id': securityID, 'limit_price': price, 'quantity': quantity,'order_type':"buy_quantity","order_sub_type": "market","time_in_force":"day","account_id": accountID}
        r = requests.post(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        if (r.status_code==200):
            print ("Completed market order")
            return 1
        else:
            print ("Something went wrong")
            return -1
        # print (r.text)

    def shootMarketOrderRegularAccount_Sell(securityID,price,quantity):
        url = 'https://trade-service.wealthsimple.com/orders'
        myobj = {'security_id': securityID, 'quantity': quantity,'order_type':"sell_quantity","order_sub_type": "market","time_in_force":"day","account_id": accountID}
        r = requests.post(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  

        if (r.status_code==201):
            print ("Completed market order")
            return 1
        else:
            print ("Something went wrong")
            return -1
        # print (r.text)

    def getHistoricalPrices(ticker,interval):
        url='https://trade-service.wealthsimple.com/securities/'+str(ticker)+'/historical_quotes/'+str(interval)+'?mic=XNAS'
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        parsed = json.loads(r.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))

    def getSecurityInformation(ticker):
        url='https://trade-service.wealthsimple.com/securities/'+str(ticker)
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        # print (r.text)
        parsed = json.loads(r.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))
    
    def balanceAccount_TFSA(tickers,allocation):
        global accountID_TFSA
        id_TFSA=[]
        quantity_TFSA=[]
        symbol_TFSA=[]
        price_TFSA=[]
        value_TFSA=[]
        percentage_TFSA=[]
        totalTFSAValue=0
        desired_percentage_TFSA=[]
        imbalance_TFSA=[]
        recommendations_TFSA=[]
        funding=fundsAvailable_TFSA
        funding=funding*0.94

        # Making Requests to find holdings
        url='https://trade-service.wealthsimple.com/account/positions'
        myobj = {"account_id": accountID}
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        },json=myobj)  
        json_object = json.loads(r.text)

        # Grabbing important data
        for i in json_object['results']:
            if (i['account_id']==accountID_TFSA):
                id_TFSA.append(i['id'])
                quantity_TFSA.append(i['quantity'])
                symbol_TFSA.append(i['stock']['symbol'])
                price_TFSA.append(i['quote']['last'])
                value_TFSA.append(float(i['quote']['last'])*float(i['quantity']))
                totalTFSAValue+=float(i['quote']['last'])*float(i['quantity'])
        
        # Making sure TFSA is structured according to configuration file
        updated=len(tickers)
        for i in range (len(id_TFSA)):
            percentage_TFSA.append(float(value_TFSA[i])/float(totalTFSAValue))
            if (len(symbol_TFSA)==len(tickers)):
                for x in range(len(tickers)):
                    if (tickers[x]==symbol_TFSA[i]):
                        desired_percentage_TFSA.append(allocation[x])
                        updated-=1
        if(updated!=0):
            print ("Issue with provided portfolio allocation (TFSA may be holding unnacounted for securities)")
            return -1

        # Checking for an imbalance in desired portfolio
        for i in range (len(id_TFSA)):
            # print (symbol_TFSA[i]+" : "+str(value_TFSA[i])+" : "+ "{:.0%}".format(percentage_TFSA[i])+ " : Desired Allocation {:.0%}".format(desired_percentage_TFSA[i]))
            if (percentage_TFSA[i]>desired_percentage_TFSA[i]):
                imbalance_TFSA.append(-1)
            elif (percentage_TFSA[i]==desired_percentage_TFSA[i]):
                imbalance_TFSA.append(0)
            elif (percentage_TFSA[i]<desired_percentage_TFSA[i]):
                imbalance_TFSA.append(1)

        # Planning out shares to purchase
        remaining=funding
        for i in range (len(id_TFSA)):
            balanceSymbol=funding*float(desired_percentage_TFSA[i])
            sharesPossible=math.trunc(balanceSymbol/float(price_TFSA[i]))
            print ('Available for : '+symbol_TFSA[i]+" : "+str(balanceSymbol))
            print ('Shares to buy : '+str(sharesPossible))
            remaining=remaining-sharesPossible*float(price_TFSA[i])
            recommendations_TFSA.append(sharesPossible)

        # Handling left over funds (put into most imbalanced portfolio item)
        for i in range (len(id_TFSA)):
            if (imbalance_TFSA[i]==1):
                if (remaining>float(price_TFSA[i])):
                    recommendations_TFSA[i]+=1

        # Place Market orders for desired shares
        for i in range (len(recommendations_TFSA)):
            if (recommendations_TFSA[i]!=0):
                print ("Placing order to Rebalance TFSA:"+ str(symbol_TFSA[i]) +' x ' +str(recommendations_TFSA[i]))
                maxPrice=float(price_TFSA[i])*1.01
                WealthsimpleAPI.shootMarketOrder(id_TFSA[i],maxPrice,recommendations_TFSA[i],accountID_TFSA)
                time.sleep(5)
        print ("TFSA Rebalancing Complete...")
        WealthsimpleAPI.getAccounts()
        return 1

    def realTimeSecurityPrice(ticker):
        url="https://trade-service.wealthsimple.com/quotes/"+ticker        
        r = requests.get(url, headers={
            'Authorization': accessToken, 'refresh_token': refreshToken
        })
        parsed = json.loads(r.text)
        result=[]
        result.append(parsed['quote']['security_id'])
        result.append(parsed['quote']['amount'])
        result.append(parsed['quote']['currency'])
        return (result)

    # Code that doesn't belong here
    def getCode():
        subprocess.call("start chrome", shell=True)
        time.sleep(2)
        pyautogui.click(1760, 50)
        time.sleep(2)
        pyautogui.click(1540, 165)
        pyautogui.hotkey('ctrl', 'w')
        return Tk().clipboard_get()
    
    def afterHours(now = None):
            import datetime, pytz, holidays
            import datetime as datetime
            
            tz = pytz.timezone('US/Eastern')
            us_holidays = holidays.US()

            if not now:
                now = datetime.datetime.now(tz)
            openTime = datetime.time(hour = 9, minute = 30, second = 0)
            closeTime = datetime.time(hour = 16, minute = 0, second = 0)
            # If a holiday
            if now.strftime('%Y-%m-%d') in us_holidays:
                return True
            # If before 0930 or after 1600
            if (now.time() < openTime) or (now.time() > closeTime):
                return True
            # If it's a weekend
            if now.date().weekday() > 4:
                return True

            return False 

    def beforeMarketOpen(now=None):
        import datetime, pytz, holidays
        import datetime as datetime
        
        tz = pytz.timezone('US/Eastern')
        us_holidays = holidays.US()

        if not now:
            now = datetime.datetime.now(tz)
        openTime = datetime.time(hour = 9, minute = 0, second = 0)
        closeTime = datetime.time(hour = 9, minute = 30, second = 0) 

        # If a holiday
        if now.strftime('%Y-%m-%d') in us_holidays:
            return False
        # If 30 minutes before check
        if (now.time() < openTime) or (now.time() > closeTime):
            return False
        # If it's a weekend
        if now.date().weekday() > 4:
            return False
        return True

    def ListToJPEG(data,filename):
        # HelperFunctions.ltf(filename.replace(".jpeg",".txt"),data)
        plt.switch_backend('agg')
        newData=[]
        for i in range(len(data)):
            if (i>=(len(data)-101)):
                newData.append(data[i])
        df = pd.DataFrame(newData, columns=['data'])
        df.data.plot()
        plt.savefig(filename,dpi=30)
        plt.clf()
    
    def getSpecificHoldings(securityId):
        currentHoldings=WealthsimpleAPI.getAccountHoldings()
        for i in range(len(currentHoldings)):
            if (currentHoldings[i]['Security_ID']==securityId):
                return currentHoldings[i]
        return -1
    
    # API Specific Image Classification Function (For Faster Classifications)
    def ClassifyImageAPI(testLocation):
        img = Image.open(testLocation)
        test_transforms = transforms.ToTensor()
        # Converting Image to Tensor
        image_tensor = test_transforms(img).float()
        image_tensor = image_tensor.unsqueeze_(0)
        # Returning Model Output
        output = model(image_tensor)
        index = output.data.cpu().numpy().argmax()
        return (index)