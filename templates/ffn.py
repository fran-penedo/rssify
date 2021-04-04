# Currently does not work due to ffn blocking non-human access

url = r"https://www.fanfiction.net/s/([0-9]+)/"
name = "#profile_top b"
item_title = "span > select#chap_select > option"
item_url = "span > select#chap_select > option"
item_url_f = lambda url, url_groups: f"/s/{url_groups[0]}/{url.get('value')}"
