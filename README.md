# Rssify

(Based on https://github.com/h43z/rssify.)

Rssify is a tool that builds RSS feeds from websites that don't have one.
It reads from a config file the websites you want to rssify, parsing title, url, date
and content via css selectors. The feed is then written to a directory.

Feeds can be manually described in the config file or using templates. A template is a
python module that defines a url regex that matches the urls you want to rssify using
the template, the css selectors for title, url, date and/or content, and functions that
are applied to the selected html elements.

A server can be optionally deployed to provide an HTTP API to add websites to rssify and
update the feeds. The server can be paired with a userscript to add websites covered by
a template with a shortcut from a web browser.

## Installation

Clone the repository:

    $ git clone https://github.com/fran-penedo/rssify
    
Install with PIP:

    $ pip install rssify
    
Optionally, install server requirements:

    $ pip install rssify[server]

Optionally, install the userscript. Install a userscript extension (for example,
[Greasemonkey for
firefox](https://addons.mozilla.org/en-US/firefox/addon/greasemonkey/)), then [click
here to install the userscript](https://raw.githubusercontent.com/fran-penedo/rssify/master/userscript/rssify.user.js).

## Usage

CLI usage is given by:

    $ rssify -h

Deploy the server to localhost with:

    $ rssify-server
    
If you want to deploy the server in a different setting, please refer to [Flask
documentation](https://flask.palletsprojects.com/en/1.1.x/deploying/#deployment).

The userscript provides the shortcut "C-S-u" to add a website to rssify. Make sure to
modify the URL if you deploy the server somewhere else.

You can update your feeds running rssify in a CRON job, or you can use the /update API
call for the server. If you add a website to the config manually, make sure to restart
the server.

## Copyright and Warranty Information

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2020-2021, Francisco Penedo Alvarez (contact@franpenedo.com)
