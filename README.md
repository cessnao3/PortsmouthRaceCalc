# Portsmouth Yardstick Race Calculator

This program provides a basic Portsmouth Yardstick sailboat race calculator and race scoring program.

## Input Files

Input files consist of the skippers, the precalculated boat table, and race information. These go in the main `input` folder.

The default fleet input is based on the Portsmouth Yardstick 2017 precalculated tables, as calculated by US Sailing in their [2017 Portsmouth Precalculated Classes](https://www.ussailing.org/wp-content/uploads/2018/01/2017-Portsmouth-Precalculated-Classes.pdf) document, but other table entries with different Beaufort number maps may be added to expand the program.

## Running the Program

The program may be run in two different ways. The `main.py` file runs the race calculations and provides a text output to the console. The `app.py` file runs a Flask application such that the race information and series scoring is output in a web browser. This also allows for plots and other graphical representations of the scoring to be performed.

## Scoring Methodology

For finished times, boats are handicapted based on the [Portsmouth Yardstick](https://www.ussailing.org/wp-content/uploads/2018/01/2017-North-American-Portsmouth-Yardstick-Handbook.pdf) to produce a "comparable" score. This final time is then used to determine the ranking of skippers in a race.

*Todo*
