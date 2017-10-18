#!/usr/bin/python3

import requests
import json
from bs4 import BeautifulSoup

def generateDB():
  url = "https://www.cpubenchmark.net/cpu_list.php"
  headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0'}

  contents = requests.get(url, headers=headers)
  text = contents.text

  with open("cpu.html", "w") as fh:
    fh.write(text)

  soup = BeautifulSoup(text, 'html.parser')
  soup = soup.find('tbody')

  cards = {}
  for cardInfo in soup.find_all('tr'):
    name = cardInfo.find('a').contents[0]
    score = cardInfo.find_all('td', limit=2)[1].contents[0]
    cards[name] = int(score)

  json.dump(cards, open('cpu_info', 'w'), indent=2, sort_keys=True)
