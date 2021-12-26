from flask import Flask, request, json
from flask_restful import Api, Resource
from datetime import datetime

app = Flask(__name__)
api = Api(app)

# in-memory database of transactions and points
transactions = []
points = {}

# blocks of points that are available to be spent
earliest = []

# variable to keep track of last scanned points
indices_checked = []

"""
Adds a transaction to the list of transactions in chronological order.
If duplicate exists, returns 409 error.
Otherwise, inserts the transaction and returns 201.
"""
def addTransaction(txn):
    if transactions:
            # if list is already populated, find a spot to insert
            for i, t in enumerate(transactions):
                # parse the timestamp of the txn to be inserted
                txn_ts = datetime.strptime(txn['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                # parse the timestamp of the txn in the list
                existing_ts = datetime.strptime(t['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                
                
                if txn_ts < existing_ts:
                    # found correct spot to insert
                    transactions.insert(i, txn)
                    err = 201
                    break
                if i == len(transactions) - 1:
                    # reached end of list, insert at end
                    transactions.append(txn)
                    err = 201
                    break     
    else:
        # insert at beginning of empty list
        transactions.append(txn)
        err = 201
    # update points tally
    if err == 201:
        if txn['payer'] not in points.keys():
            points[txn['payer']] = txn['points']
        else:
            points[txn['payer']] += txn['points']


class Transactions(Resource):
    def post(self):
        err = 409
        txn = request.json if request.json else json.loads(request.data)
        addTransaction(txn)
        return err

"""
Method to scan list of transactions and find indices of earliest available points
Searches for inflection points in the list of transactions
Adds blocks of points to the list once inflection points are found
If certain transactions have already been scanned, scans from that point onwards
Assumes adding transactions will never make points negative
Assumes first transaction cannot be negative
"""   
def update_earliest(ind):
    # example tracker:
    # { DANNON: {'positive': False, 'points': 0, 'index': None} 
    #   UNILEVER: {'positive': False, 'points': 0, 'index': None}
    #   MILLER COORS: {'positive': False, 'points': 0, 'index': None}
    # }
    temp_tracker = {k: {'positive': False, 'points': 0, 'index': None} for k in points.keys()}
    for i, txn in enumerate(transactions[ind:]):
        indices_checked.append(i)

        # initiate first block of points and start scanning
        if temp_tracker[txn['payer']]['index'] == None:
            temp_tracker[txn['payer']]['points'] += txn['points']
            temp_tracker[txn['payer']]['index'] = i
            temp_tracker[txn['payer']]['positive'] = True
            continue
        
        # check for inflection point
        if txn['points'] > 0 and temp_tracker[txn['payer']]['positive'] == False:
            # dispatch block of points to list of earliest points
            earliest.append({'payer': txn['payer'], 'points': temp_tracker[txn['payer']]['points'], 'index': temp_tracker[txn['payer']]['index']})
            temp_tracker[txn['payer']]['points'] = txn['points']
            temp_tracker[txn['payer']]['index'] = i
            temp_tracker[txn['payer']]['positive'] = True
            continue
        # if no inflection point and no initialization required, add or subtract points as indicated by transaction
        temp_tracker[txn['payer']]['points'] += txn['points']
        temp_tracker[txn['payer']]['positive'] = True if txn['points'] > 0 else False
        
    # close out any remaining blocks of points    
    for payer, tracking_dict in temp_tracker.items():
        if tracking_dict['index'] != None:
            earliest.append({'payer': payer, 'points': tracking_dict['points'], 'index': tracking_dict['index']})

    # sort by indices to get order of points to be spent
    earliest.sort(key=lambda x: x['index'])

class Points(Resource):
    def get(self):
        if points:
            return points
        else:
            return 404

    def post(self):
        # spend points
        spend_json = request.json if request.json else json.loads(request.data)
        points_to_spend = spend_json['points']
        points_spent = 0
        spend_response = {k: 0 for k in points.keys()}
        #points_available = {k: v for k, v in points.items()}
        
        # exit with error if requested points are greater than available points
        if points_to_spend > sum(points.values()):
            return 400
        
        # if list of earliest points is empty, generate it starting from the beginning
        # if not, start from the last point scanned
        if not earliest:
            update_earliest(0)
        else:
            update_earliest(indices_checked[-1])

        # go through points list and spent points
        for i, e in enumerate(earliest):
            # skip entry if block is already spent
            if e['points'] < 0:
                continue

            # if points are available, spend them
            # if request exceeds points available in current block, spend all available points
            if points_spent + e['points'] <= points_to_spend:
                points_spent += e['points']
                spend_response[e['payer']] = e['points']
                points[e['payer']] -= e['points']
                earliest[i]['points'] = 0
            else:
                # if request can be satisfied with points in current block, spend necessary points
                spend_response[e['payer']] = points_to_spend - points_spent
                points[e['payer']] -= points_to_spend - points_spent
                earliest[i]['points'] = e['points'] - (points_to_spend - points_spent)
                break

        return [{'payer': k, 'points': -v} for k, v in spend_response.items()]

            

api.add_resource(Transactions, '/transactions')
api.add_resource(Points, '/points')

if __name__ == '__main__':
    app.run(debug=True)