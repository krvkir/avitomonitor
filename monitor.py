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
parser.add_argument(
    "-l",
    type=str,
    help="Location",
    default='rossiya'
    )
args = parser.parse_args()

######################################################################
# Main

query = args.q.split(' ')
location = args.l
queryurl = "http://www.avito.ru/%s?q=%s" % (location, '+'.join(query))
dbpath = "%s-%s.sqlite3" % ('_'.join(query), location)

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
        print("LOOP ERROR: %s" % type(e))
        # print("Message:\n%s" % e.message())

    # waiting
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nExiting.")
        exit()
