#!/usr/bin/env python2
"""
This script generates db/abbrev?.bib from db/abbrev.bibyml.
This script needs to be run in the root folder containing the
folders "lib" and "db"
"""

import sys
import os
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import bibyml
import logging

import header
import config
from config import *

logging.basicConfig(level=logging.DEBUG)

def get_value(d, short=0):
    #: key to search for value (in the bibyml) depending on the wanted version short
    keys = {
        0: ["@0", ""],
        1: ["@1", "@0", ""],
        2: ["@2", "@0", ""],
        3: ["@3", "@2", "@1", ""],
    }

    for k in keys[short]:
        if k in d:
            if k == "":
                return d[k]
            else:
                return d[k][""]
    return None

def gen(out, abbrev, short=0):
    def write_abbrev(d, path=[]):
        val = get_value(d, short=short)
        if val != None:
            key = "".join(path)
            out.write("@string{{{} = {}{}}}\n".format(
                key, 
                " "*(max(0, 32-len(key)-11)), 
                val
            ))
        for k,v in d.items():
            if k in ["", "@0", "@1", "@2", "@3"]:
                continue
            write_abbrev(v, path+[k])


    out.write(header.get_header(config, "gen.py"))

    write_abbrev(abbrev)

def main():
    abbrev = bibyml.parse(file("db/abbrev.bibyml"))
    for short in range(4):
        with open("db/abbrev{}.bib".format(short), "w") as out:
            gen(out, abbrev, short=short)

if __name__ == "__main__":
    main()
