##################################################################################################################
##################################################################################################################
##################################################################################################################
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt
from dateutil.relativedelta import relativedelta

# The relativedelta type is designed to be applied to an existing datetime and can replace specific components of that datetime, or represents an interval of time.
# relativedelta(datetime1, datetime2)  <----lucky find 

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# Reflect an existing database into a new model.
Base = automap_base()
# Reflect the tables.
Base.prepare(engine, reflect=True)

# Save reference to the tables.
Measurement = Base.classes.measurement
Station = Base.classes.station


#################################################
# Flask Setup
#################################################
app = Flask(__name__)


################################################
# Flask Routes
################################################

@app.route("/")
def welcome():
    "available api routes."
    return (
        f"<h1>The Climate API</h1>"
        f"<h1>Climate App</h1>"
        f"This is an API for Climate Analysis .<br/><br/><br/>"
        # f" <img width='600' src='sqlalchemy-challenge\Resources\surfs-up.png'/>"
        f"<h2>Here are the available routes:</h2>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"

        #############################################
        # Adding Hyperlinks to Routes for easy access
        #############################################

        f"<h2>Hyperlinks for routes available below:</h2>"
        f"<ol><li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"JSON list of prcp amounts by date for the most recent year of data available</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"JSON list of weather stations</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"JSON list of the last 12 months of temperatures</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2017-08-23>"
        f"When given the start date (YYYY-M-D), calculates the min, avg, and max temperature for all dates greater than and equal to the start date</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23>"
        f"When given the start and the end date (YYYY-MM-DD), calculate the min, avg, and max temperature for dates between the start and end dates provided</a></li></ol><br/>"
      
    )
##################################################################################################################
##################################################################################################################
@app.route("/api/v1.0/precipitation")
def precipitation():
    "Query to retrieve the last 12 months of precipitation data and return the results."
     # Create session link
    session = Session(engine)

    # Calculate the date 1 year from the last data point in the database.
    last_measurement_data_point_tuple = session.query(
    Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    # Perform a query to retrieve the data and prcp scores.
    data_from_last_year = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= date_year_ago).all()

    session.close()

    # Convert the query results to a dictionary using date as the key and prcp as the value.
    all_prcp = []
    for date, prcp in data_from_last_year:
        if prcp != None:
            precip_dict = {}
            precip_dict[date] = prcp
            all_prcp.append(precip_dict)

    # Return the JSON dictionary.
    return jsonify(all_prcp)
##################################################################################################################
##################################################################################################################
@app.route("/api/v1.0/tobs")
def tobs():
    "Query for the dates and temperature observations from a year from the last data point for the most active station."
    # Create session link
    session = Session(engine)

    # Calculate the date 1 year from the last data point in the database.
    last_measurement_data_point= session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    # Find the most active station.
    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).\
        first()

    # Get the station id of the most active station.
    (most_active_station_id, ) = most_active_station
    print(
        f"Station id of the most active station is {most_active_station_id}.")

    # Perform a query to retrieve the data and temperature scores for the most active station from the year before.
    data_from_last_year = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station_id).filter(Measurement.date >= date_year_ago).all()

    session.close()

    # Convert the query dictionary using date as the key and temp as the value.
    all_temperatures = []
    for date, temp in data_from_last_year:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            all_temperatures.append(temp_dict)
    # Return the JSON dictionary.
    return jsonify(all_temperatures)
##################################################################################################################
##################################################################################################################
@app.route("/api/v1.0/stations")
def stations():
    "Return a JSON list of stations from the dataset."
    # Create session link
    session = Session(engine)

    # Query stations.
    stations = session.query(Station.station, Station.name,
                             Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Convert to dictionary.
    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    # Return the JSON dictionary.
    return jsonify(all_stations)
##################################################################################################################
##################################################################################################################
@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def determine_temps_for_date_range(start, end):
    "Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."
    "When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date."
    "When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive."
      # Create session link
    session = Session(engine)

    # If we have both a start date and an end date.
    if end != None:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).filter(
            Measurement.date <= end).all()
    # If we only have a start date.
    else:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()

    session.close()

    # Convert the query to a list.
    temp_list = []
    no_temp_data = False
    for tMin, tAVG, tMax in temperature_data:
        if tMin == None or tAVG == None or tMax == None:
            no_temp_data = True
        temp_list.append(tMin)
        temp_list.append(tMax)
        temp_list.append(tAVG)
    # Return the JSON dictionary.
    if no_temp_data == True:
        return f"No temperature data found for the given date range. Try another date range."
    else:
        return jsonify(temp_list)


if __name__ == '__main__':
    app.run(debug=True)
##################################################################################################################
##################################################################################################################
##################################################################################################################
##################################################################################################################


