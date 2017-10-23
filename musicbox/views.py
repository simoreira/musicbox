from django.shortcuts import render, render_to_response
import BaseXClient
import urllib
import urllib.request
from urllib.request import urlopen
import xml.dom.minidom
import os
from django.http import HttpResponse
from django.http import HttpRequest, Http404, HttpResponseRedirect
from datetime import datetime
import xml.etree.cElementTree as lic
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import xmlschema
import sys
import json
session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')


def parse_from_api(url, file_name):
    s = urlopen(url)
    contents = s.read()
    file = open("%s.xml" % file_name, 'wb')
    file.write(contents)
    file.close()
    doc = xml.dom.minidom.parse("%s.xml" % file_name)
    content = doc.toxml()

    ## CHECK LATER
    #query = session.query("""let $doc := '%s.xml'
    #                let $schema := '%s.xsd'
    #               return
        #              if (validation:validate($doc, $schema)) then
            #             "PASS"
    #                  else (
    #                    "FAIL"
           #              validation:validate-report($doc, $schema)
                   #      """ % (file_name, file_name))
    #query.execute()

    schema = xmlschema.XMLSchema('%s.xsd' % file_name)
    if(schema.is_valid('%s.xml' %file_name)):
        print("%s.xml is a valid XML file." % file_name)
        session.add("%s.xml" % file_name, content)
    else:
        print("%s.xml is an invalid XML file." %file_name)
        sys.exit()

    os.remove("%s.xml" % file_name)

#create database
session.execute("create db musicbox")
#seed database
doc = xml.dom.minidom.parse("artists.xml")
content = doc.toxml()
schema = xmlschema.XMLSchema('artists.xsd')

if(schema.is_valid('artists.xml')):
    print("artists.xml is a valid XML file.")
    session.add("artists.xml", content)
else:
    print("artists.xml is an invalid XML file.")
    sys.exit()
#add xml with top current tracks
get_top_tracks_url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key=79004d202567282ea27ce27e9c26a498"
parse_from_api(get_top_tracks_url, "toptracks")

#add xml with top portugal tracks
get_pt_top_tracks_url = "http://ws.audioscrobbler.com/2.0/?method=geo.gettoptracks&country=portugal&api_key=79004d202567282ea27ce27e9c26a498"
parse_from_api(get_pt_top_tracks_url, "toptrack_portugal")


def home(request):
    assert isinstance(request, HttpRequest)
    session.execute("open musicbox")

    query = session.query("""for $b in collection('musicbox/artists.xml')//artists/artist
                             order by xs:integer($b/listeners) descending
                             return concat(xs:string($b/name/text()),':',xs:string($b/listeners/text()))""")

    list = []
    tmp = dict()
    for name in query.iter():
        tmp['Name'] = name[1].split(':')[0]
        tmp['Number'] = name[1].split(':')[1]
        list.append(tmp)
        tmp = dict()


    page = request.GET.get('page', 1)

    paginator = Paginator(list, 10)
    try:
        artists = paginator.page(page)
    except PageNotAnInteger:
        artists = paginator.page(1)
    except EmptyPage:
        artists = paginator.page(paginator.num_pages)

    return render(request,'index.html', {'artists':artists})

def login(request):
    return render(request)

def artists(request):
    return render(request, 'artists.html')

def albums(request):
    assert isinstance(request, HttpRequest)
    session.execute("open musicbox")

    letter = 'L'
    print(letter)
    query = session.query("""for $x in collection("musicbox/artists.xml")//artists/artist/album
                              where starts-with($x/name, """ + "'" + letter + "')""""
                              order by $x/name
                              return $x/name/text()""")
    albums = []
    tmp = dict()
    for album in query.iter():
        tmp['Name'] = album[1]
        albums.append(tmp)

        tmp = dict()

    return render(request, 'albums.html', {'albums':albums})

def charts(request):
    return render(request, 'charts.html')

def albuminfo(request):
    assert isinstance(request, HttpRequest)
    tracks = []
    tmp = dict()

    album_name = request.GET['name']

    session.execute("open musicbox")
    query = session.query("""for $a in collection("musicbox/artists.xml")//artists/artist/album
                                    where $a/name=""" + "'" + album_name + "'""""
                                    return $a/tracks/track/concat(xs:string(name/text()),':', xs:string(duration/text()))""")

    for track in query.iter():
        tmp['name'] = track[1].split(':')[0]
        tmp['duration'] = track[1].split(':')[1]
        tracks.append(tmp)
        tmp = dict()

    query2 = session.query("""for $a in collection("musicbox/artists.xml")//artists/artist/album
                                where $a/name=""" + "'" + album_name + "'""""
                                return $a/tags/tag/name/text()""")

    tags = []
    tags_dic = dict()
    for tag in query2.iter():
        tags_dic['tag'] = tag[1]
        tags.append(tags_dic)
        tags_dic = dict()


    query3 = session.query("""for $a in collection("musicbox/artists.xml")//artists/artist/album
                                where $a/name=""" + "'" + album_name + "'""""
                                return $a/wiki/summary/text()""")

    wiki = ""
    for w in query3.iter():
        wiki = w[1]

    query4 = session.query("""for $a in collection('musicbox/artists.xml')//artists/artist/album[name=""" + "'" + album_name + "'""""]/image[@size='extralarge']
                            return $a/text()""")
    photo = ""
    for p in query4.iter():
        photo = p[1]

    return render(request, 'albuminfo.html', {'tracks':tracks, 'tags':tags, 'wiki':wiki, 'photo':photo})

def artist_page(request):
    return render(request, 'artist_page.html')