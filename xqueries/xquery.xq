(:lIST ALBUNS:)
(:for $x in collection("musicbox/artists.xml")//artists/artist/album
where starts-with($x/name, "Z")
order by $x/name
return <result>{$x/name}</result> :)

(:LIST ARTISTS:)

(:LIST :)
(:
for $x in collection("musicbox/artists.xml")//artists/artist[starts-with(name, 'A')]
order by $x/name
return <result>{$x/name}</result>
:)

(:LIST ALBUNS INFO:)

(:
for $x in collection("musicbox/artists.xml")//artists/artist/album
where contains($x/name, "Rated R")
return $x
:)
<root> {
for $x in collection("musicbox/artists.xml")//artists/artist/name,
    $y in collection("musicbox/artists.xml")//artists/artist/album/name
where (contains($x, "Radiohead") or contains($y, "Radiohead"))
return <artist>{$x}</artist>, <album>{$y}</album>
}</root> 

