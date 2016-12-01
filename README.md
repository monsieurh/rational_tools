#rational_tools
A set of tools for rational thinking

##foreword
This is a work in progress, and I'm actively looking for suggestions/ideas/improvements. Don't hesitate to open an issue.

All tools work with in a command line interface with python3.5+. They all have a `-h`/`--help` flag, just run it if you don't know what to do.

#tools
##predict.py
Keeps track of predictions and their quality. Predictions can not be modified once emitted. (Actually only the tags and the proof can). Computes the brier score on all or a subset of predictions.
### sample
```
usage: predict.py [-h] [-v] {add,edit,show,list,solve,stats,del} ...

predict.py : a python command line tool to note and test the accuracy of your
predictions

positional arguments:
  {add,edit,show,list,solve,stats,del}
                        Available commands:
    add                 Adds a new prediction
    edit                Edits tags and proof of a prediction
    show                Shows full details of a prediction
    list                Lists predictions in one-line format
    solve               Solves predictions that have come to term
    stats               Prints various statistics
    del                 Deletes a prediction

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
```




#todo
- have `predict.py` handle third-party proof of emission (twitter ? archive.org ? bitcoin?)
- publish to pip
- cleanup `today.py`
- cleanup `dataself.py`
