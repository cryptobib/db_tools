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

mybibtex.generator.config = config


def read_database(on_db=False):
    filename = "db/crypto_db.bib" if on_db else "db/test.bib"

    # Read the database
    parser = mybibtex.parser.Parser(encoding="utf8", person_fields=['author'])
    parser.parse_files(["db/abbrev0.bib", "db/crypto_conf_list.bib"])

    with open(filename, encoding="utf8") as f:
        preamble = ""

        cookie = f.tell()
        line = f.readline()
        while line == '\n' or line.startswith('%'):
            preamble += line
            cookie = f.tell()
            line = f.readline()
        f.seek(cookie)
        return preamble, parser.parse_file(f)


def write_database(preamble, db, confs_years, on_db=False):
    filename = ("db/crypto_db.bib" if on_db else "db/test.bib") + ".out"
    with open(filename, "w") as out:
        out.write(preamble)
        mybibtex.generator.bibtex_gen(out, db, expand_crossrefs=False,
                                      include_crossrefs=False,
                                      remove_empty_fields=True)


################################################################################


def namestrip(s):
    s = s.replace('{', '')
    s = s.replace('}', '')
    return re.sub('\\\\.', '', s).strip()


def fix_lineage(person):
    lastname = person.get_part_as_text('last')
    lineage = person.get_part_as_text('lineage')
    orig_name = lastname + ' ' + lineage if lineage else lastname

    moves = 0
    while re.search(' (Jr\\.|Sr\\.|II|III|IV)}?$', lastname):
        lastname = person._last[-1]
        moves += 1
        idx = lastname.rfind(' ')
        assert idx >= 0 and lastname[-1] == '}'

        person._lineage.append(lastname[idx + 1:-1])
        person._last[-1] = lastname[:idx] + '}'
        lastname = person.get_part_as_text('last')

    if re.match('^(II|III|IV)$', lastname):
        print("WARNING: Lineage is seen as lastname for ", person)

    if moves > 0:
        # Check if we can remove the {lastname}.
        if re.match('{[A-Za-z]*}', person.get_part_as_text('last')):
            assert len(person._last) == 1
            person._last[0] = person._last[0][1:-1]

        lastname = person.get_part_as_text('last')
        lineage = person.get_part_as_text('lineage')
        print("Changed \"", orig_name, "\" to \"", lastname + ', ' + lineage, "\"", sep="")


def run(db):
    for entrykey, entry in db.entries.items():
        if 'author' in entry.persons:
            for author in entry.persons['author']:
                fix_lineage(author)


def main():
    parser = argparse.ArgumentParser("Fix von prefices")
    parser.add_argument("--db", action="store_true",
                        help="Run on actual crypto_db.bib")
    args = parser.parse_args()

    # Make a backup
    # shutil.copy("db/crypto_db.bib",
    #             f"db/crypto_db.bib.{int(time.time()):0>12d}")
    # Run the command

    print("Reading bibtex source file...", file=sys.stderr, flush=True)
    preamble, db = read_database(args.db)
    print("Bibtex source file is read!", file=sys.stderr, flush=True)

    run(db)

    confs_years = get_confs_years_inter(db, config.confs_missing_years)
    write_database(preamble, db, confs_years, args.db)


if __name__ == "__main__":
    main()
