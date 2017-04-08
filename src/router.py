import sys
import json
import datetime

from flask import request
from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource
from flask_sqlalchemy import SQLAlchemy

from geopy.distance import great_circle

from model import Pslot, Reservation

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://test:test@localhost/test'
db = SQLAlchemy(app)

# MySQL Init
# app.config['MYSQL_DATABASE_USER'] = 'test'
# app.config['MYSQL_DATABASE_PASSWORD'] = 'test'
# app.config['MYSQL_DATABASE_DB'] = 'test'
# app.config['MYSQL_DATABASE_HOST'] = 'localhost'

class ParkingSlots(Resource):

    GET_REQ_TYPE_ALL = "GET_REQ_TYPE_ALL"
    GET_REQ_TYPE_FREE = "GET_REQ_TYPE_FREE"
    GET_REQ_TYPE_RADIUS = "GET_REQ_TYPE_RADIUS"

    def get(self):

        request_type, a_d = self.getRequestType()

        rows = []
        if request_type == ParkingSlots.GET_REQ_TYPE_FREE:
            rows = self.getFree()
        elif request_type == ParkingSlots.GET_REQ_TYPE_RADIUS:
            rows = self.getRadiusFree(a_d['lat'], a_d['lng'], a_d['radius'])
        else:
            rows = self.getAll()

        return self.toJson(rows)

    def getRequestType(self):

        # Did the user specify state=free?
        URL_PARAM_TAG_LAT = 'lat'
        URL_PARAM_TAG_LNG = 'lng'
        URL_PARAM_TAG_STATE = 'state'
        URL_PARAM_TAG_RADIUS = 'radius'

        request_type = ParkingSlots.GET_REQ_TYPE_ALL
        arg_dict = request.args.to_dict()

        rdict = {}
        # GET_REQ_TYPE_RADIUS
        if (URL_PARAM_TAG_LAT in arg_dict) \
           and (URL_PARAM_TAG_LNG in arg_dict) \
           and (URL_PARAM_TAG_STATE in arg_dict) \
           and (URL_PARAM_TAG_RADIUS in arg_dict):

           # Type Checking
           try:
               rdict[URL_PARAM_TAG_LAT] = float(arg_dict[URL_PARAM_TAG_LAT])
               rdict[URL_PARAM_TAG_LNG] = float(arg_dict[URL_PARAM_TAG_LNG])
               rdict[URL_PARAM_TAG_STATE] = str(arg_dict[URL_PARAM_TAG_STATE])
               rdict[URL_PARAM_TAG_RADIUS] = float(arg_dict[URL_PARAM_TAG_RADIUS])
               if rdict[URL_PARAM_TAG_STATE].lower() == "free":
                   request_type = ParkingSlots.GET_REQ_TYPE_RADIUS
           except:
               print "Exce: ", sys.exc_info()
        elif (URL_PARAM_TAG_STATE in arg_dict):

           # Type & Range Checking
           try:
               rdict[URL_PARAM_TAG_STATE] = str(arg_dict[URL_PARAM_TAG_STATE])
               if rdict[URL_PARAM_TAG_STATE].lower() == "free":
                   request_type = ParkingSlots.GET_REQ_TYPE_FREE
           except:
               print "Exce: ", sys.exc_info()

        return request_type, rdict

    def getAll(self):
        return Pslot.query.all()

    def getFree(self):
        pass

    def getRadiusFree(self, lat, lng, radius):

        pslots = self.getAll()

        # Loop through to find which one's are in radius
        rvalue = []
        target = tuple([lat, lng])
        for row in pslots:
            current = tuple([row.lat, row.lng])
            distance = great_circle(target, current).miles
            if distance <= radius:
                rvalue.append(row)

        # Exclude if they are already booked
        for row in rvalue:

            resvs = Reservation.query.filter_by(psid=row.psid).all()

            if len(resvs) == 0:
                # No Reservation for this slot, it's avilable
                continue
            else:
                for resv in resvs:
                    # Check if it's already booked
                    ct = datetime.datetime.now()
                    if  (ct >= resv.startts) \
                    and (ct <= resv.endts):
                        rvalue.remove(row)

        return rvalue

    def toJson(self, rows):

        if not isinstance(rows, list):
            return None

        data = []
        for row in rows:
            try:
                data.append( {"lat": float(row.lat), "lng": float(row.lng), "psid": row.psid})
            except:
                continue

        return jsonify({"data": data})

def bad_request(message):
    response = jsonify({'message': message})
    response.status_code = 400
    return response

class Reservations(Resource):

    def post(self):

        print "1"

        # Check for mandatory parameters and type
        mandatory_params = [ 'slot_id',
                             'end_ts',
                             'start_ts']

        print "J: ", request.get_json()
        request_dict = dict(request.get_json())
        print "R: ", request_dict
        for k in mandatory_params:
            if (not k in request_dict):
                return bad_request('Manadatory parameter missing. Paramter name: ' + k)
        print "All Man Passed"

        try:
            slot_id = int(request_dict['slot_id'])
            end_ts = str(request_dict['end_ts'])
            start_ts = str(request_dict['start_ts'])
        except:
            return bad_request('Manadatory parameter incorrect type')

        return jsonify(request_dict)

    def get(self):
        return self.toJson(Reservation.query.all())

    def toJson(self, rows):

        if not isinstance(rows, list):
            return jsonify({"data": []})

        data = []
        for row in rows:
            try:
                data.append( {"rid": row.rid, "psid":row.psid, "start_ts":row.startts, "end_ts:":row.endts})
            except:
                continue

        return jsonify({"data":data})

api.add_resource(Reservations, '/v1/reservations')
api.add_resource(ParkingSlots, '/v1/parking-slots')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
