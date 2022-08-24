# WealthsimpleBot

First upload of ongoing stock trading bot, readme will be updated in the near future with information about usage + tips

Notes:
- The codebase is still VERY messy, lots of refactoring needs to be done BUT-> the bot is functional
- Runs on the same neural network as the KrakenBot. (with a few more safeguards)
- Currently set up to run on CAD denominated accounts (non tfsa) only.
- Works best on stocks with a lot of liquidity (At least 300k shares/day average)
- Needs 101 data points before it starts trading (makes requests every 20 seconds so ~10:04AM the bot will begin making trades)
- WS uses internal security ID's for stocks, some are provided in the 'Security ID.txt' file, you can find these yourself by going to Wealthsimple's web page and inspecting network activity (this is how many of the endpoints for this program were found as well)
- WS needs to be authenticated every 2 hours, current bot is setup with automatic 2fa from a chrome plugin. 2fa can be disabled in WS or the code can be manually entered every 2 hours 
- Update the configuration file as required, for the two people that check this out just call me I'll help you with it

General Strategy:
- Market buy liquid stocks with a given % of portfolio, average into position and sell at scaled amounts depending on overall percentage of portfolio currently allocated.
- Default sell configuration is that with 15% of portfolio allocated the bot will sell if price is >= avg cost + 0.15, scaling up to 0.53 at >90% of portfolio allocated. 
- Default buy configuration is that with 15% of portfolio in, the bot will average down if the price is 0.2 under the average cost, scaling up to 1.5 under average cost at 90% of portfolio in.
- Trades based on NN image classification

Tips:
- Liquid stocks only
- Bring down the % of portfolio to use initially 
- Set up 2fa on local device and configure login function accordingly
- Trade things you wouldn't mind bagholding for years
- WS will disconnect you if you do more than 7 in an hour, if this happens just wait a bit
- Program will not start on saturday and sunday (and most holidays?)

Comments:
- It works well enough, I'm having fun with it 

