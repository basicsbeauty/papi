# coding: utf-8
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.schema import FetchedValue
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Pslot(db.Model):
    __tablename__ = 'pslot'

    psid = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Numeric(10, 8), nullable=False)
    lng = db.Column(db.Numeric(11, 8), nullable=False)


class Reservation(db.Model):
    __tablename__ = 'reservation'

    rid = db.Column(db.Integer, primary_key=True)
    psid = db.Column(db.ForeignKey(u'pslot.psid', ondelete=u'CASCADE', onupdate=u'CASCADE'), nullable=False, index=True)
    startts = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())
    endts = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())

    pslot = db.relationship(u'Pslot', primaryjoin='Reservation.psid == Pslot.psid', backref=u'reservations')
