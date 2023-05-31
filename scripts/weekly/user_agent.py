"""
Utility to fetch top user-agents from useragentstring.com with 
first and last used date for top browsers.
"""
import argparse
import os
import random
import time
from datetime import datetime
from enum import Enum
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class Browser(Enum):
    Chrome = "Chrome"
    Safari = "Safari"
    Firefox = "Firefox"
    Edge = "Edge"
    Opera = "Opera"

    def any():
        return Browser._member_map_[random.choice(Browser._member_names_)]

    def all():
        return Browser._member_map_.values()


def fetch_dates(content):
    first = last = None
    try:
        info = {}
        for tr in content.find(id="content").find("table").find_all("tr"):
            cols = [td.text for td in tr.find_all("td")]
            if len(cols) == 2:
                info[cols[0].rstrip(":")] = cols[1]
        if key := info.get("First visit", "").strip():
            first = datetime.strptime(key, "%Y.%m.%d %H:%M")
        if key := info.get("Last visit", "").strip():
            last = datetime.strptime(key, "%Y.%m.%d %H:%M")
    except AttributeError:
        pass
    return (first, last)


def fetch_content(link: str) -> BeautifulSoup:
    BASE = "https://www.useragentstring.com"
    try:
        page = requests.get(f"{BASE}{link}")
        if page.status_code != 200:
            raise ValueError(f"Loading status {page.status_code} {page.url}")
        return BeautifulSoup(page.content, "html.parser")
    except (requests.exceptions.RequestException, ValueError) as e:
        print(e)
        return None


def get_all_user_agents(browser: Browser, limit: int = 100) -> List[list]:
    content = fetch_content(f"/pages/{browser.value}/")
    user_agents = [
        (a.text, a["href"])
        for a in content.find(id="content").find_all("a")
        if a["href"].startswith("/")
    ]
    ua_list = []
    for ua, link in tqdm(user_agents[:limit], desc=browser.value):
        first, last = fetch_dates(fetch_content(link))
        if first and last:
            ua_list.append([browser.value, ua, str(first), str(last)])
        time.sleep(random.random())
    return pd.DataFrame(ua_list, columns="browser,ua,first,last".split(","))


def main():
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./top_user_agents.csv",
        help="output CSV file",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=100,
        help="limit number of entries to process per browser",
    )
    args = parser.parse_args()

    data = [get_all_user_agents(n, limit=args.limit) for n in Browser.all()]
    df = pd.concat(data)
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
