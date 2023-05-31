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


def fetch_dates(page):
    content = BeautifulSoup(page.content, "html.parser")
    start = end = None
    try:
        info = {}
        for tr in content.find(id="content").find("table").find_all("tr"):
            cols = [td.text for td in tr.find_all("td")]
            if len(cols) == 2:
                info[cols[0].rstrip(":")] = cols[1]
        if key := info.get("First visit", "").strip():
            start = datetime.strptime(key, "%Y.%m.%d %H:%M")
        if key := info.get("Last visit", "").strip():
            end = datetime.strptime(key, "%Y.%m.%d %H:%M")
    except AttributeError:
        pass
    return (start, end)


def get_all_user_agents(browser: Browser) -> List[list]:
    BASE = "https://www.useragentstring.com"
    ua_list = []
    try:
        page = requests.get(f"{BASE}/pages/{browser.value}/")
        if page.status_code != 200:
            raise ValueError(f"Loading status {page.status_code} {page.url}")
        content = BeautifulSoup(page.content, "html.parser")
        user_agents = [
            (a.text, a["href"])
            for a in content.find(id="content").find_all("a")
            if a["href"].startswith("/")
        ]
        for ua, link in tqdm(user_agents[:100], desc=browser.value):
            page = requests.get(f"{BASE}{link}")
            if page.status_code != 200:
                raise ValueError(f"Loading status {page.status_code} {page.url}")
            start, end = fetch_dates(page)
            if start and end:
                ua_list.append([browser.value, ua, str(start), str(end)])
            time.sleep(random.random())
    except (requests.exceptions.RequestException, ValueError) as e:
        print(e)
    return pd.DataFrame(ua_list, columns="browser,ua,start,end".split(","))


def main(cache_file: str = "./top_user_agents.csv"):
    data = [get_all_user_agents(n) for n in Browser.all()]
    df = pd.concat(data)
    df.to_csv(cache_file, index=False)


if __name__ == "__main__":
    main()
