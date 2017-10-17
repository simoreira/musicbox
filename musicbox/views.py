from django.shortcuts import render
import BaseXClient
import urllib
import urllib.request
from urllib.request import urlopen
import xml.dom.minidom
import os
from django.http import HttpResponse
from django.http import HttpRequest
from datetime import datetime

def home(request):
    assert isinstance(request, HttpRequest)
    tparams = {
        'title': 'Home Page',
        'year': datetime.now().year,
    }
    return render(request, 'index.html', tparams)



session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
session.execute("create db musicbox")

# Create your views here.
def top_tracks(request):
    url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key=79004d202567282ea27ce27e9c26a498"
    s = urlopen(url)
    contents = s.read()
    file = open("toptracks.xml", 'wb')
    file.write(contents)
    file.close()

    doc = xml.dom.minidom.parse("toptracks.xml")
    content = doc.toxml()
    print(session.info())

    session.add("musicbox/toptracks.xml", content)

    os.remove("toptracks.xml")

    query = session.query("""for $b in collection("toptracks")//track return $b/name""")
    list = []
    for name in query.iter():
        list += name[1] + "<br>"

    return HttpResponse(list)


def login(request):
    return render(request)




