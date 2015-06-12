#!/bin/env python2
"""
This script generates web/crypto_bib/data/changes.pkl from changes.txt.

changes.txt has to be of the form:

* yyyy-mm-dd
description of change at ...

* yyyy-mm-dd
...
"""

import sys
import os
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import cPickle
import sys
import re
import datetime

import logging

from config import *

logging.basicConfig(level=logging.DEBUG)

_re_date = re.compile(r"^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$")

def main():
    changes = []

    fin = file("changes.txt")
    lineno = 1
    for line in fin:
        if lineno == 1 and line[0] != "*":
            logging.error("Error: the first line has to start by '*'")
            sys.exit(1)
        if line[0] == "*":
            r = _re_date.match(line[1:])
            if r == None:
                logging.error("Error: invalid date on line {}. Date format is yyyy-mm-dd".format(lineno))
                sys.exit(1)
            (yy,mm,dd) = r.groups()
            changes.append((datetime.date(int(yy),int(mm),int(dd)),""))
        else:
            (date_c, desc_c) = changes[-1]
            desc_c = desc_c + line
            changes[-1] = (date_c, desc_c)

        lineno += 1
        
    fin.close()

    # debug only
    #print(repr(changes))
    # end debug only

    out = file("web/app/data/changes.pkl", "w")
    cPickle.dump(changes, out, cPickle.HIGHEST_PROTOCOL)
    out.close()

if __name__ == "__main__":
    main()
