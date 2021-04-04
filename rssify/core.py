from __future__ import annotations

import argparse
import configparser
import importlib.util
import os
import re
import sys
import traceback
import urllib.parse as urlparse
from datetime import datetime
from glob import glob
from types import ModuleType
from typing import Any, Callable, Optional, Sequence, Tuple

import attr
import requests
from bs4 import BeautifulSoup  # type: ignore
from feedgen.feed import FeedGenerator  # type: ignore
from pytz import timezone

from tzlocal import get_localzone

CONFIG_FILES = ["./config.ini", "~/.rssify.ini", "~/.config/rssify/config"]
if os.environ.get("XDG_CONFIG_HOME"):
    CONFIG_FILES.append(os.path.join(os.environ["XDG_CONFIG_HOME"], "rssify/config"))


@attr.s(auto_attribs=True)
class Template(object):
    url: str
    item_title: str
    name: Optional[str] = None  # This is a selector, not an actual name
    name_f: Callable[[Any, Sequence[str]], str] = lambda x, y: x[0].text
    item_title_f: Callable[[Any, Sequence[str]], str] = lambda x, y: x.text
    item_url: Optional[str] = None
    item_url_f: Callable[[Any, Sequence[str]], str] = lambda x, y: x.get("href")
    item_content: Optional[str] = None
    item_content_f: Callable[[Any, Sequence[str]], str] = lambda x, y: x.text
    item_date: Optional[str] = None
    item_date_format: Optional[str] = None
    url_groups: Sequence[str] = attr.ib(factory=list)

    @classmethod
    def from_module(cls, m: ModuleType) -> "Template":
        return cls(**{v: getattr(m, v) for v in dir(m) if v in attr.fields_dict(cls)})


class InvalidFeedNameSelectorException(Exception):
    def __init__(self, selector: Optional[str]) -> None:
        super().__init__(f"Name selector returned empty set: {selector}")


def process_template(template: Template, name: str) -> FeedGenerator:
    r = requests.get(template.url)
    soup = BeautifulSoup(r.text, "lxml")
    titles = soup.select(template.item_title)
    urls = soup.select(template.item_url)

    if name == "":
        resultset = soup.select(template.name)
        if len(resultset) == 0:
            raise InvalidFeedNameSelectorException(template.name)
        name = template.name_f(soup.select(template.name), template.url_groups)

    if template.item_date is not None:
        dates = soup.select(template.item_date)
    else:
        dates = None

    if template.item_content is not None:
        contents = soup.select(template.item_content)
    else:
        contents = None

    fg = FeedGenerator()
    fg.title(name)
    fg.description(name)
    fg.link(href=template.url, rel="alternate")

    for i in range(len(titles)):
        if i > len(urls) - 1:
            break

        fe = fg.add_entry()

        fe.title(template.item_title_f(titles[i], template.url_groups))

        href = template.item_url_f(urls[i], template.url_groups)
        link = urlparse.urljoin(template.url, href)
        fe.link(href=link, rel="alternate")

        if contents is not None:
            fe.content(template.item_content_f(contents[i], template.url_groups))

        now = datetime.now(timezone("Europe/Berlin"))
        if dates is not None and template.item_date_format is not None:
            datestr = dates[i].text.strip()
            formats = template.item_date_format.split("|")
            date = None
            for form in formats:
                try:
                    date = datetime.strptime(datestr, form)
                except ValueError:
                    pass
            if date is None:
                raise ValueError(
                    "Date string '{}' has no valid formats: {}".format(datestr, formats)
                )
            # Set default year to current year
            if date.year == 1900:
                date = date.replace(year=now.year)
            date = date.replace(tzinfo=get_localzone())
        else:
            date = now
            # date = '1970-01-01 00:00:00+02:00'

        fe.published(date)

    return fg


def write_feed(fg: FeedGenerator, name: str, directory: str) -> str:
    feed_fn = name.replace(" ", "_") + ".xml"
    fg.rss_file(os.path.join(directory, feed_fn))
    return feed_fn


def load_templates(dirname: str) -> list[Template]:
    templates: list[Template] = []
    for fn in glob(f"{dirname}/*.py"):
        try:
            spec = importlib.util.spec_from_file_location(
                f"templates.{os.path.splitext(os.path.basename(fn))[0]}", fn
            )
            temp = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(temp)  # type: ignore
            templates.append(Template.from_module(temp))
        except Exception:
            raise

    return templates


def add_to_config(url: str, name: str, config: configparser.ConfigParser):
    config.add_section(name)
    config[name]["url"] = url


@attr.s(auto_attribs=True)
class Options(object):
    config: str = "./config.ini"
    templates: str = "./templates"
    feeds_url: str = "http://127.0.0.1:5000"
    directory: str = "."
    cmd: str = "update"
    url: str = ""
    name: str = ""

    def update(self, d: dict) -> None:
        for k, v in d.items():
            if hasattr(self, k) and v is not None:
                setattr(self, k, v)


def parse_config_file(fn: str) -> Tuple[Options, configparser.ConfigParser]:
    config = configparser.ConfigParser()
    config.read(fn)
    options = Options()

    options.update(dict(config["options"]))
    options.config = fn

    return options, config


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rssifies websites")
    parser.add_argument("--config", help="Path to a config file")
    parser.add_argument("--templates", help="Path to the templates directory")
    parser.add_argument("--directory", help="Path to save generated feeds to")
    cmds = parser.add_subparsers(
        dest="cmd",
        help="Rssify command. If no command is specified, runs `rssify update`",
    )
    add = cmds.add_parser("add", help="Adds a website to rssify. Must match a template")
    add.add_argument("url", help="URL of the website to rssify")
    add.add_argument(
        "name",
        nargs="?",
        help="Title for the RSS feed. Can be omitted if the template defines a `name`",
    )
    cmds.add_parser("update", help="Updates feeds. Default command")
    rm = cmds.add_parser("remove", help="Removes a website")
    rm.add_argument("name", help="Name of the website to remove")

    return parser


def parse_config() -> Tuple[Options, configparser.ConfigParser]:
    argparser = build_arg_parser()
    args = argparser.parse_args()
    if args.config is not None:
        CONFIG_FILES.insert(0, args.config)

    for f in CONFIG_FILES:
        try:
            options, config = parse_config_file(f)
            break
        except FileNotFoundError:
            pass

    options.update(vars(args))

    return options, config


def setup() -> Tuple[Options, configparser.ConfigParser, list[Template]]:
    opts, config = parse_config()
    if not os.path.exists(opts.directory):
        os.makedirs(opts.directory)

    templates = load_templates(opts.templates)

    return opts, config, templates


def update(
    opts: Options, config: configparser.ConfigParser, templates: list[Template]
) -> None:
    config.remove_section("options")

    for section in config.sections():
        s = dict(config.items(section))
        temp = next((t for t in templates if re.match(t.url, s["url"])), None)
        if temp is None:
            temp = Template(**s)  # type: ignore # config should be well written or this throws exception
        else:
            match = re.match(temp.url, s["url"])
            assert match is not None
            temp.url_groups = match.groups()
        temp.url = s["url"]
        try:
            fg = process_template(temp, section)
            write_feed(fg, section, opts.directory)
        except Exception:
            print("In {}:".format(section), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


class NoTemplateForLinkException(Exception):
    def __init__(self, url: str):
        super().__init__(f"No template found for url: {url}")


def add(
    opts: Options, config: configparser.ConfigParser, templates: list[Template]
) -> str:
    temp = next((t for t in templates if re.match(t.url, opts.url)), None)
    if temp is not None:
        temp.url = opts.url
        try:
            fg = process_template(temp, opts.name)
            feed_fn = write_feed(fg, fg.title(), opts.directory)
            try:
                add_to_config(temp.url, fg.title(), config)
            except configparser.DuplicateSectionError:
                pass
            with open(opts.config, "w") as f:
                config.write(f)
            return feed_fn
        except Exception:
            raise
    else:
        raise NoTemplateForLinkException(opts.url)


def remove(
    opts: Options, config: configparser.ConfigParser, templates: list[Template]
) -> None:
    if opts.name in config.sections():
        config.remove_section(opts.name)
        with open(opts.config, "w") as f:
            config.write(f)


def main() -> None:
    opts, config, templates = setup()

    if opts.cmd == "update":
        update(opts, config, templates)
    elif opts.cmd == "add":
        add(opts, config, templates)
    elif opts.cmd == "remove":
        remove(opts, config, templates)


if __name__ == "__main__":
    main()
