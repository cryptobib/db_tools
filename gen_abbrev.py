#!/usr/bin/env python3
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
    # we need to do a recursion in the tree defined by the yaml
    def write_abbrev(d, path=[]):
        val = get_value(d, short=short)
        if val is not None:
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


def check_abbrev(abbrev):
    """
    Sanity check that abbrev file
    """

    def check_abbrev0_non_empty_field_if_other_non_empty(d, path=[]):
        """
        Ensure that if non-abbrev0 fields are not empty,
        abbrev0 field is not empty
        """
        vals = [get_value(d, short=s) for s in [0,1,2,3]]

        if any(vals[i] is not None and vals[i] != "" for i in range(1,4)):
            assert vals[0] is not None and vals[0] != "", \
                "field '{}' is non-empty for one non-abbrev0 file but is empty in abbrev0".format("".join(path))

        for k,v in d.items():
            if k in ["", "@0", "@1", "@2", "@3"]:
                continue
            check_abbrev0_non_empty_field_if_other_non_empty(v, path+[k])


    check_abbrev0_non_empty_field_if_other_non_empty(abbrev)


def main():
    abbrev = bibyml.parse(open("db/abbrev.bibyml"))

    check_abbrev(abbrev)

    for short in range(4):
        with open("db/abbrev{}.bib".format(short), "w") as out:
            gen(out, abbrev, short=short)


if __name__ == "__main__":
    main()
