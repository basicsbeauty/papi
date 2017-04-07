from flask import request
from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource
from flask_mysqldb import MySQL

app = Flask(__name__)
api = Api(app)
mysql = MySQL()

# MySQL Init
app.config['MYSQL_DATABASE_USER'] = 'test'
app.config['MYSQL_DATABASE_PASSWORD'] = 'test'
app.config['MYSQL_DATABASE_DB'] = 'test'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

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
        print "F: ", request.form
        print "F: ", request.form.keys()
        for v in mandatory_params:
            if (not v in request.form.keys()):
                return bad_request('Manadatory parameter missing')

        # Type checking
        # Slot ID
        try:
            slot_id = int(request.form['slot_id'])
            end_ts = str(request.form['end_ts'])
            start_ts = str(request.form['start_ts'])
        except:
            return bad_request('Manadatory parameter incorrect type')

        return jsonify(data)

api.add_resource(Reservation, '/v1/reservations')
api.add_resource(ParkingSlots, '/v1/parking-slots')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
