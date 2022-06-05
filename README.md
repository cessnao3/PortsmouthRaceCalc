# Portsmouth Yardstick Race Calculator

This program provides a basic Portsmouth Yardstick sailboat race calculator and race scoring program.

## Input Files

Input files consist of the skippers, the precalculated boat table, and race information. These go in the main `input` folder.

The default fleet input is based on the Portsmouth Yardstick 2017 precalculated tables, as calculated by US Sailing in their [2017 Portsmouth Precalculated Classes](https://www.ussailing.org/wp-content/uploads/2018/01/2017-Portsmouth-Precalculated-Classes.pdf) document, but other table entries with different Beaufort number maps may be added to expand the program.

## Running the Program

The program may be run in two different ways. The `main.py` file runs the race calculations and provides a text output to the console. The `build.py` file generates static HTML such that the race information and series scoring can be viewed in a web browser. This also allows for plots and other graphical representations of the scoring to be performed.

## Scoring Methodology

For finished times, boats are handicapped based on the [Portsmouth Yardstick](https://www.ussailing.org/wp-content/uploads/2018/01/2017-North-American-Portsmouth-Yardstick-Handbook.pdf) to produce a "comparable" score. This final time is then used to determine the ranking of skippers in a race.

The excerpts from the JCSS rulebook relating to the scoring of the 
1. The Low Point System of Appendix A of the racing rules will apply.
st
2. 1 place 1 point; second place, 2 points; third place, 3 points, etc.
3. Only yachts with a consistent skipper throughout the series, who is a member in good standing of JCSS, will be assigned finishing places for the purpose of series points.
4. A yacht must race the number of times required in the series description to qualify for that series.
5. A yacht that did not finish (DNF) shall score points for the finishing place equal to the number of active yachts within its fleet whose entry for that race has been accepted. (On that race day).
6. A yacht that is disqualified (DSQ) after finishing shall score points for the finishing place equal to the number of active yachts plus two within its fleet whose entry for that race has been accepted. (On that race day).
7. A yacht that did not start (DNS) shall not be scored.
8. Skippers serving on Race Committee (RC) shall score points equal to the average, to the nearest tenth of a point, of his or her points in all races in the series, except for the worst race, or as a “DNF” for races committee’d, whichever is less.
9. Skippers shall be credited with those races he or she conducted as Committee for the purposes of “3” (# of races to qualify) above. No skipper shall receive credit as RC member on more than two races in a series, excepting when that skipper serves as race committee member during a makeup race day, when 3 races may be sailed.
10. Series Ties will be handled by Appendix A paragraph 8 of the Racing Rules of sailing summarized below. If there is a series-score tie between two or more boats, each boat’s race scores shall be listed in order of best to worst, and at the first point(s) where there is a difference the tie shall be broken in favor of the boat(s) with the best score(s). No excluded scores shall be used. If a tie remains between two or more boats, they shall be ranked in order of their scores in the last race. Any remaining ties shall be broken by using the tied boats’ scores in the next-to-last race and so on until all ties are broken. These scores shall be used even if some of them are excluded scores.

Notes:
- Scores are rounded to the nearest tenth decimal place.
- There may be errors or unimplemented features in the scoring as it currently stands - please verify the output against the above rules to ensure that races are computed correctly.
