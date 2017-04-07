from flask import request
from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource
from flask_mysqldb import MySQL

app = Flask(__name__)
api = Api(app)
mysql = MySQL(app)

class ParkingSlots(Resource):

    def get(self):

        data = {"Test":90}

        # Did the user specify state=free?
        URL_PARAM_TAG_STATE = 'STATE'
        if URL_PARAM_TAG_STATE in request.args:
            print "R: ", type(query_params[URL_PARAM_TAG_STATE])

        # Extract all records from MySQL
        cur = mysql.connection.cursor()
        cur = mysql.execute("select * pslot")

        return jsonify(data)

def bad_request(message):
    response = jsonify({'message': message})
    response.status_code = 400
    return response

class Reservation(Resource):

    def post(self):

        print "1"

        # Check for mandatory parameters and type
        mandatory_params = [ 'slot_id',
                             'start_time',
                             'end_time']
        for v in mandatory_params:
            if (not v in request.args):
                return bad_request('Manadatory parameter missing')

        # Type checking
        # Slot ID
        try:
            slot_id = int(request.args['slot_id'])
            end_ts = str(request.args['end_ts'])
            start_ts = str(request.args['start_ts'])
        except:
            return bad_request('Manadatory parameter missing')

        # Insert record into MySQL


        return jsonify(data)

api.add_resource(Reservation, '/v1/reservations')
api.add_resource(ParkingSlots, '/v1/parking-slots')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
