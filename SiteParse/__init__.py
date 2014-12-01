# -*- coding: utf-8 -*-

import time
import datetime

import hashlib

import httplib2
from lxml import html

import sqlite3
import pickle

import sys
import traceback
from pprint import pprint


######################################################################
######################################################################
# Parser classes

class Parser:
    """ Abstract class for site parsers
    """

    params = {}
    items_xpath = ''
    items = {}

    def __init__(self, params):
        self.params = params

    def make_url(self, params, extparams):
        """ Makes url for the request. Site-specific function """
        raise NotImplementedError()

    ############################################################

    def print_item(self, i):
        """ Print line with item info """
        raise NotImplementedError()

    def print_items(self, items):
        """ Print group of items """
        for i in items:
            self.print_item(i)

    ############################################################

    def parse_item(self, i):
        """ Parse items html blocks to property dicts """
        raise NotImplementedError()

    def hash_item(self, i):
        """ Calculate hash uniquely identifying item """
        raise NotImplementedError()

    def get_items(self, url):
        """ Get items html blocks, parse them and return.
        There is NO checking for new items, only fetching and parsing
        """
        req = httplib2.Http()
        try:
            headers, body = req.request(url, method='GET')
        except httplib2.ServerNotFoundError:
            return {}

        if headers['status'] != '200':
            return {}
            # raise Exception("Server returned error")

        parsed_body = html.fromstring(body)
        raw_items = parsed_body.xpath(self.items_xpath)

        items = []
        for i in raw_items:
            try:
                items.append(self.parse_item(i))
            except Exception:
                # exception info
                # etype, e, tb = sys.exc_info()
                traceback.print_exc()
                # print("PARSE ERROR: %s: %s" % (e.errno, e.strerror))
                # traceback.print_tb(tb)
                # item info (and link to the item on the site)
                pprint(i.values())
                for lnk in i.iterlinks():
                    print(lnk)
                # skip this item and proceed
                pass

        return {self.hash_item(i): i for i in items}

    def refresh(self):
        """ Get items, add ones that do not already present in storage
        Check for new items is THERE
        """
        # initialize new items hashes list
        newhashes = []

        # for every query...
        for query in self.params['queries']:
            # ...searching for every category listed...
            for cat in self.params['categories']:
                # ... and crawling through pages before stop getting new items
                for p in range(1, self.params['maxpages']+1):
                    # prepare url
                    url = self.make_url(
                        self.params,
                        {'query': query, 'category': cat, 'page': p})
                    # get items from the site
                    items = self.get_items(url)

                    # checking which items are new
                    newnbr = 0
                    for h, i in items.items():
                        if h not in self.items:
                            self.items[h] = i
                            newhashes.append(h)
                            newnbr += 1

                    # if no new items found on this page
                    # then we reached the extent where we already searched,
                    # no need to go farther through pages
                    if newnbr == 0:
                        break

                    time.sleep(3)

        # return new items hashes list
        return newhashes

    ############################################################

    def init_db(self, path):
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS Items (hash, url, data)")
        cur.close()
        return conn

    def save(self, path, hashes=None):
        """ Save data to database
        Returns number of added new records
        """
        conn = self.init_db(path)
        cur = conn.cursor()

        if hashes is None:
            items = self.items
        else:
            items = {k: self.items[k] for k in hashes}

        newhashes = []
        for k, i in items.items():
            cur.execute("SELECT * FROM Items WHERE hash=?", [k])
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO Items (hash, url, data) VALUES (?, ?, ?)",
                    [k, i['url'], pickle.dumps(i)]
                    )
                newhashes.append(k)

        if len(newhashes) > 0:
            conn.commit()
        cur.close()
        conn.close()
        return newhashes

    def load(self, path):
        """ Load record from db file.
        Resets items dict!
        """
        conn = self.init_db(path)
        cur = conn.cursor()
        cur.execute("SELECT hash, data FROM Items")
        self.items = {k: pickle.loads(i) for k, i in cur}
        cur.close()
        conn.close()


######################################################################
######################################################################

class AvitoParser(Parser):
    """ Class for parsing avito.ru.
    Version 2014-12-01
    """
    items_xpath = ".//*[starts-with(@class, 'item')]"

    def make_url(self, params, extparams):
        return "http://%s/%s/%s?q=%s&p=%i" % \
            (
                params['baseurl'],
                params['location'],

                extparams['category'],
                '+'.join(extparams['query']),
                extparams['page']
            )

    ############################################################

    def print_item(self, i):
        print("%s\n\t%s\t%s\t%s\n\thttp://%s\n"
              % (i['title'],
                 i['price'], i['date'], i['location'],
                 self.params['baseurl']+i['url']))

    ############################################################

    def parse_item(self, i):
        """ Parse items html blocks to property dicts
        """
        d = i.xpath("*[@class='description']")[0]

        price = normalize_str(d.xpath("*[@class='about']/text()")[0])
        title = normalize_str(d.xpath("*[@class='title']/a/text()")[0])
        url = d.xpath("*[@class='title']/a/@href")[0]

        category_and_company = d.xpath("*[@class='data']/p[1]/text()")
        category = normalize_str(category_and_company[0])
        company = normalize_str(category_and_company[1]) \
            if len(category_and_company) > 1 else ''

        # location
        try:
            location = normalize_str(
                d.xpath("*[@class='data']/p[2]/text()")[0])
        except:
            # for items without location
            location = ''

        date = normalize_str(normalize_date(d.xpath(
            "*[@class='data']/*[@class='date']/text()"
        )[0]))

        # icon URL
        try:
            photourl = i.xpath("*[@class='b-photo']/a/img/@src")[0]
        except:
            # for items without photo
            photourl = ''

        return {'price': price,
                'title': title,
                'url': url,

                'category': category,
                'company': company,

                'location': location,
                'date': date,

                'photourl': photourl,
                }

    fields_order = ['price', 'title', 'url', 'category', 'company',
                    'location', 'date', 'photourl']

    def hash_item(self, i):
        """ Calculate hash uniquely identifying item """
        h = hashlib.md5()
        for f in self.fields_order:
            h.update(i[f].encode('UTF-8'))
        return h.hexdigest()


######################################################################
######################################################################
# Some helpers

def normalize_date(d):
    """ Convert date from textual form to timestamp
    """
    today = datetime.date.today()
    oneday = datetime.timedelta(1)
    yesterday = today - oneday

    subst = {
        u'Вчера': yesterday.strftime("%d %m"),
        u'Сегодня': today.strftime("%d %m"),
        u'окт.': '10',
        u'нояб.': '11',
    }

    for k, v in subst.items():
        d = d.replace(k, v)

    return d


def normalize_str(s):
    """ Remove all redundant spaces or newlines or tabs
    """
    return ' '.join(s.split()).lower()
