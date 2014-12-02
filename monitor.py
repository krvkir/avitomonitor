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
    "-l",
    type=str,
    help="Location",
    default='rossiya'
    )
parser.add_argument(
    "-q",
    type=str,
    help="""Search queries:
Each query is space-separated list of words,
one query divided from another by comma.
"""
    )
parser.add_argument(
    "-c",
    type=str,
    help="Categories, space-separated list",
    default=''
    )
parser.add_argument(
    "-pages",
    type=int,
    help="Maximum pages to crawl through (default is 5)",
    default=5
    )

parser.add_argument(
    "-pmin",
    type=int,
    help="Minimal price for the item",
    default=0
    )
parser.add_argument(
    "-pmax",
    type=int,
    help="Maximal price for the item",
    default=0
    )

parser.add_argument(
    "-s",
    type=int,
    help="Save found items into db (default is true)",
    default=1
    )
parser.add_argument(
    "-t",
    type=int,
    help="Time interval in seconds between refreshes (default is 60)",
    default=60
    )
args = parser.parse_args()

######################################################################
# Main

# preparing parameters
queries = [q.split() for q in args.q.split(',')]
location = args.l
categories = args.c.replace(',', ' ').split()
params = {
    # basic
    'baseurl': 'www.avito.ru',
    'location': location,
    'categories': categories,
    'queries': queries,
    'price': [args.pmin, args.pmax],
    # auxilliary
    'maxpages': args.pages,
    }
print("Starting monitor with the following parameters:")
for k, v in params.items():
    print("\t%s:\t\t%s" % (k, str(v)))
print("\n")

# creating the parser
sp = AvitoParser(params)

# loading records database
dbpath = "%s-%s.sqlite3" \
         % ('_'.join(['_'.join(q) for q in queries]), location)
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
                # notification
                if i < 5:
                    # checking if there was image
                    if len(item['photourls']) > 0:
                        photoname = item['photourls'][0].split('/')[-1]
                        photopath = "%s/photo/%s/%s" \
                                    % (os.getcwd(), h, photoname)
                    else:
                        photopath = ''
                    # messenging
                    cmd = "notify-send -u critical -i '%s' '(%s) %s: %s'"\
                          % (photopath, item['date'],
                             item['title'], item['price'])
                    os.system(cmd)
            if len(hashes)-5 > 0:
                os.system("notify-send -u critical '...and %i more.'"
                          % (len(hashes)-5))
    except Exception as e:
        print("LOOP ERROR: %s" % type(e))
        raise e
        # print("Message:\n%s" % e.message())

    # waiting
    try:
        time.sleep(args.t)
    except KeyboardInterrupt:
        print("\nExiting.")
        exit()
