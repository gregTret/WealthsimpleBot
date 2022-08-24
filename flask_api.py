from flask_cors import CORS, cross_origin
from flask import Flask, jsonify, request
from flask.helpers import make_response
from WealthsimpleBot import WealthsimpleAPI as WealthsimpleAPI

# Initializing App
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/refresh', methods=['GET'])
def refreshSession():
    response = WealthsimpleAPI.refreshSession()
    if (response == 1):
        return make_response(jsonify({'Status': "Successfully Refreshed Session"}), 200)
    else:
        return make_response(jsonify({'Status': "Failed to refresh session"}), 404)


@app.route('/latestPrice', methods=['GET'])
def latestPrice():
    # Real time pricing
    ticker = request.args.get('ticker', default='SPY', type=str)
    id = WealthsimpleAPI.getSecurityID(ticker)
    result = WealthsimpleAPI.realTimeSecurityPrice(id)
    return make_response(jsonify({'symbol': result[0], 'price': result[1], 'currency': result[2]}), 200)

@app.route('/latestPriceByID', methods=['GET'])
def latestPriceByID():
    # Real time pricing
    id = request.args.get('id', default='', type=str)
    result = WealthsimpleAPI.realTimeSecurityPrice(id)
    return make_response(jsonify({'symbol': result[0], 'price': result[1], 'currency': result[2]}), 200)

# Get specific security information
@app.route('/getSecurityInformation')
def check():
    id = request.args.get('security', default='', type=str)
    info = WealthsimpleAPI.getInfoByID(id)
    return make_response(jsonify({'information': info}), 200)

@app.route('/holdings')
def account():
    info = WealthsimpleAPI.getAccountHoldings()
    return make_response(jsonify({'positions': info}), 200)

@app.route('/holdingsTFSA')
def accountTFSA():
    result = WealthsimpleAPI.getAccountHoldingsTFSA()
    return make_response(jsonify({'positions': result}), 200)

@app.route('/rebalanceTFSA')
def rebalance():
    before = WealthsimpleAPI.getAccountHoldingsTFSA()
    tickers_TFSA=[]
    desired_allocation_TFSA=[]
    tickers_TFSA.append("VSP")
    desired_allocation_TFSA.append(.3)
    tickers_TFSA.append("CAR.UN")
    desired_allocation_TFSA.append(.2)
    tickers_TFSA.append("TD")
    desired_allocation_TFSA.append(.3)
    tickers_TFSA.append("XQQ")
    desired_allocation_TFSA.append(.2)
    WealthsimpleAPI.balanceAccount_TFSA(tickers_TFSA,desired_allocation_TFSA)
    after = WealthsimpleAPI.getAccountHoldingsTFSA()
    return make_response(jsonify({'positionBefore': before,'positionAfter':after}), 200)

app.run(port=5000)