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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

class ParkingSlots(Resource):

    GET_REQ_TYPE_ALL = "GET_REQ_TYPE_ALL"
    GET_REQ_TYPE_RADIUS = "GET_REQ_TYPE_RADIUS"
    GET_REQ_TYPE_RADIUS_FREE = "GET_REQ_TYPE_RADIUS_FREE"

    def get(self):

        a_d = {}
        request_type = str()
        try:
            request_type, a_d = self.getRequestType()
        except ValueError as ve:
            return bad_request(ve.message)
        print "RT: ", request_type
        print "AD: ", a_d

        rows = []
        if request_type == ParkingSlots.GET_REQ_TYPE_RADIUS:
            rows = self.getRadius(a_d['lat'], a_d['lng'], a_d['radius'])
        elif request_type == ParkingSlots.GET_REQ_TYPE_RADIUS_FREE:
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
           and (URL_PARAM_TAG_RADIUS in arg_dict):

           # Type Checking
           try:
               rdict[URL_PARAM_TAG_LAT] = float(arg_dict[URL_PARAM_TAG_LAT])
               rdict[URL_PARAM_TAG_LNG] = float(arg_dict[URL_PARAM_TAG_LNG])
               rdict[URL_PARAM_TAG_RADIUS] = float(arg_dict[URL_PARAM_TAG_RADIUS])
               request_type = ParkingSlots.GET_REQ_TYPE_RADIUS
           except:
               print "Exce: ", sys.exc_info()
               raise ValueError("Paramter: Invalid Type")

           if (URL_PARAM_TAG_STATE in arg_dict):
               try:
                   rdict[URL_PARAM_TAG_STATE] = str(arg_dict[URL_PARAM_TAG_STATE])
                   if rdict[URL_PARAM_TAG_STATE].lower() == "all":
                       request_type = ParkingSlots.GET_REQ_TYPE_RADIUS
                   elif rdict[URL_PARAM_TAG_STATE].lower() == "free":
                       request_type = ParkingSlots.GET_REQ_TYPE_RADIUS_FREE
               except:
                   print "Exce: ", sys.exc_info()
                   raise ValueError("Paramter: Invalid Type")

           # Range checking
           LAT_MAX = 90
           LAT_MIN = -90
           LNG_MAX = 180
           LNG_MIN = -180
           if not ((rdict[URL_PARAM_TAG_LAT] >= LAT_MIN) \
               and (rdict[URL_PARAM_TAG_LAT] <= LAT_MAX) \
               and (rdict[URL_PARAM_TAG_LNG] >= LNG_MIN) \
               and (rdict[URL_PARAM_TAG_LNG] <= LNG_MAX)
               and (rdict[URL_PARAM_TAG_RADIUS] >= 0)):
               raise ValueError("Parameter: Invalid Value")

        elif (URL_PARAM_TAG_STATE in arg_dict):

           # Type & Range Checking
           try:
               rdict[URL_PARAM_TAG_STATE] = str(arg_dict[URL_PARAM_TAG_STATE])
               if rdict[URL_PARAM_TAG_STATE].lower() == "free":
                   request_type = ParkingSlots.GET_REQ_TYPE_FREE
           except:
               print "Exce: ", sys.exc_info()
               raise ValueError("Invalid Type")

        return request_type, rdict

    def getAll(self):
        return Pslot.query.all()

    def getRadius(self, lat, lng, radius):

        pslots = self.getAll()

        # Loop through to find which one's are in radius
        rvalue = []
        target = tuple([lat, lng])
        for row in pslots:
            current = tuple([row.lat, row.lng])
            distance = great_circle(target, current).miles
            # print "T: ", target, " C: ", current, " D: ", distance
            if distance <= radius:
                rvalue.append(row)

        return rvalue

    def getRadiusFree(self, lat, lng, radius):

        rvalue = []
        rvalue = self.getRadius(lat, lng, radius)

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
                data.append( {"lat": float(row.lat), "lng": float(row.lng), "id": row.psid})
            except:
                continue

        return jsonify({"data": data})

class Reservations(Resource):

    def post(self):

        # Check for mandatory parameters and type
        mandatory_params = [ 'id',
                             'end_ts',
                             'start_ts']

        # print "J: ", request.get_json()
        request_dict = dict(request.get_json())
        # print "R: ", request_dict

        # Mandatory paramters checking
        for k in mandatory_params:
            if (not k in request_dict):
                return bad_request('Manadatory parameter missing. Paramter name: ' + k)

        # Type checking
        format = "%Y-%m-%d %H:%M:%S"
        try:
            slot_id = int(request_dict['id'])
            end_ts = datetime.datetime.strptime(request_dict['end_ts'], format)
            start_ts = datetime.datetime.strptime(request_dict['start_ts'], format)
        except ValueError as ve:
            return bad_request('Manadatory parameter incorrect type')

        # Parking Slot: Check validity
        slot = Pslot.query.filter_by(psid=slot_id).first()
        if not slot:
            return bad_request("Parking Slot: %d doesn't exist" % slot_id)

        # Start Time > NOW()
        if start_ts < datetime.datetime.now():
            return bad_request("Start time can't be in the past")

        # Start Time < End Time
        if start_ts > end_ts:
            return bad_request("Start time can't be greater then end time ")

        # There should not any conflicting reservations
        try:
            resvs = []
            resvs = Reservation.query.filter_by(psid=int(slot_id)).all()
            if len(resvs) == 0:
                self.addRow(slot_id, start_ts, end_ts)
            else:
                for record in resvs:
                    print 'C: ST: ', start_ts, ' ET: ', end_ts
                    print 'R: ST: ', record.startts, ' ET: ', record.endts

                    # Overlap check
                    #  - End time in between the current reservation interval
                    #  - Start time in between the current reservation interval
                    #  - New-Start: Current-Start - Current-End: New-End
                    if ((end_ts >= record.startts) and (end_ts <= record.endts)) \
                    or ((start_ts >= record.startts) and (start_ts <= record.endts)) \
                    or ((start_ts <= record.startts) and (end_ts >= record.endts)):
                        return bad_request("Reservation colflict", 400)

                # Passed all the checks: No conflict
                self.addRow(slot_id, start_ts, end_ts)

        except:
            print "E: ", sys.exc_info()
            return bad_request("Internal Error", 500)

        return jsonify({"data":request_dict})

    def addRow(self, slotid, start_ts, end_ts):
        reserv = Reservation(psid=slotid, startts=start_ts, endts=end_ts)
        db.session.add(reserv)
        db.session.commit()
        print "Record Added"

    def get(self):
        rows = []
        print "R: ", rows
        rows = self.getAll()
        return self.toJson(rows)

    def getAll(self):
        db.session.flush()
        rows = []
        print "R: ", Reservation.query.all()
        rows = Reservation.query.all()
        print "R: ", len(Reservation.query.all()), " L: ", len(rows)
        return rows

    def toJson(self, rows):

        if not isinstance(rows, list):
            return jsonify({"data": []})

        data = []
        for row in rows:
            try:
                data.append( {"rid": row.rid, "psid":row.psid, "start_ts":str(row.startts), "end_ts:":str(row.endts)})
            except:
                continue

        return jsonify({"data":data})

    def delete(self, rid):

        # Type checking
        try:
            rid = int(rid)
        except:
            return bad_request("Reservation ID must be a integer")

        # Range checking
        if rid < 1:
            return bad_request("Reservation ID: Invalid value")

        # Check if there a reservation with that Id
        record = Reservation.query.filter_by(rid=rid).all()
        if len(record) == 0:
            return bad_request("Reservation ID: Doesn't exist", 404)
        record = record[0]

        try:
            db.session.query(Reservation).filter(Reservation.rid == record.rid).delete()
            db.session.commit()
            db.session.expire_all()
        except:
            print "Exce: ", sys.exc_info()
            return bad_request("Reservation ID: Delete failed", 500)

        response = jsonify()
        response.status_code = 204
        return response

def bad_request(message, code=400):
    response = jsonify({'message': message})
    response.status_code = code
    return response

api.add_resource(ParkingSlots, '/v1/parking-slots')
api.add_resource(Reservations, '/v1/reservations', '/v1/reservations/<rid>')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
