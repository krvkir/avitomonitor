avitomonitor
============

Simple Avito.ru monitor

Works:
- AvitoParser class fetchs search results page, parses it and gets properties for items: title, price, city, date, company, url and photo url
- Parser class can save results into db and load them from it
- Parser crawls through pages
  - pages number limited by maxpages constant (by default = 5)
  - smart refresh: if no new items found on current page, next pages are not requested (assuming results ordered by addition time)
- monitor.py:
  - one can specify search query
  - new results are printed, sent to the message bus (needs notify-send installed) and saved
  - refreshes results every 60 seconds

Doesn't work
- one can't specify city
- does not distinguish ad items