# Updated_IPD_Nueva

## information

Updated Code Base for MicroEconomics Iterated Prisoner's Dilemma simulation.

* to block people's submissions, add names to "blocked_submissions.txt"
* to block individual strategies, add function names to "blocked_functions.txt"

This version is pulled from <https://github.com/AleTuch17/Updated_IPD_Nueva>, which was pulled from <https://github.com/annliz/IPD>. Major changes can be seen in commit history, but here is a list:

* features / bug fixes
  * gave around 10x speed up to the code by moving 'suppress_stdout' to an outer layer of the code
  * added ability to block indivdual functions
  * added more statistics when running the code to see what functions were disallowed
  * added the name of the function as a global variable in the check functions funciton and in the simulation; its absence was preventing some of the functions from running
  * added a tests.py to test parts of the simulation
  * added test cases to check functions
* qol / maintainability
  * fixed the typing problems (originally there were a ton of warnings)
  * removed some "import *" statements 
  * changed variable, funciton, and file names to be more intuitive
  * updated .gitignore
  * removed disfunctional command line parsing
  * fixed get_scores (it used to return the reversed results)
  * formatted code with black formatter
  * changed default functions' to use snake case (the best case)

## to run

Documentation found here: <https://docs.google.com/document/d/1JOLhksun38wb1Sgl5Nyap8-G7bx3RATD8Qso5tgEUFE/edit>

## to test

`python tests.py` or `python3 tests.py`

## todo

* why are we importing everything from our modules
* put control settings in a class (not as important)
* add seciton for functions that should be run single threadedly
  * maybe automatically test which functions should be run like that?
* redo command line parsing
* export the pairwise as csv too
* parse strategies from each file, turn them into lists of individual functions to import individually
  * some pastebins were all dying because some of the functions had syntax errors
  * change the maximum number of funcitons to only load the first 10 instead of just killing the pastebin
