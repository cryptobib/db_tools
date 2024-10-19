#!/usr/bin/env python3
"""
This script needs to be run in the root folder containing the
folders "lib" and "db"
"""

import argparse
import logging
import os
import re
import sys

from pybtex.bibtex.utils import split_name_list

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import mybibtex.parser
import mybibtex.generator
import config

mybibtex.generator.config = config
logging.basicConfig(level=logging.DEBUG)

color_texts = {
    "Error": "\x1b[6;30;41mError\x1b[0m",
    "Warning": "\x1b[6;30;43mWarning\x1b[0m",
    "Success": "\x1b[6;30;42mSuccess\x1b[0m",
}

# Capture the author part of a key, between the ":" and the year
re_author_part_key = re.compile(r"^[a-zA-Z0-9]+:([a-zA-Z]+)[0-9]{2}[a-z]?$")


def check_more_6_authors(args):
    """
    Analyze papers with more than 6 authors
    and check whether their keys have more than 6 initials or not

    because original rule of cryptobib is to have at most 6 initials in key
    """
    parser = mybibtex.parser.Parser()
    parser.parse_file("db/abbrev3.bib")
    parser.parse_file("db/crypto_db.bib")
    db = parser.parse_file("db/crypto_conf_list.bib")

    my_filter = mybibtex.generator.FilterPaper()
    filter_conf = args.filter
    if filter_conf:
        my_filter = mybibtex.generator.FilterConf(filter_conf, my_filter)
    entries = dict(my_filter.filter(db.entries))

    # dictionaries of the keys of the papers with >6 authors: split by number of authors in the key
    keys_more_6_initials = {}
    keys_equal_6_initials = {}
    keys_less_6_initials = {}

    # number of papers with more than 6 authors
    nb_papers = 0

    for keybib, entry in mybibtex.generator.SortConfYearPage().sort(iter(entries.items())):
        key = str(keybib)
        authors = split_name_list(entry.fields["author"].expand())
        if len(authors) <= 6:
            continue

        nb_papers += 1

        # Get the author part of the key (between the ":" and the year)
        author_part_key_match = re_author_part_key.match(key)
        if author_part_key_match is None:
            print(f"{color_texts['Error']}: key {key} cannot be parsed")
            return
        author_part_key = author_part_key_match.group(1)

        if len(author_part_key) < 6:
            keys_less_6_initials[key] = authors
        elif len(author_part_key) == 6:
            keys_equal_6_initials[key] = authors
        elif len(author_part_key) > 6:
            keys_more_6_initials[key] = authors

    if args.verbose:
        print("Papers with >6 authors and <6 initials in key:")
        for key, authors in keys_less_6_initials.items():
            print(f"    {key:20s}: {authors}")
        print()
        print("Papers with >6 authors and =6 initials in key:")
        for key, authors in keys_equal_6_initials.items():
            print(f"    {key:20s}: {authors}")
        print()
        print("Papers with >6 authors and >6 initials in key:")
        for key, authors in keys_more_6_initials.items():
            print(f"    {key:20s}: {authors}")
        print()

    print(f"{len(keys_less_6_initials):4d} / {nb_papers:4d} papers with >6 authors have <6 initials in key")
    print(f"{len(keys_equal_6_initials):4d} / {nb_papers:4d} papers with >6 authors have =6 initials in key")
    print(f"{len(keys_more_6_initials):4d} / {nb_papers:4d} papers with >6 authors have >6 initials in key")


def main():
    parser = argparse.ArgumentParser("Analyze papers with >6 authors: count how many use key with >6 initials")
    parser.add_argument("--filter", help="filter a specific conference")
    parser.add_argument("--verbose", action="store_true", help="display all the papers with >6 authors")
    args = parser.parse_args()

    check_more_6_authors(args)


if __name__ == "__main__":
    main()
