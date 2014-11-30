avitomonitor
============

Simple Avito.ru monitor

Works:
- AvitoParser class fetchs search results page, parses it and gets properties for items: title, price, city, date, company, url and photo url
- Parser class can save results into db and load them from it
- monitor.py:
  - one can specify search query
  - new results are printed, sent to the message bus (needs notify-send installed) and saved
  - refreshes results every 60 seconds

Doesn't work
- one can't specify city
- results are fetched from 1st page only (no crawling through pages yet)
- for some reason when program stops and then starts again, then fetches from the site some items already existing in db, they are not recognized as existing and are added again.