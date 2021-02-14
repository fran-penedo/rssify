Forked from https://github.com/h43z/rssify.

I looked at a few online services that provide custom created RSS feeds
for websites that don't have one. None of them were free of charge 
without being too much limited in functionality for me.

So I hacked together this very simple rssify.py script.
It reads from a config file your websites you want to rssify.
It could be easily extened for more features if needed.
For now it parses the title, url, date and content via css selectors and generates
a feed.xml file which can be imported into newsboat/newsbeuter or I guess any
other rss reader.

For title, url and content, you can evaluate an expression over the
'item_title', 'item_url' or 'item_content' element, which are in a variable
named 'title', 'url' or 'content'. If no function is defined, it gets text,
href and text respectively by default.

You can specify several date formats separated by '|'.

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

[Steam Curator Example - substitute ######## for curator id and name]
url = https://store.steampowered.com/curator/########/
item_title = .recommendation_link
item_title_function = re.match(r'https://store\.steampowered\.com/app/[0-9]+/(.+)/.*', title.get('href')).group(1)
item_url = .recommendation_link
item_content = .recommendation_desc
item_date = .curator_review_date
item_date_format = %%B %%d|%%B %%d, %%Y
```

The script runs once daily in a cronjob on my local machine.
