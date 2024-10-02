#!/usr/bin/env python3
"""
This script needs to be run in the root folder containing the
folders "lib" and "db".

Note: either can be called from a different script, or from command line!
TODO: let db_import/import.py use this one!
"""
from copy import copy
from unidecode import unidecode

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


def strip_accents(s):
    """
    Return a string similar to `s` but with all accents removed.
    These can be unicode characters or LaTeX escaped.
    """
    original_s = s

    # Remove any UTF-8 characters, although most of them are escaped with LaTeX.
    s = unidecode(s)

    # Expand \ss to 'ss', because it's a ringel-s, like in:
    # [PoPETS:Gross21]: author="Thomas Gro{\ss}"
    s = s.replace('\\ss', 'ss')

    # Remove \textcommabelow, like in
    # [EPRINT:RosButSim23](https://eprint.iacr.org/2023/124)
    s = s.replace('\\textcommabelow', '')

    # Replace Danish \O, \o by respectively O, o:
    s = re.sub('\\\\o', 'o', re.sub('\\\\O', 'O', s))

    # Also remove all LaTeX escape characters, and gobble up the character after it.
    s = re.sub('\\\\.', '', s)

    if s.find('.') >= 0:
        print(f"WARNING: Spurious '.' found in \"{original_s}\".")

    # Remove '{', '}', '(', ')', "'", '-', '~', ' ', etc.:
    # 1) "-" can occur in [EPRINT:Hall-Andersen19]: Mathias Hall-Andersen
    # 2) "'" can occur in [CANS:BelONe13]: Adam O'Neill
    #    but watch out for [C:ChaCreDam87]:
    #    here "Cr{\'e}peau" should be replaced by "Crepeau"!
    # 3) "~" can occur in [SAC:OhESco06] with name "Colm {{\'O}~h{\'E}igeartaigh}".
    # 4) "(" can occur in [WISA:YanKimOhL16] with name "Il Seok {Oh(Luke)}".
    return re.sub('[^a-zA-Z]', '', s)
    # https://www.w3schools.com/python/ref_string_translate.asp
    # return s.translate(str.maketrans('', '', "{}()'-~. "))


_warned_authors = set()


def author_abbreviation(author):
    """
    Return the name of the author that can be used as an entry key for a bibtex entry.
    If there are some von prefices, these are abbreviated to one letter.

    Note: this is only for one single author.
    Use authors_abbreviation instead if you have a list of all authors.
    """
    von = author.prelast()
    lastname = strip_accents(author.get_part_as_text('last'))

    if not 'A' <= lastname[0] <= 'Z':
        if author not in _warned_authors:
            print("WARNING: odd lastname: \"", lastname, "\"; ", str(author), sep="")
            _warned_authors.add(author)

    return "".join(strip_accents(x)[0] for x in von) + lastname


def authors_abbreviation(authors):
    """return the author bibtext key part"""
    if len(authors) <= 0:
        print("ERROR: Entry with no author => replaced by ???")
        return "???"

    if len(authors) == 1:
        # The key contains the last name.
        return author_abbreviation(authors[0])

    if len(authors) <= 3:
        # The key contains the first three letters of each last name.
        return "".join(author_abbreviation(a)[:3] for a in authors)

    # The key contains the first letter of the last name of the first six authors.
    # (any von prefices are removed)
    return "".join(strip_accents(a.last()[0])[0] for a in authors[:6])


def run(db):
    # Warning: if we modify the entry name,
    # it might conflict with one that we already saw overriding that entry.
    # In any case, it is not a smart idea to modify a dict while iterating over it,
    # so just compute the new result in new_db.
    new_db = mybibtex.database.BibliographyData()

    for entrykey, entry in db.entries.items():
        if 'author' not in entry.persons:
            new_db.add_entry(entrykey, entry)
            continue

        authors = entry.persons['author']

        new_key = copy(entrykey)
        new_key.auth = authors_abbreviation(authors)
        key_a = copy(new_key)
        new_key.dis, key_a.dis = '', 'a'

        if new_key in new_db.entries:
            # We require disambiguation: turn KEY into KEYa and KEYb.
            new_db.entries[key_a] = new_db.entries.pop(new_key)
            new_key.dis = 'b'
        elif key_a in new_db.entries:
            # Find the next disambiguation string ("", "a", "b", ...) that is unused.
            # May be needed if same authors and same year occur for different papers.
            new_key.dis = 'b'
            while new_key in new_db.entries:
                # Having more than 26 of the same names is weird... That will NEVER happen!
                assert new_key.dis[0] < 'z'
                new_key.dis = chr(ord(new_key.dis[0]) + 1)
        new_db.add_entry(new_key, entry)
    return new_db


def main():
    parser = argparse.ArgumentParser("Fix von prefices")
    parser.add_argument("--db", action="store_true",
                        help="Run on actual crypto_db.bib")
    args = parser.parse_args()

    # Make a backup
    # shutil.copy("db/crypto_db.bib",
    #             f"db/crypto_db.bib.{int(time.time()):0>12d}")
    # Run the command

    print("LOG: Reading bibtex source file...", file=sys.stderr, flush=True)
    preamble, db = read_database(args.db)
    print("LOG: Bibtex source file is read!\n", file=sys.stderr, flush=True)

    new_db = run(db)
    del db
    print("LOG: Output bibtex to output file...")
    confs_years = get_confs_years_inter(new_db, config.confs_missing_years)
    write_database(preamble, new_db, confs_years, args.db)


if __name__ == "__main__":
    main()
