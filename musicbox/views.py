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

session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')

def home(request):
    assert isinstance(request, HttpRequest)
    tparams = {
        'title': 'MusicBox',
    }
    return render(request, 'index.html', tparams)

# Create your views here.

def users(request):
    doc = xml.dom.minidom.parse("Users.xml")
    content = doc.toxml()

    session.add("users.xml", content)
    session.query("""find """)
    query = session.query("""for $b in collection("musicbox/users")//user return $b/email""")
    list=[]
    for email in query.iter():
        list += email

    return HttpResponse(list)

def top_tracks(request):
    session.execute("open musicbox")
    url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key=79004d202567282ea27ce27e9c26a498"
    s = urlopen(url)
    contents = s.read()
    file = open("toptracks.xml", 'wb')
    file.write(contents)
    file.close()

    doc = xml.dom.minidom.parse("toptracks.xml")
    content = doc.toxml()

    session.add("toptracks.xml", content)

    os.remove("toptracks.xml")

    query = session.query("""for $b in collection("musicbox/toptracks")//track return $b/name""")
    list = []
    for name in query.iter():
        list += name[1] + "<br>"

    return HttpResponse(list)


def login(request):
    return render(request)


def music(request):
    assert isinstance(request, HttpRequest)
    b = {
        'music': 'oi',
    }
    return render(request, 'music.html', b)

def allsongs(request):
    assert isinstance(request, HttpRequest)
    b = {
        'music': 'oi',
    }
    return render(request, 'allsongs.html', b)

