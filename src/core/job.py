import requests
from local_settings import *


def syncdb(url, data):
    requests.post("/".join([FRONT_URL, url]), data)