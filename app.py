"""
Main entry point for Flask web application
"""

from master_database import MasterDatabase

from flask import Flask, redirect, url_for, render_template, send_from_directory
import race_utils

app = Flask(__name__)
app.jinja_env.globals.update(format_time=race_utils.format_time)

database = MasterDatabase()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        'static',
        'favicon.ico')


@app.route('/')
def index_page():
    return render_template(
        'index.html',
        database=database,
        series_list=list(reversed(database.series.values())),
        fleets_list=list(database.fleets.values()))


@app.route('/series/<string:series_name>')
def series_page(series_name):
    if series_name in database.series:
        return render_template(
            'series_page.html',
            database=database,
            series=database.series[series_name])
    else:
        return redirect(url_for('index_page'))


@app.route('/series/<string:series_name>/<int:race_index>')
def race_page(series_name, race_index):
    if series_name in database.series or race_index > len(database.series[series_name].races):
        return render_template(
            'race_page.html',
            database=database,
            series=database.series[series_name],
            race_index=race_index)
    else:
        return redirect(url_for('index_page'))


@app.route('/fleet/<string:fleet_name>')
def fleet_page(fleet_name):
    if fleet_name in database.fleets:
        fleet = database.fleets[fleet_name]
        return render_template(
            'fleet_page.html',
            database=database,
            fleet=fleet)
    else:
        return redirect(url_for('index_page'))


@app.route('/fleet/<string:fleet_name>/boats/<string:boat_code>')
def boat_page(fleet_name, boat_code):
    if fleet_name in database.fleets:
        fleet = database.fleets[fleet_name]
        boat = fleet.get_boat(boat_code)

        if boat is None:
            return redirect(url_for('index_page'))
        else:
            return render_template(
                'boat_page.html',
                database=database,
                boat=boat,
                fleet_name=fleet_name)
    else:
        return redirect(url_for('index_page'))


if __name__ == '__main__':
    # Initialize plotting (if available) and run
    race_utils.get_pyplot()
    app.run()

