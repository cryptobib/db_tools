#!/usr/bin/env python3
"""
This script needs to be run in the root folder containing the
folders "lib" and "db"
"""

import sys
import os

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import mybibtex.parser
import mybibtex.generator
import confs_years

import logging
import shutil
import argparse
import time

import config
from config import *

mybibtex.generator.config = config
logging.basicConfig(level=logging.DEBUG)


def add(filenames: list[str]):
    parser = mybibtex.parser.Parser()
    parser.parse_file("db/abbrev0.bib")
    parser.parse_file("db/crypto_db.bib")
    db = parser.parse_file("db/crypto_conf_list.bib")

    for filename in filenames:
        db = parser.parse_file(filename)

    conf_years = confs_years.get_confs_years_inter(db, confs_missing_years)

    with open("db/crypto_db.bib", "w") as out:
        out.write("% FILE GENERATED by add.py\n")
        out.write("% DO NOT MODIFY MANUALLY\n")
        out.write("\n")
        out.write("\n")
        for conf in sorted(conf_years.keys()):
            (start, end) = conf_years[conf]
            out.write("%    {}:{}{} - {}\n".format(conf, " "*(16-len(conf)-1), start, end))
        out.write("\n")
        out.write("\n")
    
        mybibtex.generator.bibtex_gen(out, db)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", metavar="file.bib", type=str, help="list of bib files to add to crypto_db.bib", nargs="*")
    args = parser.parse_args()

    shutil.copy("db/crypto_db.bib", "db/crypto_db.bib.{:0>12d}".format(int(time.time())))

    add(args.filenames)
    

if __name__=="__main__":
    main()
