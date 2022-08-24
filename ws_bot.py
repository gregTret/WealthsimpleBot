import math
from WealthsimpleBot import WealthsimpleAPI as WealthsimpleAPI
import time
from datetime import datetime

# Email
email=""
# Password
password=""

# Getting date and setting up logging files
todaysDate=datetime.today().strftime('%Y-%m-%d')
logFile="logs/"+todaysDate+"_LOG.txt"
profitLogFile="logs/PROFITS_LOG.csv"
configurationFile="configuration.json"

# Loading Configurtation file
configuration=(WealthsimpleAPI.readConfigurationFile(configurationFile))
tickers=[]
for attribute, value in configuration['tickers'].items():
    elements=[]
    for attributeInner, valueInner in configuration['tickers'][attribute].items():
        elements.append(valueInner)
    tickers.append(elements)
for i in range (len(tickers)):
    tickers[i][0]="data/"+tickers[i][0]+'_'+todaysDate+".txt" 

# Signing in with Automatic 2FA
WealthsimpleAPI.loginWith2FA(email,password)

# Data collection phase (gonna need a little bit more)
while (WealthsimpleAPI.beforeMarketOpen()):
    print ("within 30 minutes to open, waiting...")
    time.sleep(10)

print ("Proceeding to main loop...")
messageBox=""
while (WealthsimpleAPI.afterHours()==False):
    for i in range(len(tickers)):
        filename=tickers[i][0]
        percentOfPortfolio=tickers[i][1]
        averageDown=tickers[i][2]
        minProfitMult=tickers[i][3]
        buyingEnabled=tickers[i][4]
        securityID=tickers[i][5]
        dataFile = open(filename, "a")
        
        # Getting Latest time
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        
        # All API calls made in here
        try:
            info=WealthsimpleAPI.realTimeSecurityPrice(securityID)
            output=str(info[0])+" : "+ str(info[1]) +" : " + str(info[2]) +" : " + str(current_time)
            dataFile.write(output+"\n")
            # print (output)
            dataFile.close()
            # Trading bot runs on filename
            if (buyingEnabled==1):
                f = open(filename, "r")
                line=f.readline().replace(" ","")
                prices=[]
                securityID_check=""
                classification=-2
                while (line):
                    splitLine=line.split(":")
                    splitLine[1]=float(splitLine[1])
                    securityID_check=splitLine[0]
                    prices.append(splitLine[1])
                    line=f.readline().replace(" ","")
                # Once enough data is collected the trading bot will kick in
                if (len(prices)>101):
                    # Convert List to JPEG for NN classification
                    WealthsimpleAPI.ListToJPEG(prices,"test.jpeg")
                    # Single most important line (Classifies last 100 data points)
                    classification=WealthsimpleAPI.ClassifyImageAPI("./test.jpeg")
                    # Update Account information
                    WealthsimpleAPI.getAccounts()
                    # Load variables up
                    holdings=WealthsimpleAPI.getSpecificHoldings(securityID_check)
                    latestPrice=float(WealthsimpleAPI.realTimeSecurityPrice(securityID_check)[1])
                    funds=WealthsimpleAPI.getAvailableFunds()
                    sharesToBuy=math.trunc((funds*percentOfPortfolio)/latestPrice)        
                    messageBox+= ("latest Price: " +str(latestPrice))+'\n'
                    # Displaying Current Classification for last 101 data points (33 minute sliding window)
                    if (classification==0):
                        messageBox+= ("Classification: None \n")
                    elif (classification==1):
                        messageBox+= ("Classification: Buy \n")
                    else:
                        messageBox+= ("Classification: Sell \n")
                    # Checking if currently selected shares are held in the account
                    if (holdings!=-1):
                        # Updating Variables
                        averagePrice=float(holdings['Average_Price'])
                        sharesInAccount=float(holdings['Quantity'])
                        approxAccountValue=(sharesInAccount*averagePrice)+funds
                        approxAmount=math.trunc((approxAccountValue*percentOfPortfolio)/latestPrice)
                        # Checking if there are enough funds to average into positions + checking out how many shares can be purchased under current configuration
                        if (funds>(approxAccountValue*percentOfPortfolio)):
                            sharesToBuy=math.trunc((approxAccountValue*percentOfPortfolio)/latestPrice)
                        else:
                            messageBox+= ("Bot fully averaged in : Must manually purchase remaining % of portfolio\n")
                        # Adding to display message box
                        messageBox+=("\nCurrent Profit/Loss: "+ str(holdings['Profit']))+'\n'
                        messageBox+=("Shares In Account: "+ str(holdings['Quantity']))+'\n'
                        messageBox+=("Percent: "+str (holdings['Percent']))+'\n'
                        messageBox+=("Average Cost: "+ str(round(averagePrice,2)))+'\n'
                        messageBox+=("Funds Remaining: " + str(funds))+'\n\n'
                        messageBox+=("Shares to buy : "+str(sharesToBuy))+'\n'
                        # Average downinator #2
                        averageDownAdjustment=round((averageDown*5)*((sharesInAccount*averagePrice)/approxAccountValue),2)
                        priceToAverageDownAt=averagePrice-averageDownAdjustment
                        # Minimum profitinator
                        if (((sharesInAccount*averagePrice)/approxAccountValue)<=0.15):
                            minProfit=minProfitMult
                        elif (((sharesInAccount*averagePrice)/approxAccountValue)<=0.3):
                            minProfit=round(minProfitMult*1.5,2)
                        elif (((sharesInAccount*averagePrice)/approxAccountValue)<=0.45):
                            minProfit=round(minProfitMult*2,2)
                        elif (((sharesInAccount*averagePrice)/approxAccountValue)<=0.6):
                            minProfit=round(minProfitMult*2.5,2)
                        elif (((sharesInAccount*averagePrice)/approxAccountValue)<=0.75):
                            minProfit=round(minProfitMult*3,2)
                        else:
                            minProfit=round(minProfitMult*3.5,2)
                        # Adding to display message box 
                        messageBox+=("Minimum Sell: "+str(round(averagePrice+minProfit,2)))+'\n'
                        messageBox+=("Minimum Profit: "+str(round(minProfit,2)))+'\n'
                        messageBox+=("Average Down Below: "+str (round(priceToAverageDownAt,2)))+'\n'
                        messageBox+=("Average Down Amount: "+str (averageDownAdjustment))+'\n\n'
                    else:
                        # If there are no holdings display # of shares that will be purchased
                        messageBox+= ("Will buy : " + str(sharesToBuy))+'\n'

                    # if classification is BUY and buying has been enabled
                    if (classification==1 and buyingEnabled==1):
                        # if there are no holdings
                        if (-1==holdings):
                            # print ("Not holding any of this security yet -> Time to buy")
                            WealthsimpleAPI.shootMarketOrderRegularAccount(securityID_check,latestPrice*1.01,sharesToBuy)
                            WealthsimpleAPI.getAccounts()
                            log="BUY,"+str(securityID_check)+','+str(latestPrice)+','+str(sharesToBuy)+','+str(current_time)
                            WealthsimpleAPI.appendToFile(log,logFile)
                            print ('Purchase Logged to file...')
                        # If there are already holdings of this security average down according to configuration
                        else:
                            # print ("Already holding time to average down...")
                            # print ("AverageDownAdjustment :" + str(averageDownAdjustment))
                            if (float(holdings['Average_Price'])>float(latestPrice)+averageDownAdjustment):
                                if (sharesToBuy!=0):
                                    # print ("Good to average down...")                         
                                    WealthsimpleAPI.shootMarketOrderRegularAccount(securityID_check,latestPrice*1.01,sharesToBuy)
                                    WealthsimpleAPI.getAccounts()
                                    log="BUY_AVERAGE_DOWN,"+str(securityID_check)+','+str(latestPrice)+','+str(sharesToBuy)+','+str(current_time)
                                    WealthsimpleAPI.appendToFile(log,logFile)
                                    print ('Purchase (AVG DOWN) Logged to file...')
                    # If classification is SELL
                    elif (classification==2):
                        # Checking if we are actually holding the selected securities
                        if (-1!=holdings):
                            averagePrice=holdings['Average_Price']
                            if (float(averagePrice)<float(latestPrice)-minProfit):
                                sharesInAccount=holdings['Quantity']
                                WealthsimpleAPI.shootMarketOrderRegularAccount_Sell(securityID_check,latestPrice,sharesInAccount)
                                log="SELL,"+str(securityID_check)+','+str(latestPrice)+','+str(sharesToBuy)+','+str(current_time)+','+str(holdings['Profit'])
                                WealthsimpleAPI.appendToFile(log,logFile)
                                # Appending to profit log file
                                WealthsimpleAPI.appendToFile(str(todaysDate)+" , "+str(holdings['Profit']),profitLogFile)
                                print ('Sale Logged to file...')
                f.close()
                if (len(prices)<101):
                    messageBox+="Not enough data points currently at : "+str(len(prices))+'\n'
                    holdings=WealthsimpleAPI.getSpecificHoldings(securityID_check)
                    if (holdings!=-1):
                        messageBox+=("\nCurrent Profit/Loss: "+ str(holdings['Profit']))+'\n'
                        messageBox+=("Shares In Account: "+ str(holdings['Quantity']))+'\n'
                        messageBox+=("Percent: "+str (holdings['Percent']))+'\n'

                # Showing Changes/Updates + Resetting display box
                WealthsimpleAPI.print_msg_box(messageBox)
                messageBox=""
            else:
                print ("Trading disabled for this security...")
                print (output)
        except:
            print ("Trying to sign in again, session has likely timed out...")
            WealthsimpleAPI.loginWith2FA(email,password)
            time.sleep(5)
    # Waiting for 20 seconds after all requests
    time.sleep(20)

print ("Looks like the markets aren't open right now (or have just closed)...")