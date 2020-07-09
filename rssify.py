import configparser
from datetime import datetime
import requests
from feedgen.feed import FeedGenerator
from bs4 import BeautifulSoup
from pytz import timezone
from tzlocal import get_localzone
import os
import urlparse
import sys

if len(sys.argv) > 1:
    config_fn = sys.argv[1]
else:
    config_fn = 'config.ini'

config = configparser.ConfigParser()
config.read(config_fn)

try:
    directory = config.get('options', 'directory')
except:
    directory = "."

config.remove_section('options')

for section in config.sections():
    s = dict(config.items(section))
    r = requests.get(s['url'])
    soup = BeautifulSoup(r.text, 'lxml')
    titles = soup.select(s['item_title'])
    urls = soup.select(s['item_url'])

    if 'item_date' in s:
        dates = soup.select(s['item_date'])
    else:
        dates = None

    fg = FeedGenerator()
    fg.title(section)
    fg.description(section)
    fg.link(href=s['url'], rel='alternate')

    for i in range(len(titles)):
        if i > len(urls) - 1:
            break

        fe = fg.add_entry()
        fe.title(titles[i].text)
        if 'item_url_function' in s:
	     url = urls[i]
   	     href = eval(s['item_url_function'])
	else:
	     href = urls[i].get('href')
        link = urlparse.urljoin(s['url'], href)
        fe.link(href=link, rel='alternate')
        if dates is not None:
            date = datetime.strptime(dates[i].text.strip(), s['item_date_format'])
            date = date.replace(tzinfo=get_localzone())
            if config.has_option(section, 'item_timezone'):
                localtz = timezone(s['item_timezone'])        
                date = localtz.localize(date)
        else:
            #date = datetime.now(timezone("Europe/Berlin")) 
            date = '1970-01-01 00:00:00+02:00'

        fe.published(date)

    fg.rss_file(os.path.join(directory, section.replace(' ', '_') + '.xml'))
