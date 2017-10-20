from django.shortcuts import render, render_to_response
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


def parse_from_api(url, file_name):
    s = urlopen(url)
    contents = s.read()
    file = open("%s.xml" % file_name, 'wb')
    file.write(contents)
    file.close()
    doc = xml.dom.minidom.parse("%s.xml" % file_name)
    content = doc.toxml()
    session.add("%s.xml" % file_name, content)
    os.remove("%s.xml" % file_name)

#create database
session.execute("create db musicbox")
#seed database
doc = xml.dom.minidom.parse("artists.xml")
content = doc.toxml()
session.add("artists.xml", content)

#add xml with top current tracks
get_top_tracks_url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key=79004d202567282ea27ce27e9c26a498"
parse_from_api(get_top_tracks_url, "toptracks")

#add xml with top portugal tracks
get_pt_top_tracks_url = "http://ws.audioscrobbler.com/2.0/?method=geo.gettopartists&country=portugal&api_key=79004d202567282ea27ce27e9c26a498"
parse_from_api(get_pt_top_tracks_url, "toptracks_portugal")

def home(request):
    assert isinstance(request, HttpRequest)
    tparams = {
        'title': 'MusicBox',
    }
    return render(request, 'index.html', tparams)

# Create your views here.

def top_tracks(request):

    print(request)
    session.execute("open musicbox")

    query = session.query("""for $b in collection('musicbox/artists.xml')//artists/artist
                             order by xs:integer($b/listeners) descending
                             return <result>{$b/name} {$b/listeners}</result>""")
    list = []
    for name in query.iter():
        list.append(name[1])
        

    return render(request,'index.html', {'list':list})

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
