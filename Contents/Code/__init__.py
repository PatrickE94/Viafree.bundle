import urllib

TITLE = 'Viafree'
ART = 'art-default.png'
ICON = 'icon-default.png'

PREFIX = '/video/viafree'
PLAYCLIENT_URL = 'http://viafree.se/api/playClient'
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17'
ITEMS_PER_PAGE = 20

ART_SIZE = "1080x720"
SHOW_THUMB_SIZE = "200x300"
SEASON_THUMB_SIZE = "200x300"
EPISODE_THUMB_SIZE = "300x200"

##############################################
def Shows(oc, shows):
    for show in shows:
        oc.add(
            TVShowObject(
                key = Callback(ViafreeShowSeasons, show = show),
                rating_key = show["id"],
                title = unicode(show["title"]),
                summary = unicode(show["summary"]),
                thumb = show["image"].replace("{size}", SHOW_THUMB_SIZE),
                art = show["image"].replace("{size}", ART_SIZE)
            )
        )

    return oc

##############################################
def Start():
    Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = TITLE
    ObjectContainer.view_group = 'List'
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime = 300
    HTTP.Headers['User-agent'] = USER_AGENT

##############################################
@handler(PREFIX, TITLE, ICON, ART)
def MainMenu():
    oc = ObjectContainer(no_cache = True)
    ObjectContainer.art = R(ART)

    title = L('Categories')
    oc.add(
        DirectoryObject(
            key = Callback(ViafreeCategories, title = title),
            title = title
        )
    )

    title = L('All Programs')
    oc.add(
        DirectoryObject(
            key = Callback(ViafreeShows, title = title),
            title = title
        )
    )

    title = L('Search')
    oc.add(
        InputDirectoryObject(
            key = Callback(Search, title = title),
            title = title,
            prompt = title
        )
    )

    return oc

##############################################
@route(PREFIX + '/categories')
def ViafreeCategories(title):
    oc = ObjectContainer(title2 = unicode(title))

    categories = JSON.ObjectFromURL(PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=categories')

    for category in categories:
        oc.add(
            DirectoryObject(
                key = Callback(ViafreeShows, title = category["name"], category = category["id"]),
                title = unicode(category["name"])
            )
        )

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

##############################################
@route(PREFIX + '/shows', query = list)
def ViafreeShows(title, category = ''):
    oc = ObjectContainer(title2 = unicode(title))

    reqQuery = {}

    if category:
        reqQuery["category"] = category

    url = PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=formats;query='
    url = url + urllib.quote(JSON.StringFromObject(reqQuery))
    oc = Shows(oc, JSON.ObjectFromURL(url))

    if len(oc) < 1:
        oc.header = "Inga program funna"
        oc.message = unicode("Kunde ej få kontakt med server")

        return oc

    oc.objects.sort(key=lambda obj: obj.title)

    return oc

##############################################
@route(PREFIX + '/search', page = int)
def Search(query, title, page = 1):
    oc = ObjectContainer(title1="Viafree", title2=unicode(title + " '%s'" % query))

    reqQuery = {
        "term": query,
        "limit": 20,
        "columns": "formats",
        "page": page
    }
    url = PLAYCLIENT_URL + ';isColumn=true;resource=search;query='
    url = url + urllib.quote(JSON.StringFromObject(reqQuery))

    results = JSON.ObjectFromURL(url)
    if "formats" in results:
        Shows(oc, results["formats"])

    if len(oc) < 1:
        oc.header = "Inga program funna"
        oc.message = unicode("Inga resultat för '%s'" % query)

    elif len(oc) >= ITEMS_PER_PAGE:
        oc.add(
            NextPageObject(
                key =
                    Callback(
                        Search,
                        query = query,
                        title = title,
                        page = page + 1
                    ),
                title = "Ladda mera..."
            )
        )

    return oc


@route(PREFIX + '/seasons', show = list)
def ViafreeShowSeasons(show):
    oc = ObjectContainer(title2 = unicode(show["title"]))

    reqQuery = {"format": show["id"], "order": "-order"}
    seasons = JSON.ObjectFromURL(PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=seasons;query=' + urllib.quote(JSON.StringFromObject(reqQuery)))

    for season in seasons:
        oc.add(
            SeasonObject(
                key = Callback(ViafreeEpisodes, show = show, season = season),
                rating_key = season["id"],
                title = unicode(season["title"]),
                show = show["title"],
                index = season["seasonNumber"],
                summary = unicode(season["summary"]),
                art = season["image"].replace("{size}", ART_SIZE),
                thumb = season["image"].replace("{size}", SEASON_THUMB_SIZE)
            )
        )

    return oc

@route(PREFIX + '/episodes', season = list)
def ViafreeEpisodes(show, season):
    oc = ObjectContainer(title1=unicode(show["title"]), title2=unicode(season["title"]))

    reqQuery = {"season":season["id"],"type":"program"}
    url = PLAYCLIENT_URL + ';fetchAll=true;isList=true;resource=videos;query='
    url = url + urllib.quote(JSON.StringFromObject(reqQuery))
    episodes = JSON.ObjectFromURL(url)

    for episode in episodes:
        oc.add(
            EpisodeObject(
                url = PLAYCLIENT_URL + ";resource=videos/" + episode["id"],
                title = unicode(episode["title"]),
                summary = unicode(episode["summary"]),
                duration = episode["duration"] * 1000,
                index = episode["episodeNumber"],
                show = unicode(episode["formatTitle"]),
                art = episode["image"].replace("{size}", ART_SIZE),
                thumb = episode["image"].replace("{size}", EPISODE_THUMB_SIZE)
            )
        )

    oc.objects.sort(key=lambda obj: obj.index)

    return oc
