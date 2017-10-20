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
        'title': 'MusicBox',
    }
    return render(request, 'index.html', tparams)

# Create your views here.

session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
session.execute("create db musicbox")
doc = xml.dom.minidom.parse("artists.xml")
content = doc.toxml()
session.add("artists.xml", content)

def top_tracks(request):

    session.execute("open musicbox")

    query = session.query("""for $b in collection('musicbox/artists.xml')//artists/artist
                             order by xs:integer($b/listeners) descending
                             return <result>{$b/name} {$b/listeners}</result>""")
    list = []
    for name in query.iter():
        list += name[1] + "<br>"

    return HttpResponse(list)

def login(request):
    return render(request)

def artists(request):
    return render(request, 'artists.html')

def albums(request):
    return render(request, 'albums.html')

def charts(request):
    return render(request, 'charts.html')

def albuminfo(request):
    return render(request, 'albuminfo.html')

def artist_page(request):
    return render(request, 'artist_page.html')
