#!/usr/bin/env python2
"""
This script generates db/crypto.bib from
  db/abbrev0.bib
  db/crypto_db.bib
  db/crypto_conf_list.bib
  db/crypto_db_misc.bib

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
from confs_years import *

import logging

import header
import config
from config import *

mybibtex.generator.config = config
logging.basicConfig(level=logging.DEBUG)

def gen_crypto_bib(db, confs_years, expand_crossrefs):
    if expand_crossrefs == False:
        outname = "db/crypto_crossref.bib"
    else:
        outname = "db/crypto.bib"

    with open(outname, "w") as out:
        out.write(header.get_header(config, "gen.py", confs_years))
    
        mybibtex.generator.bibtex_gen(out, db, expand_crossrefs=expand_crossrefs, include_crossrefs=not expand_crossrefs)

        out.write("\n")
        out.write("\n")

        with open("db/crypto_misc.bib") as fin:
            for line in fin:
                out.write(line)

def main():
    parser = mybibtex.parser.Parser()
    parser.parse_file("db/abbrev0.bib")
    parser.parse_file("db/crypto_db.bib")
    db = parser.parse_file("db/crypto_conf_list.bib")

    confs_years = get_confs_years_inter(db, confs_missing_years)

    gen_crypto_bib(db, confs_years, True)
    gen_crypto_bib(db, confs_years, False)

if __name__ == "__main__":
    main()
