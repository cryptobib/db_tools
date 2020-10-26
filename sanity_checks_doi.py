#!/usr/bin/env python2
"""
This script needs to be run in the root folder containing the
folders "lib" and "db"
"""



import collections
import sys
import os

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import mybibtex.parser
import mybibtex.database
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

color_texts = {
    "Error": "\x1b[6;30;41mError\x1b[0m",
    "Warning": "\x1b[6;30;43mWarning\x1b[0m",
    "Success": "\x1b[6;30;42mSuccess\x1b[0m",
}


# http://stackoverflow.com/q/3844948/
def check_all_elements_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)


def filter_doi(entries):
    """ Return entries with DOI only """
    return [entry for entry in entries if "doi" in entry.fields]


def check_doi_lncs_book(book, entries, verbose=False):
    """ Check the DOI of a Springer book are consistent
     @param entries list of entries of `book` with a DOI """

    if len(entries) == 0:
        return

    doi_prefix = [
        "_".join(entry.fields["doi"].expand().split("_")[:-1])
        for entry in entries
        if entry.fields["doi"].expand() != "10.1007/10931455_18" # there is an exception for this DOI CHES:CheJoyPai03
    ]

    ok = check_all_elements_equal(doi_prefix)
    if (not ok) or verbose:
        print("{:<40}".format("Checking Springer book {}... ".format(book)), end="")
    if ok:
        if verbose:
            print("{} (prefix: {} for {} entries with DOI)".format(color_texts["Success"], doi_prefix[0], len(entries)))
    else:
        print("{} (list of prefixes: {} for {} entries with DOI)".format(color_texts["Error"], " ".join(list(set(doi_prefix))), len(entries)))


def is_lncs(db, entry):
    fields = db.entries[mybibtex.database.EntryKey.from_string(entry.fields["crossref"].expand())].fields
    return "series" in fields and fields["series"].expand() == "{LNCS}"


def check_doi(args):
    parser = mybibtex.parser.Parser()
    parser.parse_file("db/abbrev3.bib")
    parser.parse_file("db/crypto_db.bib")
    db = parser.parse_file("db/crypto_conf_list.bib")

    myfilter = mybibtex.generator.FilterPaper()
    filter_conf = args.filter
    if filter_conf:
        myfilter = mybibtex.generator.FilterConf(filter_conf, myfilter)
    entries = dict(myfilter.filter(db.entries))

    entries_per_book = collections.OrderedDict()

    for (keybib, entry) in mybibtex.generator.SortConfYearPage().sort(iter(entries.items())):
        key = str(keybib)

        if key.startswith("EPRINT"):
            continue

        if "crossref" not in entry.fields:
            continue

        book = entry.fields["crossref"].expand()
        if book not in entries_per_book:
            entries_per_book[book] = [entry]
        else:
            entries_per_book[book].append(entry)

    nb = 0
    nb_checked = 0
    for (book, entries) in entries_per_book.items():
        nb += 1
        if is_lncs(db, entries[0]):
            check_doi_lncs_book(book, filter_doi(entries), args.verbose)
            nb_checked += 1

        dois = ["doi" in entry.fields for entry in entries]
        if dois.count(True) != len(dois):
            print("{}: book {:<10} has only {:2d} entries with DOI out of {}".format(color_texts["Warning"], book, dois.count(True), len(dois)))
        elif args.verbose:
            print("{}: book {:<10} has all {:2d} entries with DOI".format(color_texts["Success"], book, len(dois)))

    print("")
    print("{} out of {} books checked".format(nb_checked, nb))


def main():
    parser = argparse.ArgumentParser("Does some sanity checks for DOI (e.g., that first part of Springer DOI is the same for each book")
    parser.add_argument("--filter", help="filter a specific conference")
    parser.add_argument("--verbose", action="store_true", help="display also successful checks")
    args = parser.parse_args()

    shutil.copy("db/crypto_db.bib", "db/crypto_db.bib.{:0>12d}".format(int(time.time())))

    check_doi(args)


if __name__ == "__main__":
    main()
