#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
import threading
import time
import os
import difflib


def getLaptops():
  """ Get the n cheapest laptops from edbpriser.dk and store them in a file """
  sys.stdout.write("Scraping edbpriser.dk")
  sys.stdout.flush()
  n = 2000
  url = "http://www.edbpriser.dk/computer/baerbar-laptop.aspx?count={}&sort=TotalPrice&rlm=List".format(n)
  headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:56.0) Gecko/20100101 Firefox/56.0'}

  contents = requests.get(url, headers=headers)
  text = contents.text

  soup = BeautifulSoup(text, 'html.parser')
  soup = soup.find('ul', class_='product-result product-list')

  links = []
  for a in soup.find_all('a'):
    link = a.get('href')
    if link and link.startswith('/baerbar-laptop/') and not link.endswith('#priceagent') and "galleri" not in link:
      if link not in links:
        links.append(link)

  with open("laptops", 'w') as fh:
    fh.write("\n".join(links))
  sys.stdout.write("\tDone\n")
  sys.stdout.flush()


def getSpecs(laptop):
  url = "http://www.edbpriser.dk" + laptop
  headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0'}

  contents = requests.get(url, headers=headers)
  text = contents.text

  soup = BeautifulSoup(text, 'html.parser')
  spec = soup.find('div', class_="ProductSpecList")
  if spec:
    info = {}
    for row in spec.findAll('tr'):
        aux = row.findAll('td')
        if len(aux) > 1:
          info[aux[0].string] = aux[1].string
    price = soup.find('div', class_="floatLeft")['content']
    spec = [info, int(price)]
  return spec


def getSpecAndStore(laptop):
  q = getSpecs(laptop)
  if q:
    name = laptop.replace("/baerbar-laptop/", "")
    json.dump(q, open('specs/' + name, 'w'), indent=2, ensure_ascii=False)
  # else:
  #   print("No specs found for\n\t{:}".format(laptop))


def storeAllSpecs():
  sys.stdout.write("Setting up spec files\n")
  sys.stdout.flush()

  if "specs" not in os.listdir("."):
    os.mkdir("specs")

  with open('laptops', 'r') as fh:
    laptops = [l.strip() for l in fh.readlines()]

  specsExists = os.listdir("specs")
  threads = []
  for i, laptop in enumerate(laptops):
    if (i + 1) % int(len(laptops)/10) == 0:
      print("{} out of {}".format(i + 1, len(laptops)))
    name = laptop.replace("/baerbar-laptop/", "")
    if name in specsExists:
      continue

    try:
      threads.append(threading.Thread(target=getSpecAndStore, args=(laptop, )))
      threads[-1].start()
      # Avoid sending too many requests too quickly
      time.sleep(0.2)
    except Exception as e:
      print(e)

  sys.stdout.write("Finishing")
  sys.stdout.flush()
  for thread in threads:
    thread.join()
  sys.stdout.write("\tDone\n")
  sys.stdout.flush()


def setUpDbs():
  sys.stdout.write("Setting up benchmark lookup files")
  sys.stdout.flush()
  import generate_cpu_db as cpu
  import generate_gpu_db as gpu
  cpu.generateDB()
  gpu.generateDB()
  sys.stdout.write("\tDone\n")
  sys.stdout.flush()


def findCpu(path, info, cpus):
  name = info['Processornr.']
  if name in cpus:
    return name, name, 0

  sub = [cpu for cpu in cpus if name.lower() in cpu.lower()]
  if len(sub) == 1:
    return sub[0], name.lower(), 1

  diff = difflib.get_close_matches(name, cpus, 1)
  if diff:
    return diff[0], name, 2

  if 'Processor type' in info and not name.startswith(info['Processor type']):
    info['Processornr.'] = info['Processor type'] + ' ' + name
    ret = findCpu(path, info, cpus)
    if ret:
      return ret

  print("Cpu not found for {}".format(path))


def findGpu(path, info, gpus):
  name = info['Grafikprocessor'].split("/")[0].replace("NVIDIA", "").replace("AMD", "").strip()
  if name in gpus:
    return name, name, 0

  sub = [name for name in gpus if name in gpus.keys()]
  if len(sub) == 1:
    return sub[0], name.lower(), 1

  diff = difflib.get_close_matches(name, gpus, 1)
  if diff:
    return diff[0], name, 2

  print("Gpu not found for {}".format(path))


def giveScore(path, cpus, gpus):
  with open(path, 'r') as fh:
    info, price = json.load(fh)

  cpu, cpuOriginal, matchTypeCpu = findCpu(path, info, cpus)
  if cpu:
    cpuScore = cpus[cpu]
  else:
    cpuScore = 0

  gpu, gpuOriginal, matchTypeGpu = findGpu(path, info, gpus)
  if gpu:
    gpuScore = gpus[gpu]
  else:
    gpuScore = 0

  return {"cpuScore": cpuScore,
          "matchedCpuName": cpu,
          "originalCpuName": cpuOriginal,
          "matchTypeCpu": matchTypeCpu,
          "gpuScore": gpuScore,
          "matchedGpuName": gpu,
          "originalGpuName": gpuOriginal,
          "matchTypeGpu": matchTypeGpu,
          "price": price}


def rateAll():
  sys.stdout.write("Rating laptops\n")
  sys.stdout.flush()
  laptops = os.listdir('specs')
  cpuBenchmark = json.load(open("cpu_info", 'r'))
  gpuBenchmark = json.load(open("gpu_info", 'r'))
  scores = []
  for laptop in laptops:
    try:
      score = giveScore('specs/' + laptop, cpuBenchmark, gpuBenchmark)
    except Exception as e:
      print(laptop, e)
      continue
    score["name"] = laptop
    scores.append(score)
  json.dump(scores, open("scores", 'w'), indent=2, ensure_ascii=False)
  sys.stdout.write("\tDone\n")
  sys.stdout.flush()


if __name__ == "__main__":
  import sys
  if len(sys.argv) != 2:
    print("Usage: <what to do (a/b/c/d/e)>\n\ta: scrape edbpriser.dk\n\tb: set up specs files\n\tc: set up benchmark loopup files\n\td: rate all laptops\n\te: do it all")
    exit(-1)
  if sys.argv[1] == 'a':
    getLaptops()

  elif sys.argv[1] == 'b':
    storeAllSpecs()

  elif sys.argv[1] == 'c':
    setUpDbs()

  elif sys.argv[1] == 'd':
    rateAll()

  elif sys.argv[1] == 'e':
    getLaptops()
    storeAllSpecs()
    setUpDbs()
    rateAll()
