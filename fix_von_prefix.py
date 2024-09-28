#!/usr/bin/env python3
"""
This script needs to be run in the root folder containing the
folders "lib" and "db"
"""

import argparse
import os
import re
import sys
# import shutil
# import time

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import mybibtex.parser
import mybibtex.database
import mybibtex.generator
from confs_years import get_confs_years_inter


import header
import config
from config import confs_missing_years

mybibtex.generator.config = config


def read_database(on_db=False):
    filename = "db/crypto_db.bib" if on_db else "db/crypto_db_test.bib"

    # Read the database
    parser = mybibtex.parser.Parser(encoding="utf8", person_fields=['author'])
    return parser.parse_files([
        "db/abbrev0.bib",
        "db/crypto_conf_list.bib",
        filename,
    ])


def write_database(db, confs_years):
    for expand_crossrefs in [False, True]:
        outname = "db/crypto.bib" if expand_crossrefs else "db/crypto_crossref.bib"
        with open(outname, "w") as out, open("db/crypto_misc.bib") as fin:
            out.write(header.get_header(config, "gen.py", confs_years))
            mybibtex.generator.bibtex_gen(out, db, expand_crossrefs=expand_crossrefs,
                                          include_crossrefs=not expand_crossrefs,
                                          remove_empty_fields=True)
            out.write("\n\n")
            for line in fin:
                out.write(line)


def namestrip(s):
    s = s.replace('{', '')
    s = s.replace('}', '')
    return re.sub('\\\\.', '', s).strip()


def fix_von_prefix(on_db=False):
    db = read_database(on_db)
    print("crypto_db is read.", file=sys.stderr)

    people = set()
    for entrykey, entry in db.entries.items():
        # key = str(entrykey)
        if 'author' in entry.persons:
            for author in entry.persons['author']:
                people.add(author)

    people = sorted(list(people), key=lambda x: str(x))
    stripped_people = dict()

    for p in people:
        parts = (
            p.get_part('first')
            + p.get_part('prelast')
            + p.get_part('last')
            + p.get_part('lineage')
        )
        stripped_p = ' '.join(map(namestrip, parts))

        if stripped_p not in stripped_people:
            stripped_people[stripped_p] = []
        stripped_people[stripped_p].append(p)
        # lastname = p.get_part_as_text('last')
        # if re.match('^{[a-z]', lastname):
        #     print(p)

    for strip, ps in stripped_people.items():
        if len(ps) > 1:
            print(strip, "has multiple hits:")
            for p in ps:
                print("    ", p)

    return db


def main():
    parser = argparse.ArgumentParser("Fix von prefices")
    parser.add_argument("--db", action="store_true",
                        help="Run on actual crypto_db.bib")
    parser.add_argument("--out", action="store_true",
                        help="Write to db/crypto[_crossref].bib")
    args = parser.parse_args()

    # Make a backup
    # shutil.copy("db/crypto_db.bib",
    #             f"db/crypto_db.bib.{int(time.time()):0>12d}")
    # Run the command
    db = fix_von_prefix(on_db=args.db)
    if args.out:
        confs_years = get_confs_years_inter(db, confs_missing_years)
        write_database(db, confs_years)



if __name__ == "__main__":
    main()
