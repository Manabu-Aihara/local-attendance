from urllib.request import urlopen
from urllib.error import (HTTPError, URLError)
from bs4 import BeautifulSoup
import requests
import re

def connect_test():
  try:
      pattern = r'\d+$'
      url = 'http://127.0.0.1:8000/notification-list/20'
      html = requests.get(url)
  except HTTPError as e:
      print(e)
  except URLError as e:
      print("Server could not be found.")
  # else:
  #     print("It works!")

  bsObj = BeautifulSoup(html.content, "html.parser")
  # for select_tag in bsObj.find_all("select", {"class": "search-date"}):
  print(bsObj.body)
