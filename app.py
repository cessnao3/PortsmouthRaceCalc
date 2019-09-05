"""
Main entry point for Flask web application
"""

from master_database import MasterDatabase

from flask import Flask, redirect, url_for, render_template
app = Flask(__name__)

database = MasterDatabase()


@app.route('/')
def main_page():
    return render_template('main.html', series=database.series, fleets=database.fleets)


@app.route('/series/<string:series_name>')
def series_page(series_name):
    if series_name in database.series:
        return render_template('series_page.html', series=database.series[series_name])
    else:
        return redirect(url_for('main_page'))


@app.route('/fleet/<string:fleet_name>')
def fleet_page(fleet_name):
    if fleet_name in database.fleets:
        fleet = database.fleets[fleet_name]
        return render_template('fleet_page.html', fleet=fleet)
    else:
        return redirect(url_for('main_page'))


@app.route('/fleet/<string:fleet_name>/boats/<string:boat_code>')
def boat_page(fleet_name, boat_code):
    if fleet_name in database.fleets:
        fleet = database.fleets[fleet_name]
        boat = fleet.get_boat(boat_code)

        if boat is None:
            return redirect(url_for('main_page'))
        else:
            return render_template('boat_page.html', boat=boat, fleet_name=fleet_name)
    else:
        return redirect(url_for('main_page'))


if __name__ == '__main__':
    app.run()
