"""
Main entry point for Flask web application
"""

from flask import Flask, redirect, url_for, render_template, send_from_directory

import pathlib

from database import MasterDatabase
import database.utils as utils
import database.utils.plotting as plotting

app = Flask(__name__)
app.jinja_env.globals.update(format_time=utils.format_time)

database = MasterDatabase(input_folder=pathlib.Path(__file__).parent / 'input')
database.update_statistics()


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
        series_list=list(reversed(list(database.series.values()))),
        fleets_list=list(database.fleets.values()))


@app.route('/series/<string:series_name>')
def series_page(series_name: str):
    if series_name in database.series:
        return render_template(
            'series_page.html',
            database=database,
            series=database.series[series_name])
    else:
        return redirect(url_for('index_page'))


@app.route('/series/<string:series_name>/<int:race_index>')
def race_page(series_name: str, race_index: int):
    if series_name in database.series or race_index > len(database.series[series_name].races):
        return render_template(
            'race_page.html',
            database=database,
            series=database.series[series_name],
            race_index=race_index)
    else:
        return redirect(url_for('index_page'))


@app.route('/fleet/<string:fleet_name>')
def fleet_page(fleet_name: str):
    if fleet_name in database.fleets:
        fleet = database.fleets[fleet_name]
        return render_template(
            'fleet_page.html',
            database=database,
            fleet=fleet)
    else:
        return redirect(url_for('index_page'))


@app.route('/fleet/<string:fleet_name>/boats/<string:boat_code>')
def boat_page(fleet_name: str, boat_code: str):
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
                fleet=fleet)
    else:
        return redirect(url_for('index_page'))


@app.route('/skippers')
def skipper_page_all():
    return render_template(
        'skippers_page_all.html',
        database=database)


@app.route('/skippers/<string:skipper_name>')
def skipper_page_ind(skipper_name: str):
    return render_template(
        'skippers_page_individual.html',
        database=database,
        skipper_name=skipper_name)


if __name__ == '__main__':
    # Initialize plotting (if available) and run
    plotting.get_pyplot()
    app.run()
