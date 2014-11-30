# -*- coding: utf-8 -*-

import time
import datetime

import hashlib

import httplib2
from lxml import html

import sqlite3
import pickle

from pprint import pprint


######################################################################
######################################################################
# Parser classes

class Parser:
    """ Abstract class for site parsers
    """

    items_xpath = ''
    items = {}

    def __init__(self, url):
        self.url = url

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

    def get_items(self):
        """ Get items html blocks from avito.ru
        """
        req = httplib2.Http()
        try:
            headers, body = req.request(self.url, method='GET')
        except httplib2.ServerNotFoundError:
            return []

        if headers['status'] != '200':
            raise Exception("Server returned error")

        parsed_body = html.fromstring(body)
        raw_items = parsed_body.xpath(self.items_xpath)
        items = [self.parse_item(i) for i in raw_items]
        items = {hash_dict(i): i for i in items}

        return items

    def refresh(self):
        """ Get items and add ones that do not exist
        """
        # get items from the site
        items = self.get_items()
        # initialize new items hashes list
        newhashes = []

        # checking which items are new
        for h, i in items.items():
            if h not in self.items:
                print("ACHTUNG!!! new item!!!")
                self.items[h] = i
                newhashes.append(h)

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
                print("ACHTUNG!!! item not from DB!!!")
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
        # self.items = {}
        # for k, i in cur:
        #     pprint(k)
        #     self.items[k] = i
        self.items = {k: pickle.loads(i) for k, i in cur}
        cur.close()
        conn.close()


######################################################################
######################################################################

class AvitoParser(Parser):
    """ Class for parsing avito.ru
    """

    items_xpath = ".//*[starts-with(@class, 'item')]"

    ############################################################

    def print_item(self, i):
        print("%s\t%s\t%s\t%s"
              % (i['date'], i['city'], i['price'], i['title']))

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

        city = normalize_str(d.xpath("*[@class='data']/p[2]/text()")[0])
        date = normalize_str(normalize_date(d.xpath(
            "*[@class='data']/*[@class='date']/text()"
        )[0]))

        photourl = i.xpath("*[@class='b-photo']/a/img/@src")[0]

        return {'price': price,
                'title': title,
                'url': url,

                'category': category,
                'company': company,

                'city': city,
                'date': date,

                'photourl': photourl,
                }


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


def hash_dict(p):
    """ Calculate hash of dict properties
    """
    m = hashlib.md5()
    m.update(''.join(p.values()).encode('UTF-8'))
    return m.hexdigest()
