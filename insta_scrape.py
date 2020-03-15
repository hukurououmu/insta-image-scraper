import os
import sys
import json
import time
import uuid
import requests
from random import choice
from bs4 import BeautifulSoup


_user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9",
    "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36"
]


class Colors():
    GREEN  = "\033[92m"


class InstagramScraper():

    def __init__(self, user_agent=None, proxy=None):
        self.user_agent = user_agent
        self.proxy = proxy


    def __random_agent(self):
        if self.user_agent and isinstance(self.user_agent, list):
            return choice(self.user_agent)
        return choice(_user_agents)


    def __request_url(self, url):
        try:
            res = requests.get(
                url, 
                headers={"User-Agent": self.__random_agent()}, 
                proxies={"http": self.proxy,"https": self.proxy}
            )
            res.raise_for_status()
        except requests.HTTPError:
            raise requests.HTTPError("Received non 200 status code from Instagram")
        except requests.RequestException:
            raise requests.RequestException
        else:
            return res.text


    @staticmethod
    def extract_json_data(html):
        soup = BeautifulSoup(html, "lxml")
        body = soup.find("body")
        script_tag = body.find("script")
        raw_string = script_tag.text.strip().replace("window._sharedData =", "").replace(";", "")
        return json.loads(raw_string)


    def profile_page_metrics(self, profile_url):
        results = {}
        try:
            res = self.__request_url(profile_url)
            json_data = self.extract_json_data(res)
            metrics = json_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]
        except Exception as e:
            raise e
        else:
            for key, value in metrics.items():
                if key != "edge_owner_to_timeline_media":
                    if value and isinstance(value, dict):
                        value = value["count"]
                        results[key] = value
                    elif value:
                        results[key] = value
        return results


    def profile_page_recent_posts(self, profile_url):
        results = []
        try:
            res = self.__request_url(profile_url)
            json_data = self.extract_json_data(res)
            metrics = json_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
        except Exception as e:
            raise e
        else:
            for node in metrics:
                node = node.get("node")
                if node and isinstance(node, dict):
                    results.append(node)
        return results


try:
    account_name = input("> Enter the instagram account name:")
    while not account_name:
        account_name = input("> Enter the instagram account name:")
except:
    print("\n> The account does not exist or is a key account")
    sys.exit()

if not os.path.exists("./img/{}/".format(account_name)):
    os.mkdir("./img/{}/".format(account_name))


def json_write():
    k = InstagramScraper()       
    results = k.profile_page_recent_posts("https://www.instagram.com/{}/?hl=ja".format(account_name))
    with open("insta.json", "w") as f:
        json.dump(results, f, indent=4)


def download():
    with open("insta.json", "r") as json_file:
        json_obj = json.load(json_file)
        img_objs = [d.get("display_url") for d in json_obj]
        print(Colors.GREEN + "Downloading image from {}...".format(account_name))
        try:
            for imgfile in img_objs:
                res = requests.get(imgfile)
                time.sleep(1)
                filename = str(uuid.uuid4()) + ".jpg"
                with open("./img/{}/".format(account_name) + filename, "wb") as f:
                    f.write(res.content)
        except FileNotFoundError:
            print("> Please make a [img] folder")
            sys.exit()
        print("✔Downloaded " + str(len(img_objs)) + " images")


def main():
    json_write()
    download()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n> Exit program")
        sys.exit()