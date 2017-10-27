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
    file = open("%s/%s.xml" % (os.path.dirname(os.path.abspath(__file__)) ,file_name), 'wb')
    file.write(contents)
    file.close()
    doc = xml.dom.minidom.parse("%s/%s.xml" % (os.path.dirname(os.path.abspath(__file__)), file_name))
    content = doc.toxml()

    schema = xmlschema.XMLSchema('%s/%s.xsd' % (os.path.dirname(os.path.abspath(__file__)), file_name))
    if(schema.is_valid('%s/%s.xml' % (os.path.dirname(os.path.abspath(__file__)), file_name))):
        print("%s.xml is a valid XML file." % file_name)
        session.add("%s.xml" % file_name, content)
    else:
        print("%s.xml is an invalid XML file." % file_name)
        sys.exit()

    os.remove("%s/%s.xml" % (os.path.dirname(os.path.abspath(__file__)), file_name))

def database():
    try:
        session.execute("open musicbox")
    except:
        print("Creating database")
        #create database
        session.execute("create db musicbox")

        #seed database
        doc = xml.dom.minidom.parse("%s/artists.xml" % os.path.dirname(os.path.abspath(__file__)))
        content = doc.toxml()
        schema = xmlschema.XMLSchema('%s/artists.xsd' % os.path.dirname(os.path.abspath(__file__)))

        if(schema.is_valid('%s/artists.xml' % os.path.dirname(os.path.abspath(__file__)))):
            print("artists.xml is a valid XML file.")
            session.add("artists.xml", content)
        else:
            print("artists.xml is an invalid XML file.")
            sys.exit()

        doc = xml.dom.minidom.parse("%s/Users.xml" % os.path.dirname(os.path.abspath(__file__)))
        content = doc.toxml()
        schema = xmlschema.XMLSchema('%s/Users.xsd' % os.path.dirname(os.path.abspath(__file__)))

        if (schema.is_valid('%s/Users.xml' % os.path.dirname(os.path.abspath(__file__)))):
            print("Users.xml is a valid XML file.")
            session.add("Users.xml", content)
        else:
            print("Users.xml is an invalid XML file.")
            sys.exit()


        #add xml with top current tracks
        get_top_tracks_url = "http://ws.audioscrobbler.com/2.0/?method=chart.gettoptracks&api_key=79004d202567282ea27ce27e9c26a498"
        parse_from_api(get_top_tracks_url, "toptracks")

        #add xml with top portugal tracks
        get_pt_top_tracks_url = "http://ws.audioscrobbler.com/2.0/?method=geo.gettoptracks&country=portugal&api_key=79004d202567282ea27ce27e9c26a498"
        parse_from_api(get_pt_top_tracks_url, "toptrack_portugal")

        session.execute("open musicbox")


def home(request):
    database()
    assert isinstance(request, HttpRequest)

    rss_url = "http://www.rollingstone.com/music/rss"
    s = urlopen(rss_url)
    contents = s.read()
    file = open("%s/rss.xml" % os.path.dirname(os.path.abspath(__file__)), 'wb')
    file.write(contents)
    file.close()

    rss_xml = ET.parse("%s/rss.xml" % os.path.dirname(os.path.abspath(__file__)))
    xslt = ET.parse("%s/rss.xslt" % os.path.dirname(os.path.abspath(__file__)))
    transform = ET.XSLT(xslt)
    new_rss_xml = transform(rss_xml)
    file = open("%s/new_rss.xml" % os.path.dirname(os.path.abspath(__file__)), 'wb')
    file.write(new_rss_xml)
    file.close()

    os.remove("%s/rss.xml" % os.path.dirname(os.path.abspath(__file__)))

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


    top_artist = session.query("""file:write("%s/result.xml", <root> {
                                    (for $b in collection('musicbox/artists.xml')//artists/artist
                                     order by xs:integer($b/listeners) descending
                                     return  <top> {$b/name, $b/listeners, $b/image[@size='large']}</top>)[position()=1 to 12]}</root>)""" % (os.path.dirname(
os.path.abspath(__file__))))
    top_artist.execute()
    top_artist_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    top_artists_root = top_artist_tree.getroot()
    top_artists_result = dict()
    top_artists_list = []

    count =0
    for elem in top_artists_root.iter('top'):
        top_artists_result['name'] = elem.find('name').text
        top_artists_result['image'] = elem.find('image').text
        top_artists_result['listeners'] = elem.find('listeners').text
        count +=1
        top_artists_result['count'] = count
        top_artists_list.append(top_artists_result)
        top_artists_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))

    return render(request, 'index.html', {'artists': top_artists_list, 'news': news_list})

def search_query(request):

    search = dict(request.POST)

    term = search.get('search_term')[0]

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
        return render(request, 'search.html', {'artists': artists_list})
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

    database()
    artists = session.query("""file:write("%s/result.xml", <root>{
                                     for $x in collection("musicbox/artists.xml")//artists/artist
                                      where starts-with($x/name, "%s")
                                      order by $x/name
                                      return <artists>{$x/name, $x/image[@size='large']}</artists>}</root>)""" % (os.path.dirname(
 os.path.abspath(__file__)), letter))
    artists.execute()

    artists_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    artists_root = artists_tree.getroot()
    artists_result = dict()
    artists_list = []

    for elem in artists_root.iter('artists'):
        artists_result['name'] = elem.find('name').text
        artists_result['image'] = elem.find('image').text
        artists_list.append(artists_result)
        artists_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    return render(request, 'artists.html', {'artists': artists_list, 'flist': flist})

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

    database()
    albums = session.query("""file:write("%s/result.xml", <root>{
                            for $x in collection("musicbox/artists.xml")//artists/artist/album
                                  where starts-with($x/name, "%s")
                                  order by $x/name
                                  return <album>{$x/name, $x/image[@size='large']}</album>}</root>)""" % (os.path.dirname(
 os.path.abspath(__file__)), letter))
    albums.execute()

    albums_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    albums_root = albums_tree.getroot()
    albums_result = dict()
    albums_list = []

    for elem in albums_root.iter('album'):
        albums_result['name'] = elem.find('name').text
        albums_result['image'] = elem.find('image').text
        albums_list.append(albums_result)
        albums_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    return render(request, 'albums.html', {'albums': albums_list, 'flist': flist})

def albuminfo(request):
    assert isinstance(request, HttpRequest)
    database()

    if request.POST:
        if 'faveBtn' in request.POST:
            name_album = request.POST['faveBtn']

            query6 = session.query("""insert node <fav data="%s" type="album">%s</fav>
                                    into fn:doc("musicbox/Users.xml")//user[email="simoreira@ua.pt"]/starred""" % (name_album, name_album))
            query6.execute()
        elif 'delBtn' in request.POST:
            album_delete = request.POST['delBtn']

            albumdel = session.query("""delete node fn:doc("musicbox/Users.xml")//user[email="simoreira@ua.pt"]/starred/fav[@data="%s"]""" % album_delete)
            albumdel.execute()
        else:
            pass

    album_name = request.GET['name']


    tracks = session.query("""file:write("%s/result.xml", <root>{
                                for $a in collection("musicbox/artists.xml")//artists/artist/album[name="%s"]/tracks/track
                                    return <tracks>{$a/name, $a/duration}</tracks>}</root>)""" % (os.path.dirname(
        os.path.abspath(__file__)), album_name))
    tracks.execute()

    tracks_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    tracks_root = tracks_tree.getroot()
    tracks_result = dict()
    tracks_list = []

    for elem in tracks_root.iter('tracks'):
        tracks_result['name'] = elem.find('name').text
        tracks_result['duration'] = elem.find('duration').text
        tracks_list.append(tracks_result)
        tracks_result = dict()

    tags = session.query("""file:write("%s/result2.xml", <root>{
                                for $a in collection("musicbox/artists.xml")//artists/artist/album
                                where $a/name="%s"
                                return <tag>{$a/tags/tag/name}</tag>}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), album_name))

    tags.execute()

    tags_tree = etree.parse('%s/result2.xml' % os.path.dirname(os.path.abspath(__file__)))
    tags_root = tags_tree.getroot()
    tags_result = ""

    for elem in tags_root.iter('tag'):
        tags_result = elem.find('name').text


    wiki = session.query("""file:write("%s/result3.xml", <root>{
                                for $a in collection("musicbox/artists.xml")//artists/artist/album
                                where $a/name="%s"
                                return <wiki>{$a/wiki/summary}</wiki>}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), album_name))

    wiki.execute()
    wiki_tree = etree.parse('%s/result3.xml' % os.path.dirname(os.path.abspath(__file__)))
    wiki_root = wiki_tree.getroot()
    wiki_result = ""

    for elem in wiki_root.iter('wiki'):
        wiki_result = elem.find('summary').text

    photo = session.query("""file:write("%s/result4.xml", <root>{
                            for $a in collection('musicbox/artists.xml')//artists/artist/album[name="%s"]/image[@size='extralarge']
                            return <photo>{$a}</photo>}</root>)""" % (os.path.dirname(
os.path.abspath(__file__)), album_name))

    photo.execute()
    photo_tree = etree.parse('%s/result4.xml' % os.path.dirname(os.path.abspath(__file__)))
    photo_root = photo_tree.getroot()
    photo_result = ""

    for elem in photo_root.iter('photo'):
        photo_result = elem.find('image').text

    artist = session.query("""file:write("%s/result5.xml", <root>{
                                for $a in collection('musicbox/artists.xml')//artists/artist/album[name="%s"]
                                return <artists>{$a/artist}</artists>}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), album_name))

    artist.execute()
    artist_tree = etree.parse('%s/result5.xml' % os.path.dirname(os.path.abspath(__file__)))
    artist_root = artist_tree.getroot()
    artist_result = ""

    for elem in artist_root.iter('artists'):
        artist_result = elem.find('artist').text

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result2.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result3.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result4.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result5.xml" % os.path.dirname(os.path.abspath(__file__)))

    return render(request, 'albuminfo.html', {'tracks':tracks_list, 'tags':tags_result, 'wiki':wiki_result, 'photo':photo_result, 'artist':artist_result, 'album_name':album_name})

def artist_page(request):
    database()

    if request.POST:
        if 'faveBtn' in request.POST:
            name_artist = request.POST['faveBtn']

            query6 = session.query("""insert node <fav data="%s" type="artist">%s</fav>
                                    into fn:doc("musicbox/Users.xml")//user[email="simoreira@ua.pt"]/starred""" % (name_artist, name_artist))
            query6.execute()
        elif 'delBtn' in request.POST:
            artist_delete = request.POST['delBtn']

            artistdel = session.query("""delete node fn:doc("musicbox/Users.xml")//user[email="simoreira@ua.pt"]/starred/fav[@data="%s"]""" % artist_delete)
            artistdel.execute()

        else:
            pass

    artist_name = request.GET['name']

    image = session.query("""file:write("%s/result.xml", <root>{
                                            for $b in collection('musicbox/artists.xml')//artists/artist[name="%s"]/image[@size='extralarge'] 
                                            return $b}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), artist_name))

    image.execute()
    image_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    image_root = image_tree.getroot()
    image_result = ""

    for elem in image_root.iter('image'):

        image_result = elem.text


    bio = session.query("""file:write("%s/result2.xml", <root>{
                                    for $c in collection('musicbox/artists.xml')//artist[name="%s"]
                                      return $c/bio/summary}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), artist_name))

    bio.execute()
    bio_tree = etree.parse('%s/result2.xml' % os.path.dirname(os.path.abspath(__file__)))
    bio_root = bio_tree.getroot()
    bio_result = ""

    for elem in bio_root.iter('summary'):
        bio_result = elem.text

    top_albums = session.query("""file:write("%s/result3.xml", <root>{
                            (for $c in collection('musicbox/artists.xml')/lfm/artists//artist//album
                                  where $c/artist="%s"
                                  order by $c/listeners
                                  return <topAlbum>{$c/name, $c/image[@size='large']}</topAlbum>)[position() = 1 to 3]}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), artist_name))


    top_albums.execute()

    top_albums_tree = etree.parse('%s/result3.xml' % os.path.dirname(os.path.abspath(__file__)))
    top_albums_root = top_albums_tree.getroot()
    top_albums_result = dict()
    top_albums_list = []

    for elem in top_albums_root.iter('topAlbum'):
        top_albums_result['name'] = elem.find('name').text
        top_albums_result['image'] = elem.find('image').text
        top_albums_list.append(top_albums_result)
        top_albums_result = dict()


    all_albums = session.query("""file:write("%s/result4.xml", <root>{
                                for $c in collection('musicbox/artists.xml')//artists//artist//album
                                  where $c/artist="%s"
                                  return <albums>{$c/name, $c/image[@size='large']}</albums>}</root>)""" % (os.path.dirname(
    os.path.abspath(__file__)), artist_name))

    all_albums.execute()

    all_albums_tree = etree.parse('%s/result4.xml' % os.path.dirname(os.path.abspath(__file__)))
    all_albums_root = all_albums_tree.getroot()
    all_albums_result = dict()
    all_albums_list = []

    for elem in all_albums_root.iter('albums'):
        all_albums_result['name'] = elem.find('name').text
        all_albums_result['image'] = elem.find('image').text
        all_albums_list.append(all_albums_result)
        all_albums_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result2.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result3.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result4.xml" % os.path.dirname(os.path.abspath(__file__)))

    return render(request, 'artist_page.html', {'image': image_result, 'bio': bio_result, 'album': top_albums_list, 'lista': all_albums_list, 'name':artist_name})

def charts(request):

    database()

    top_Portugal = session.query("""file:write("%s/result.xml", <root>{
                            (for $c in collection('musicbox/toptrack_portugal.xml')/lfm/tracks/track
                                order by $c/listeners
                                return <topPortugal>{$c/name, <artist>{$c/artist/name/text()}</artist>, $c/image[@size='large']}</topPortugal>)[position() = 1 to 10]}</root>)""" % os.path.dirname(
    os.path.abspath(__file__)))
    top_Portugal.execute()

    top_Portugal_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    top_Portugal_root = top_Portugal_tree.getroot()
    top_Portugal_result = dict()
    top_Portugal_list = []
    count = 0

    for elem in top_Portugal_root.iter('topPortugal'):
        count +=1
        top_Portugal_result['name'] = elem.find('name').text
        top_Portugal_result['artist'] = elem.find('artist').text
        top_Portugal_result['image'] = elem.find('image').text
        top_Portugal_result['count'] = count
        top_Portugal_list.append(top_Portugal_result)
        top_Portugal_result = dict()


    top_World = session.query("""file:write("%s/result2.xml", <root>{
                            (for $c in collection('musicbox/toptracks.xml')/lfm/tracks/track
                                order by $c/listeners
                                return <topWorld>{$c/name, <artist>{$c/artist/name/text()}</artist>, $c/image[@size='large']}</topWorld>)[position() = 1 to 10]}</root>)""" % os.path.dirname(
    os.path.abspath(__file__)))

    top_World.execute()

    top_World_tree = etree.parse('%s/result2.xml' % os.path.dirname(os.path.abspath(__file__)))
    top_World_root = top_World_tree.getroot()
    top_World_result = dict()
    top_World_list = []
    count2 = 0

    for elem in top_World_root.iter('topWorld'):
        count2 += 1
        top_World_result['name'] = elem.find('name').text
        top_World_result['artist'] = elem.find('artist').text
        top_World_result['image'] = elem.find('image').text
        top_World_result['count'] = count2
        top_World_list.append(top_World_result)
        top_World_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result2.xml" % os.path.dirname(os.path.abspath(__file__)))


    return render(request, 'charts.html', {'topPortugal' : top_Portugal_list, 'topWorld' :top_World_list})

def login(request):
    return render(request, 'logIn.html')

def register(request):
    return render(request, 'register.html')

def profile(request):
    if request.POST:
        #query
        print("POST FORM")

    database()
    #search users
    person = session.query("""file:write("%s/result.xml", <root>{
                                for $c in collection('musicbox/Users.xml')//users/user
                                return
                                    if ($c/@login="True") then
                                        <person>{$c/name, $c/email}</person>
                                    else
                                        break
                                }</root>)""" % os.path.dirname( os.path.abspath(__file__)))

    person.execute()
    person_tree = etree.parse('%s/result.xml' % os.path.dirname(os.path.abspath(__file__)))
    person_root = person_tree.getroot()
    person_name = ""
    person_email = ""

    for elem in person_root.iter('person'):
        person_name = elem.find('name').text
        person_email = elem.find('email').text

    artist = session.query("""file:write("%s/result2.xml", <root>{
                                for $c in collection('musicbox/Users.xml')//users/user
                                return
                                if ($c/@login="True") then
                                    <artist>{$c/starred/fav[@type="artist"]}</artist>
                                else
                                    break
                                }</root>)""" % os.path.dirname( os.path.abspath(__file__)))

    artist.execute()
    artist_tree = etree.parse('%s/result2.xml' % os.path.dirname(os.path.abspath(__file__)))
    artist_root = artist_tree.getroot()
    artist_list = []
    artist_result = dict()
    tmp = []

    for elem in artist_root.iter('artist'):
        if elem.find('fav') == None:
            pass
        else:
            tmp = elem.findall('fav')
            for z in tmp:
                artist_result['artist'] = z.get('data')
                artist_list.append(artist_result)
                artist_result = dict()


    album = session.query("""file:write("%s/result3.xml", <root>{
                                for $c in collection('musicbox/Users.xml')//users/user
                                return
                                if ($c/@login="True") then
                                    <album>{$c/starred/fav[@type="album"]}</album>
                                else
                                    break
                                }</root>)""" % os.path.dirname( os.path.abspath(__file__)))

    album.execute()
    album_tree = etree.parse('%s/result3.xml' % os.path.dirname(os.path.abspath(__file__)))
    album_root = album_tree.getroot()
    album_list = []
    tmp2 = []
    album_result = dict()

    for elem in album_root.iter('album'):
        if elem.find('fav') == None:
            pass
        else:
            tmp2 = elem.findall('fav')
            for z in tmp2:
                album_result['album'] = z.get('data')
                album_list.append(album_result)
                album_result = dict()

    os.remove("%s/result.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result2.xml" % os.path.dirname(os.path.abspath(__file__)))
    os.remove("%s/result3.xml" % os.path.dirname(os.path.abspath(__file__)))


    return render(request, 'profile.html', {'name' : person_name, 'email': person_email, 'artists': artist_list, 'albums': album_list})
