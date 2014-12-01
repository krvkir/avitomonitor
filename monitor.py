#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os
import time
import datetime

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
parser.add_argument(
    "-s",
    type=int,
    help="Save found items into db",
    default=1
    )
args = parser.parse_args()

######################################################################
# Main

# creating the parser
query = args.q.split(' ')
location = args.l
# queryurl = "http://www.avito.ru/%s?q=%s" % (location, '+'.join(query))
params = {
    # basic
    'baseurl': 'www.avito.ru',
    'location': location,
    'query': query,
    # auxilliary
    'maxpages': 5,
    }
sp = AvitoParser(params)

# loading records database
dbpath = "%s-%s.sqlite3" % ('_'.join(query), location)
sp.load(dbpath)

print("Already in db: %i" % len(sp.items))
sp.print_items(sp.items.values())

# watching
while True:
    # querying for new
    try:
        hashes = sp.refresh()
        print("Refreshed at %s"
              % datetime.datetime.today().strftime("%Y-%m-%d %H:%M"))
        if len(hashes) > 0:
            if args.s != 0:
                sp.save(dbpath)
            print("Updates found:")
            for i, h in enumerate(hashes):
                item = sp.items[h]
                sp.print_item(item)
                if i < 10:
                    os.system("notify-send '%s: %s'"
                              % (item['title'], item['price']))
    except Exception as e:
        print("LOOP ERROR: %s" % type(e))
        raise e
        # print("Message:\n%s" % e.message())

    # waiting
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nExiting.")
        exit()
