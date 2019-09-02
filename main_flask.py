from master_database import MasterDatabase

from flask import Flask, redirect, url_for, render_template
app = Flask(__name__)

database = MasterDatabase()


@app.route('/')
def main_page():
    return render_template('main.html', series=database.series)


@app.route('/series/<string:series_name>')
def series_page(series_name):
    if series_name in database.series:
        return render_template('series_page.html', series=database.series[series_name])
    else:
        return redirect(url_for('main_page'))


if __name__ == '__main__':
    app.run()
