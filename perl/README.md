# Perl Scoring Program

This folder hosts a copy of the `race_scorer_v04.pl` file as found at [https://github.com/rodinski/sailing/blob/master/race_scorer_v04.pl](https://github.com/rodinski/sailing/blob/master/race_scorer_v04.pl).

As this program was the original JCSS scoring implementation, it is used as a cross-check for this updated implementation.

The `check.py` file in the root directory generates compatible input files for the `race_scorer_v04.pl` Perl variant from the input files. The Perl program is then run, which generates an output dictionary of race results as a YAML file, which can be imported and compared the same results as computed by this program.

If any race result doesn't match, the `check.py` file fails and lists the outputs for debugging, exiting with a non-zero exit code.
