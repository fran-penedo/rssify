import re

url = r"https://store.steampowered.com/curator/[0-9a-zA-Z-]+/"
name = ".curator_name a"
item_title = ".recommendation_link"


def item_title_f(title, url_groups):
    return re.match(
        r"https://store\.steampowered\.com/app/[0-9]+/(.+)/.*", title.get("href")
    ).group(1)


item_url = ".recommendation_link"
item_content = ".recommendation_desc"
item_date = ".curator_review_date"
item_date_format = r"%d %B|%d %B, %Y|%B %d|%B %d, %Y"
