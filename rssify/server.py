from __future__ import annotations

import urllib.parse
import os

from flask import Flask, request
from flask_cors import CORS

import rssify.core as rssify


def setup() -> Flask:
    app = Flask("rssify")
    CORS(app)
    # app.logger.setLevel(10)

    opts, config, templates = rssify.setup()

    @app.route("/add", methods=["POST"])
    def add_link() -> dict:
        opts.url = request.json["url"]
        app.logger.debug(f"{opts = }")
        app.logger.debug(f"{config = }")
        try:
            feed_path = rssify.add(opts, config, templates)
            app.logger.debug(f"{feed_path = }")
            response = {
                "link": urllib.parse.urljoin(opts.feeds_url, feed_path),
                "added": True,
            }
        except rssify.NoTemplateForLinkException as e:
            response = {"link": "", "added": False, "reason": str(e)}
        except rssify.InvalidFeedNameSelectorException as e:
            response = {"link": "", "added": False, "reason": str(e)}
        app.logger.debug(f"{response = }")
        return response

    @app.route("/update")
    def update() -> str:
        rssify.update(opts, config, templates)
        return "Updated"

    return app


def main() -> None:
    app = setup()
    app.logger.debug("Setup complete")
    app.run()


if __name__ == "__main__":
    main()
