Forked from https://github.com/h43z/rssify.

I looked at a few online services that provide custom created RSS feeds
for websites that don't have one. None of them were free of charge 
without being too much limited in functionality for me.

So I hacked together this very simple rssify.py script.
It reads from a config file your websites you want to rssify.
It could be easily extened for more features if needed.
For now it only parses the title and date via css selectors and generates
a feed.xml file which can be imported into newsboat/newsbeuter or I guess any
other rss reader.

It can also evaluate set an url for each link, either obtaining the 'href' attribute of an 'a' element or evaluating an expression over the 'item_url' element.

```config.ini
[options]
directory = /var/www/feeds/

[Jodel Engineering Blog]
url = https://jodel.com/engineering/
item_title = .post-title > a
item_date = .post-date
item_date_format = %%b %%d, %%Y
item_timezone = Europe/Berlin

[Ao3 Example - substitute ####### for fic id]
url = https://archiveofourown.org/works/#######/navigate
item_title = .chapter > li > a
item_url = .chapter > li > a
item_date = .chapter > li > .datetime
item_date_format = (%%Y-%%m-%%d)

[fanfiction.net Example - substitute ####### for fic id]
url = https://www.fanfiction.net/s/#######/
item_title = span > select#chap_select > option
item_url = span > select#chap_select > option
item_url_function = '/s/#######/' + url.get('value') + '/Example'
```

The script runs once daily in a cronjob on my local machine.
