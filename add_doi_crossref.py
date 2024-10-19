#!/usr/bin/env python3
"""
This script needs to be run in the root folder containing the
folders "lib" and "db"
"""

import argparse
import json
import logging
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))

import mybibtex.parser
import mybibtex.database
import mybibtex.generator
import confs_years

import config
from config import *

mybibtex.generator.config = config
logging.basicConfig(level=logging.DEBUG)

color_texts = {
    "Error": "\x1b[6;30;41mError\x1b[0m",
    "Warning": "\x1b[6;30;43mWarning\x1b[0m",
    "Success": "\x1b[6;30;42mSuccess\x1b[0m",
}


# From https://stackoverflow.com/a/32558749
def levenshtein_distance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = list(range(len(s1) + 1))
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


def format_name(person):
    def join(l):
        return ' '.join([name for name in l if name])

    first = person.get_part_as_text('first')
    middle = person.get_part_as_text('middle')
    prelast = person.get_part_as_text('prelast')
    last = person.get_part_as_text('last')
    lineage = person.get_part_as_text('lineage')
    s = ''
    if last:
        s += join([prelast, last])
    if lineage:
        s += ', %s' % lineage
    if first or middle:
        s += ', '
        s += join([first, middle])
    return s


def get_first_author(entry):
    if "author" in entry.persons:
        return format_name(entry.persons["author"][0])
    elif "author" in entry.fields:
        return entry.fields["author"].expand().split("and")[0].strip()
    else:
        return ""


def get_number_authors(entry):
    if "author" in entry.persons:
        return len(entry.persons["author"])
    elif "author" in entry.fields:
        return len(entry.fields["author"].expand().split("and"))
    else:
        return 0


def get_crossref_url(entry):
    query_conf = []
    if "booktitle" in entry.fields:
        query_conf = [("query.container-title", entry.fields["booktitle"].expand())]
    return "https://api.crossref.org/works?" + urllib.parse.urlencode([
        ("query.author", get_first_author(entry)),
        # ("query.bibliographic", entry.fields["year"].expand()), # removing it because does not work for all Springer books
        ("query.title", entry.fields["title"].expand())
    ] + query_conf)


def get_matching_doi(entry, j):
    for item in j["message"]["items"]:
        # check that number of author identical
        # and title close enough
        # similarly to https://github.com/IACR/program-editor/blob/c1de208435c063d3f878d55dd2a6b0e8a4b31c21/scripts/editor.js#L1336
        if len(item["author"]) == get_number_authors(entry) and \
                min(levenshtein_distance(title, entry.fields["title"].expand()) for title in item["title"]) <= 4:
            return item["DOI"]

    return None


def get_doi_entry(entry):
    url = get_crossref_url(entry)
    f = urllib.request.urlopen(url)
    j = json.load(f)
    return get_matching_doi(entry, j)


def add_doi(check_known_doi=False, filter_conf=None):
    parser = mybibtex.parser.Parser()
    parser.parse_file("db/abbrev3.bib")
    parser.parse_file("db/crypto_db_c85.bib")
    db = parser.parse_file("db/crypto_conf_list.bib")

    myfilter = mybibtex.generator.FilterPaper()
    if filter_conf:
        myfilter = mybibtex.generator.FilterConf(filter_conf, myfilter)
    entries = dict(myfilter.filter(db.entries))
    for (keybib, entry) in entries.items():
        key = str(keybib)

        if key.startswith("EPRINT"):
            continue

        if "doi" in entry.fields and not check_known_doi:
           continue # doi already there

        print(("Searching DOI for {}".format(key)))

        doi = get_doi_entry(entry)

        if doi == None:
            print(("    {}: cannot find DOI for {}".format(color_texts["Warning"], key)))
            print(("    tried: {}".format(get_crossref_url(entry))))
            continue

        if doi != None and "doi" in entry.fields and doi != entry.fields["doi"].expand():
            print(("    {}: expected {} but got {}".format(color_texts["Error"], entry.fields["doi"].expand(), doi)))
            continue

        print(("    {}: found DOI {}".format(color_texts["Success"], doi)))

        if "doi" in entry.fields:
            print("    (matched known DOI)")
        else:
            entry.fields["doi"] = mybibtex.database.Value([mybibtex.database.ValuePartQuote(doi)])

    conf_years = confs_years.get_confs_years_inter(db, confs_missing_years)

    with open("db/crypto_db.bib", "w") as out:
        out.write("% FILE GENERATED by add.py\n")
        out.write("% DO NOT MODIFY MANUALLY\n")
        out.write("\n")
        out.write("\n")
        for conf in sorted(conf_years.keys()):
            (start, end) = conf_years[conf]
            out.write("%    {}:{}{} - {}\n".format(conf, " " * (16 - len(conf) - 1), start, end))
        out.write("\n")
        out.write("\n")

        mybibtex.generator.bibtex_gen(out, db)


def main():
    parser = argparse.ArgumentParser("Automatically get the missing DOI from crossrefs. WARNING: does not seem to match paper very well...")
    parser.add_argument("-c", action="store_true", help="check known DOI too")
    parser.add_argument("--filter", help="filter a specific conference")
    args = parser.parse_args()

    shutil.copy("db/crypto_db.bib", "db/crypto_db.bib.{:0>12d}".format(int(time.time())))

    add_doi(args.c, args.filter)


if __name__ == "__main__":
    main()
