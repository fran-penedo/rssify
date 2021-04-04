from setuptools import setup, find_packages

config = {
    "description": "Create RSS feeds from webpages using CSS selectors",
    "url": "https://github.com/fran-penedo/rssify",
    "author": "Fran Penedo",
    "author_email": "fran@franpenedo.com",
    "version": "1.0.0",
    "install_requires": [
        "tzlocal>=2.1",
        "pytz>=2021.1",
        "attrs>=20.3.0",
        "beautifulsoup4>=4.9.3",
        "feedgen>=0.9.0",
        "requests>=2.25.1",
    ],
    "extras_require": {"server": ["flask>=1.1.2"]},
    "packages": ["rssify"],
    "entry_points": {
        "console_scripts": [
            "rssify=rssify.core:main",
            "rssify-server=rssify.server:main",
        ],
    },
    "name": "rssify",
}

setup(**config)
