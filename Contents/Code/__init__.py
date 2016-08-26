PLAYCLIENT_URL = 'http://viafree.se/api/playClient'
ITEMS_PER_PAGE = 20

def Shows(oc, shows):
    for show in shows:
        oc.add(
            TVShowObject(
                key = Callback(ViafreeShowSeasons, show = show),
                rating_key = show["id"],
                title = unicode(show["title"]),
                summary = unicode(show["summary"]),
                thumb = show["image"].replace("{size}", "200x300"),
                art = show["image"].replace("{size}", "1080x720")
            )
        )

    return oc

def GetShowsURL(page, category = '', query = ''):

    reqQuery = {}

    if category:
        reqQuery["category"] = category

    if query:
        reqQuery["term"] = query

    Log(PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=formats;query=%s' % (JSON.StringFromObject(reqQuery)))
    return PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=formats;query=%s' % (JSON.StringFromObject(reqQuery))


##############################################3

def Start():
    ObjectContainer.title1 = 'Viafree'

    HTTP.CacheTime = 300
    HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'

@handler('/video/viafree', 'Viafree')
def MainMenu():
    oc = ObjectContainer(no_cache = True)

    title = 'Kategorier'
    oc.add(
        DirectoryObject(
            key = Callback(ViafreeCategories, title = title),
            title = title
        )
    )

    title = 'Alla program'
    oc.add(
        DirectoryObject(
            key = Callback(ViafreeShows, title = title),
            title = title
        )
    )

    title = unicode('Sök')
    oc.add(
        InputDirectoryObject(
            key = Callback(Search, title = title),
            title = title,
            prompt = title
        )
    )

    return oc

@route('/video/viafree/categories')
def ViafreeCategories(title):
    oc = ObjectContainer(title2 = unicode(title))

    categories = JSON.ObjectFromURL(PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=categories')

    for category in categories:
        oc.add(
            DirectoryObject(
                key = Callback(ViafreeShows, title = category["name"], categoryId = unicode(category["id"])),
                title = unicode(category["name"])
            )
        )

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

@route('/video/viafree/shows', query = list, page = int)
def ViafreeShows(title, categoryId = '', query = '', page = 1):
    oc = ObjectContainer(title2 = unicode(title))

    shows = JSON.ObjectFromURL(GetShowsURL(page, categoryId, query))
    oc = Shows(oc, shows)

    if len(oc) < 1:
        oc.header = "Inga program funna"
        oc.message = unicode("Kunde ej få kontakt med server")

        return oc

    elif len(oc) >= ITEMS_PER_PAGE:
        oc.add(
            NextPageObject(
                key =
                    Callback(
                        ViafreeShows,
                        title = title,
                        categoryId = categoryId,
                        query = query,
                        page = page + 1
                    ),
                title = "Ladda mera..."
            )
        )

    return oc

@route('/video/viafree/search')
def Search(query, title):
    oc = ObjectContainer(title1="Viafree", title2=unicode(title + " '%s'" % query))

    reqQuery = {
        "term": query,
        "limit": 20,
        "columns": "formats",
        "with": "format"
    }

    results = JSON.ObjectFromURL(PLAYCLIENT_URL + ';isColumn=true;resource=search;query=%s' % (JSON.StringFromObject(reqQuery)))
    if "formats" in results:
        Shows(oc, results["formats"])

### TODO Pagination

    return oc


@route('/video/viafree/seasons', show = list)
def ViafreeShowSeasons(show):
    Log(show)
    oc = ObjectContainer(title2 = unicode(show["title"]))

    reqQuery = {"format": show["id"], "order": "-order"}
    seasons = JSON.ObjectFromURL(PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=seasons;query=%s' % (JSON.StringFromObject(reqQuery)))

    for season in seasons:
        oc.add(
            SeasonObject(
                key = Callback(ViafreeEpisodes, show = show, season = season),
                rating_key = season["id"],
                title = unicode(season["title"]),
                show = show["title"],
                index = season["seasonNumber"],
                summary = unicode(season["summary"]),
                art = show["image"].replace("{size}", "1080x720"),
                thumb = season["image"].replace("{size}", "200x300")
            )
        )

    return oc

@route('/video/viafree/episodes', season = list)
def ViafreeEpisodes(show, season):
    oc = ObjectContainer(title1=unicode(show["title"]), title2=unicode(season["title"]))

    reqQuery = {"season":season["id"],"type":"program"}
    episodes = JSON.ObjectFromURL(PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=videos;query=%s' % (JSON.StringFromObject(reqQuery)))

    for episode in episodes:
        oc.add(
            EpisodeObject(
                url = PLAYCLIENT_URL + ";resource=videos/" + episode["id"],
                title = unicode(episode["title"]),
                summary = unicode(episode["summary"]),
                duration = episode["duration"] * 1000,
                index = episode["episodeNumber"],
                show = unicode(episode["formatTitle"]),
                art = episode["image"].replace("{size}", "1080x720"),
                thumb = episode["image"].replace("{size}", "300x200")
            )
        )

    return oc
