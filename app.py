from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.pool import SingletonThreadPool
import datetime
import dateutil.relativedelta

# Creating DB connection with mapped classes for queries in sqlalchemy
engine = create_engine("sqlite:///Resources/hawaii.sqlite", poolclass=SingletonThreadPool)
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station

#start Flask App
app = Flask(__name__)


#defined pages in flask app
@app.route("/")
def index_page():
    htmlFile = open('index.html', 'r')
    page = htmlFile.read()
    return (page)

@app.route("/api/v1.0/precipitation")
#TODO Are we to include the station name here as well?
def precip_page():    
    session = Session(engine)
    try:
        precip_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date > '2016-08-22').filter(Measurement.prcp.isnot(None)).all()
        session.close()
        precip_dict = {}
        for item in precip_data:
            precip_item =  {item[0]:item[1]}
            precip_dict.update(precip_item)
        return jsonify(precip_dict)
    except:
         return jsonify({"error": f"Prectipitation data not found."}), 404       

@app.route("/api/v1.0/stations")
def stations_page(): 
    session = Session(engine)
    try:
        stations = session.query(Station.name).all()
        session.close()
        stations_list=[]
        for item in stations:
            _station = item[0]
            stations_list.append(_station)
        station_dict = {'station_name': stations_list}
        return jsonify(station_dict)
    except:
        return jsonify({"error": f"Stations not found."}), 404

@app.route("/api/v1.0/tobs")
def tobs_page(): 
    session = Session(engine)
    get_active_station = session.query(Measurement.station, func.count(Measurement.station)).filter(Measurement.date > year_date())\
        .group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()
    session.close()
    active_station = get_active_station[0]

    session = Session(engine)
    tobs = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date > year_date())\
        .order_by(Measurement.date).all()
    session.close()

    tobs_dict = {}
    for item in tobs:
        tobs_item = {item[0]:item[1]}
        tobs_dict.update(tobs_item)
    tobs_dict_final = [active_station, {'date_temps':tobs_dict}]
    return jsonify(tobs_dict_final)


@app.route("/api/v1.0/<start>")
def temp_stats(start):
    session = Session(engine)
    tempdata = session.query(Station.name, func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))\
            .join(Measurement, Station.station==Measurement.station).filter(Measurement.date >= start).group_by(Station.name).all()
    session.close()
    return jsonify(compile_data(tempdata))

@app.route("/api/v1.0/<start>/<end>")
def temp_stats2(start, end):
    session = Session(engine)
    tempdata = session.query(Station.name, func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs))\
            .join(Measurement, Station.station==Measurement.station).filter(Measurement.date.between(start, end)).group_by(Station.name).all()
    session.close()
    return jsonify(compile_data(tempdata))



def compile_data(tempdata):
    """Function supports temp pages with start and end dates by compiling information into a list of dictionaries."""
    listed=[]
    for item in tempdata:
        listed.append([{'station_name': item[0], 'min_temp': item[1], 
        'max_temp': item[2], 'avg_temp': item[3]}])
    return(listed)

def year_date():
    """Function queries the max date of dataset and returns a date 12 months in the past."""
    session = Session(engine)
    max_date = session.query(func.max(Measurement.date)).first()
    session.close()
    
    d = datetime.datetime.strptime(max_date[0], "%Y-%m-%d")
    d2 = d - dateutil.relativedelta.relativedelta(months=12)
    return d2


if __name__ == "__main__":
    app.run(debug=True)