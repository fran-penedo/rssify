from __future__ import print_function

import traceback
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
import re

def process_section(s, directory):
    r = requests.get(s["url"])
    soup = BeautifulSoup(r.text, "lxml")
    titles = soup.select(s["item_title"])
    urls = soup.select(s["item_url"])

    if "item_date" in s:
        dates = soup.select(s["item_date"])
    else:
        dates = None

    if "item_content" in s:
        contents = soup.select(s["item_content"])
    else:
        contents = None

    fg = FeedGenerator()
    fg.title(section)
    fg.description(section)
    fg.link(href=s["url"], rel="alternate")

    for i in range(len(titles)):
        if i > len(urls) - 1:
            break

        fe = fg.add_entry()

        if "item_title_function" in s:
            title = titles[i]
            title_text = eval(s["item_title_function"])
        else:
            title_text = titles[i].text
        fe.title(title_text)

        if "item_url_function" in s:
            url = urls[i]
            href = eval(s["item_url_function"])
        else:
            href = urls[i].get("href")
        link = urlparse.urljoin(s["url"], href)
        fe.link(href=link, rel="alternate")

        if contents is not None:
            if "item_content_function" in s:
                content = contents[i]
                content_text = eval(s["item_content_function"])
            else:
                content_text = contents[i].text
            fe.content(content_text)

        now = datetime.now(timezone("Europe/Berlin"))
        if dates is not None:
            datestr = dates[i].text.strip()
            formats = s["item_date_format"].split("|")
            date = None
            for form in formats:
                try:
                    date = datetime.strptime(datestr, form)
                except ValueError:
                    pass
            if date is None:
                raise ValueError("Date string '{}' has no valid formats: {}".format(datestr, formats))
            # Set default year to current year
            if date.year == 1900:
                date = date.replace(year=now.year)
            date = date.replace(tzinfo=get_localzone())
            if config.has_option(section, "item_timezone"):
                localtz = timezone(s["item_timezone"])
                date = localtz.localize(date)
        else:
            date = now
            # date = '1970-01-01 00:00:00+02:00'

        fe.published(date)

    fg.rss_file(os.path.join(directory, section.replace(" ", "_") + ".xml"))


if len(sys.argv) > 1:
    config_fn = sys.argv[1]
else:
    config_fn = "config.ini"

config = configparser.ConfigParser()
config.read(config_fn)

try:
    directory = config.get("options", "directory")
except:
    directory = "."

config.remove_section("options")

for section in config.sections():
    s = dict(config.items(section))
    try:
        process_section(s, directory)
    except Exception as e:
        print("In {}:".format(section), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

