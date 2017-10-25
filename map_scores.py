#!/usr/bin/env python3

import json
from pprint import pprint

with open("scores", "r") as fh:
  scores = json.load(fh)


def ratingFunc(d):
  return d["cpuScore"]**2 * d["gpuScore"] / d["price"]**2


for score in scores:
  score["rating"] = ratingFunc(score)


for laptop in sorted(scores, key=lambda x: x["rating"]):
  print("Score:\t{:4.2f}\t{:}\t{:}\n\tOriginal:\t\t{:<30}\tOriginal:\t\t{:<30}\n\tMatched:\t\t{:<30}\tMatched:\t\t{:<30}\n\tMatchType:\t{:<30}\tMatchType:\t{:<30}\n\tScore:\t\t\t{:<30}\tScore:\t\t\t{:<30}\n\n".format(float(laptop["rating"]), laptop["price"], laptop["name"],
                                                               laptop["originalCpuName"], laptop["originalGpuName"],
                                                               laptop["matchedCpuName"], laptop["matchedGpuName"],
                                                               laptop["matchTypeCpu"], laptop["matchTypeGpu"],
                                                               laptop["cpuScore"], laptop["gpuScore"]))
