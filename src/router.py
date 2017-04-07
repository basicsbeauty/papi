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

class Reservation(Resource):

    def POST(self):

        # Check for mandatory parameters and type
        mandatory_params = { 'slot_id':int,
                             'start_time':}

api.add_resource(ParkingSlots, '/v1/reservations')
api.add_resource(ParkingSlots, '/v1/parking-slots')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
