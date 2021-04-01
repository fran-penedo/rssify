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
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from pytz import timezone

from tzlocal import get_localzone

CONFIG_FILES = ["./config.ini", "~/.rssify.ini", "~/.config/rssify/config"]
if os.environ.get("XDG_CONFIG_HOME"):
    CONFIG_FILES.append(os.path.join(os.environ["XDG_CONFIG_HOME"], "rssify/config"))


@attr.s(auto_attribs=True)
class Template(object):
    url: str
    item_title: str
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


def process_template(template: Template, name: str, directory: str) -> None:
    r = requests.get(template.url)
    soup = BeautifulSoup(r.text, "lxml")
    titles = soup.select(template.item_title)
    urls = soup.select(template.item_url)

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

    fg.rss_file(os.path.join(directory, name.replace(" ", "_") + ".xml"))


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
        except:
            raise

    return templates


def add_to_config(url: str, name: str, config: configparser.ConfigParser):
    config.add_section(name)
    config[name]["url"] = url


@attr.s(auto_attribs=True)
class Options(object):
    config: str = "./config.ini"
    templates: str = "./templates"
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
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--config")
    parser.add_argument("--templates")
    parser.add_argument("--directory")
    cmds = parser.add_subparsers(dest="cmd")
    add = cmds.add_parser("add")
    add.add_argument("url")
    add.add_argument("name")
    cmds.add_parser("update")
    rm = cmds.add_parser("remove")
    rm.add_argument("name")

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


def main() -> None:
    opts, config = parse_config()
    if not os.path.exists(opts.directory):
        os.makedirs(opts.directory)

    templates = load_templates(opts.templates)

    if opts.cmd == "update":
        config.remove_section("options")

        for section in config.sections():
            s = dict(config.items(section))
            temp = next(
                (t for t in templates if (match := re.match(t.url, s["url"]))), None
            )
            if temp is None:
                temp = Template(**s)  # type: ignore # config should be well written or this throws exception
            else:
                assert match is not None
                temp.url_groups = match.groups()
            temp.url = s["url"]
            try:
                process_template(temp, section, opts.directory)
            except Exception as e:
                print("In {}:".format(section), file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    elif opts.cmd == "add":
        temp = next((t for t in templates if re.match(t.url, opts.url)), None)
        if temp is not None:
            temp.url = opts.url
            try:
                process_template(temp, opts.name, opts.directory)
                add_to_config(temp.url, opts.name, config)
                with open(opts.config, "w") as f:
                    config.write(f)
            except:
                raise

    elif opts.cmd == "remove":
        if opts.name in config.sections():
            config.remove_section(opts.name)
            with open(opts.config, "w") as f:
                config.write(f)


if __name__ == "__main__":
    main()
