#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
import time

from pprint import pprint

from SiteParse import AvitoParser


######################################################################
# Parameters
parser = argparse.ArgumentParser()
parser.add_argument(
    "-q",
    type=str,
    help="Search query"
    )
args = parser.parse_args()

######################################################################
# Main

query = args.q.split(' ')
queryurl = "http://www.avito.ru/rossiya?q=%s" % '+'.join(query)
dbpath = '_'.join(query) + '.sqlite3'

# loading records database
sp = AvitoParser(queryurl)
sp.load(dbpath)

print("Already in db: %i" % len(sp.items))
sp.print_items(sp.items.values())

# watching
while True:
    # querying for new
    try:
        hashes = sp.refresh()
        if len(hashes) > 0:
            sp.save(dbpath)
            print("Updates found:")
            for h in hashes:
                i = sp.items[h]
                sp.print_item(i)
                os.system("notify-send '%s: %s'"
                          % (i['title'], i['price']))
    except Exception as e:
        print("ERROR: %s" % type(e))
        print("Message:\n%s" % e.message())

    # waiting
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nExiting.")
        exit()
