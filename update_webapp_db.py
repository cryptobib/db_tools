#!/usr/bin/env python3
"""
This script updates the database of the web server using
  db/abbrev0.bib
  db/abbrev1.bib
  db/abbrev2.bib
  db/abbrev3.bib
  db/crypto_db.bib
  db/crypto_conf_list.bib
  db/crypto_db_misc.bib
  db/changes.txt

WARNING: THIS SCRIPT NEEDS TO BE EXECUTED in the ROOT folder of the cryptobib project
   AND web2py needs to installed as explained in webapp/README.md

In addition, it may be necessary to clear the cache of the web server or to restart it, after updating storage.sqlite.
Please read README.md for details.
"""

import sys
import os
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(".")
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", "db"))
sys.path.append(os.path.join(scriptdir, "..", "web2py"))

from mybibtex import tools
import mybibtex.parser
import mybibtex.generator
from confs_years import *
import config
from config import *

mybibtex.generator.config = config

import logging
import re
import datetime

logging.basicConfig(level=logging.DEBUG)

os.chdir("web2py")
import gluon.shell
from gluon.storage import Storage

_re_date = re.compile(r"^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$")


def update_changes(db):
    """
    Store changes in the table "changes" of storage.sql

    changes.txt has to be of the form:

    * yyyy-mm-dd
    description of change at ...

    * yyyy-mm-dd
    ...
    """

    changes = []

    fin = open("../db/changes.txt")
    lineno = 1
    for line in fin:
        if lineno == 1 and line[0] != "*":
            logging.error("Error: the first line has to start by '*'")
            sys.exit(1)
        if line[0] == "*":
            r = _re_date.match(line[1:])
            if r == None:
                logging.error("Error: invalid date on line {}. Date format is yyyy-mm-dd".format(lineno))
                sys.exit(1)
            (yy,mm,dd) = r.groups()
            changes.append((datetime.date(int(yy),int(mm),int(dd)),""))
        else:
            (date_c, desc_c) = changes[-1]
            desc_c = desc_c + line
            changes[-1] = (date_c, desc_c)

        lineno += 1
    fin.close()

    changes_bulk = [
        {"date": date_c.strftime("%Y-%m-%d"), "desc": desc_c} 
        for (date_c, desc_c) in changes
    ]

    db.change.truncate()
    db.change.bulk_insert(changes_bulk)
    db.commit()


def update_confs(db, confs_years):
    confs = [
        {
            "type":       conf["type"],
            "key":        confkey,
            "name":       conf["name"],
            "full_name":  conf["full_name"],
            "start_year": confs_years[confkey][0],
            "end_year":   confs_years[confkey][1]
        }
        for (confkey, conf) in sorted(
                iter(config.confs.items()),
                key = lambda k_x: ("a-" if k_x[1]["type"] == "conf" else "b-") + k_x[1]["name"]
        )
    ]
    db.conf.truncate()
    db.conf.bulk_insert(confs)
    db.commit()


def update_entries(db, cryptodb):
    db.entry.truncate()

    def aux(cryptodb, entries):
        for key, entry in entries:
            fields_orig = mybibtex.generator.bibtex_entry_format_fields(db, key, entry, expand_crossrefs=False)
            fields = {k: v.to_bib(expand=False) for (k,v) in fields_orig.items()}

            fields["type"] = entry.type.lower()
            
            fields["key_conf"] = key.confkey
            fields["key_year"] = tools.short_to_full_year(key.year)
            fields["key_auth"] = key.auth
            fields["key_dis"]  = key.dis

            start_page = None
            end_page = None
            if "pages" in fields:
                pages = fields["pages"]
                if pages.isdigit():
                    start_page = pages
                else:
                    a = pages[1:-1].split("--")
                    if len(a) == 1 or len(a) == 2:
                        start_page = a[0]
                    if len(a) == 2:
                        end_page = a[1]

            fields["start_page"] = start_page
            fields["end_page"]   = end_page

            if "years" in fields:
                fields["years"] = int(fields["years"])

            if "pages" in fields:
                del fields["pages"]

            if "crossref" in fields:
                fields["crossref_expanded"] = fields_orig["crossref"].to_bib(expand=True)[1:-1] # expand and remove quotes

            db.entry.insert(**fields)
        db.commit()
    
    entries = dict(mybibtex.generator.FilterPaper().filter(cryptodb.entries))
    aux(cryptodb, mybibtex.generator.SortConfYearPage().sort(iter(entries.items())))

    crossrefs = dict()
    for k, e in entries.items():
        if "crossref" in e.fields:
            crossref = mybibtex.generator.EntryKey.from_string(e.fields["crossref"].expand())
            if crossref not in crossrefs:
                crossrefs[crossref] = cryptodb.entries[crossref]
    aux(cryptodb, mybibtex.generator.SortConfYearPage().sort(iter(crossrefs.items())))


def main():
    app = Storage(gluon.shell.env("cryptobib", import_models = True))

    print("* read crypto_db.bib")
    parser = mybibtex.parser.Parser()
    parser.parse_file("../db/abbrev0.bib")
    parser.parse_file("../db/crypto_db.bib")
    cryptodb = parser.parse_file("../db/crypto_conf_list.bib")
    confs_years = get_confs_years_inter(cryptodb, confs_missing_years)

    print("* update changes table")
    update_changes(app.db)
    print("* update confs table")
    update_confs(app.db, confs_years)
    print("* update entries table")
    update_entries(app.db, cryptodb)


if __name__ == "__main__":
    main()
