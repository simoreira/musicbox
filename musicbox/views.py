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
import xml.etree.cElementTree as etree
import lxml.etree as ET


session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')


def parse_from_api(url, file_name):
    s = urlopen(url)
    contents = s.read()
    file = open("%s.xml" % file_name, 'wb')
    file.write(contents)
    file.close()
    doc = xml.dom.minidom.parse("%s.xml" % file_name)
    content = doc.toxml()

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

    rss_url = "http://www.rollingstone.com/music/rss"
    s = urlopen(rss_url)
    contents = s.read()
    file = open("rss.xml", 'wb')
    file.write(contents)
    file.close()

    rss_xml = ET.parse("rss.xml")
    xslt = ET.parse("rss.xslt")
    transform = ET.XSLT(xslt)
    new_rss_xml = transform(rss_xml)
    file = open("%s/new_rss.xml" % os.path.dirname(os.path.abspath(__file__)), 'wb')
    file.write(new_rss_xml)
    file.close()

    os.remove("rss.xml")

    tree = etree.parse('%s/new_rss.xml' % os.path.dirname(os.path.abspath(__file__)))
    root = tree.getroot()
    news = dict()
    news_list = []

    for elem in root.iter('item'):
        news['Title'] = elem.find("title").text
        news['Link'] = elem.find("link").text
        news['Image'] = elem.find("media").text

        news_list.append(news)
        news = dict()

    os.remove("%s/new_rss.xml" % os.path.dirname(os.path.abspath(__file__)))

    query2 = session.query("""(for $b in collection('musicbox/artists.xml')//artists/artist
                                     order by xs:integer($b/listeners) descending
                                     return concat(xs:string($b/name/text()),'_$!_', xs:string($b/listeners), '_$!_', xs:string($b/image[@size='large']/text())))[position()=1 to 12]""")

    list = []
    top_artist = dict()
    count =0
    for name in query2.iter():
        top_artist['name'] = name[1].split('_$!_')[0]
        top_artist['listeners'] = name[1].split('_$!_')[1]
        top_artist['imagem'] = name[1].split('_$!_')[2]
        count += 1
        top_artist['count'] = count
        list.append(top_artist)
        top_artist = dict()

    return render(request, 'index.html', {'artists': list, 'news': news_list})

def search_query(request):

    search = dict(request.POST)

    term = search.get('search_term')[0]

    print(term)

    search_artist = session.query("""file:write("%s/result.xml",<root> {
                                             for $x in collection("musicbox/artists.xml")//artists/artist
                                             where (contains($x/name, "%s"))
                                             return <artist>{$x/name, $x/image[@size='large']}</artist>}</root>)""" % (os.path.dirname(
        os.path.abspath(__file__)), term))

    search_album = session.query("""file:write("%s/result2.xml", <root>{
                                            for $x in collection("musicbox/artists.xml")//artists/artist/album
                                            where (contains($x/name, "%s"))
                                            return <album>{$x/name, $x/image[@size='large']}</album>}</root>)""" % (os.path.dirname(
        os.path.abspath(__file__)), term))
    search_artist.execute()
    search_album.execute()

    artists_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    artists_root = artists_tree.getroot()
    artists_result = dict()
    artists_list = []

    albums_tree = etree.parse('%s/result2.xml' % os.path.dirname(os.path.abspath(__file__)))
    albums_root = albums_tree.getroot()
    albums_result = dict()
    albums_list = []

    for elem in artists_root.iter('artist'):
        artists_result['Name'] = elem.find('name').text
        artists_result['Image'] = elem.find('image').text
        artists_list.append(artists_result)
        artists_result = dict()

    for elem in albums_root.iter('album'):
        albums_result['Name'] = elem.find('name').text
        albums_result['Image'] = elem.find('image').text
        albums_list.append(albums_result)
        albums_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result2.xml" % os.path.dirname(os.path.abspath(__file__)))

    if not albums_list and not artists_list:
        return render(request, 'searchNFound.html')
    elif not albums_list and artists_list:
        return render(request, 'search.html', {'artists':artists_list})
    elif not artists_list and albums_list:
        return render(request, 'search.html', {'albums': albums_list})
    else:
        return render(request, 'search.html', {'albums': albums_list, 'artists': artists_list})


def artists(request):
    assert isinstance(request, HttpRequest)
    list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
            'V', 'W', 'X', 'Y', 'Z']
    lst = dict()
    flist = []
    for l in list:
        lst['ll'] = l[0]
        flist.append(lst)
        lst = dict()

    if request.GET.get('name') == None:
        letter = 'A'
    else:
        letter = request.GET.get('name')

    session.execute("open musicbox")
    query = session.query("""for $x in collection("musicbox/artists.xml")//artists/artist
                                      where starts-with($x/name, """ + "'" + letter + "')""""
                                      order by $x/name
                                      return concat(xs:string($x/name/text()), '_$!_', xs:string($x/image[@size='large']/text()))""")
    artists = []
    tmp = dict()
    for art in query.iter():
        tmp['Name'] = art[1].split('_$!_')[0]
        tmp['Imagem'] = art[1].split('_$!_')[1]
        artists.append(tmp)
        tmp = dict()

    return render(request, 'artists.html', {'artists': artists, 'flist': flist})

def albums(request):
    assert isinstance(request, HttpRequest)
    list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U',
            'V', 'W', 'X', 'Y', 'Z']
    lst = dict()
    flist = []
    for l in list:
        lst['ll'] = l[0]
        flist.append(lst)
        lst = dict()

    if request.GET.get('name') == None:
        letter = 'A'
    else:
        letter = request.GET.get('name')

    session.execute("open musicbox")
    query = session.query("""for $x in collection("musicbox/artists.xml")//artists/artist/album
                                  where starts-with($x/name, """ + "'" + letter + "')""""
                                  order by $x/name
                                  return concat(xs:string($x/name/text()), '_$!_', xs:string($x/image[@size='large']/text()))""")
    albums = []
    tmp = dict()
    for album in query.iter():
        tmp['Name'] = album[1].split('_$!_')[0]
        tmp['Imagem'] = album[1].split('_$!_')[1]
        albums.append(tmp)
        tmp = dict()
    return render(request, 'albums.html', {'albums': albums, 'flist': flist})

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

    query5 = session.query("""for $a in collection('musicbox/artists.xml')//artists/artist/album[name=""" + "'" + album_name + "'""""]
                                return $a/artist/text()""")
    artist = ""
    for n in query5.iter():
        artist=n[1]

    return render(request, 'albuminfo.html', {'tracks':tracks, 'tags':tags, 'wiki':wiki, 'photo':photo, 'artist':artist, 'album_name':album_name})

def artist_page(request):
    session.execute("open musicbox")

    ###############################
    artist_name = request.GET['name']
    query1 = session.query(
        """for $b in collection('musicbox/artists.xml')//artists/artist[name=""" + "'" + artist_name + "'""""]/image[@size='extralarge'] return data($b/text())""")

    image = ""
    for img in query1.iter():
        image = img[1]

    ################################
    query2 = session.query("""for $c in collection('musicbox/artists.xml')//artist
                                  where $c/name=""" + "'" + artist_name + "'""""
                                  return (data($c/bio/summary))""")

    bio = ""
    for b in query2.iter():
        bio = b[1]

    ################################
    query3 = session.query("""(for $c in collection('musicbox/artists.xml')/lfm/artists//artist//album
                                  where $c/artist=""" + "'" + artist_name + "'""""
                                  order by $c/listeners
                                  return concat(xs:string($c/name/text()),'_$?_',xs:string($c/image[@size='large']/text())))[position() = 1 to 3]""")

    album = []
    tmp = dict()
    for a in query3.iter():
        tmp['name'] = a[1].split('_$?_')[0]
        tmp['imagem'] = a[1].split('_$?_')[1]
        album.append(tmp)
        tmp = dict()

    ################################
    query4 = session.query("""for $c in collection('musicbox/artists.xml')//artists//artist//album
                                  where $c/artist=""" + "'" + artist_name + "'""""
                                  return concat(xs:string($c/name/text()),'_$?_',xs:string($c/image[@size='large']/text()))""")
    list2 = []
    tmp2 = dict()

    for c in query4.iter():
        tmp2['name'] = c[1].split('_$?_')[0]
        tmp2['imagem'] = c[1].split('_$?_')[1]
        list2.append(tmp2)
        tmp2 = dict()

    return render(request, 'artist_page.html', {'image': image, 'bio': bio, 'album': album, 'lista': list2, 'name':artist_name})

def charts(request):

    session.execute("open musicbox")

    query1 = session.query("""(for $c in collection('musicbox/toptrack_portugal.xml')/lfm/tracks/track
                                order by $c/listeners
                                return concat(xs:string($c/name/text()), '_$?_', xs:string($c/artist/name/text()), '_$?_', xs:string($c/image[@size='large']/text())))[position() = 1 to 10]""")
    list1 = []
    tmp = dict()
    count = 0
    for c in query1.iter():
        count += 1
        tmp['name'] = c[1].split('_$?_')[0]
        tmp['artist'] = c[1].split('_$?_')[1]
        tmp['image'] = c[1].split('_$?_')[2]
        tmp['count'] = count
        list1.append(tmp)
        tmp = dict()

    #########################
    query2 = session.query("""(for $c in collection('musicbox/toptracks.xml')/lfm/tracks/track
                                order by $c/listeners
                                return concat(xs:string($c/name/text()), '_$?_', xs:string($c/artist/name/text()), '_$?_', xs:string($c/image[@size='large']/text())))[position() = 1 to 10]""")

    list2 = []
    tmp2 = dict()
    count2 = 0
    for d in query2.iter():
        count2 +=1
        tmp2['name'] = d[1].split('_$?_')[0]
        tmp2['artist'] = d[1].split('_$?_')[1]
        tmp2['image'] = d[1].split('_$?_')[2]
        tmp2['count'] = count2
        list2.append(tmp2)
        tmp2 = dict()

    return render(request, 'charts.html', {'list1' : list1, 'list2' :list2})

def login(request):
    return render(request, 'logIn.html')

def register(request):
    return render(request, 'register.html')