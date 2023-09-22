# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
# showEntries:    6 Stunden
# showSeasons:    6 Stunden
# showEpisodes:   4 Stunden
# Seite vollständig mit JSON erstellt

import json

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'cineclix'
SITE_NAME = 'CineClix'
SITE_ICON = 'cineclix.png'

# Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '.domain', 'cineclix.de')
URL_MAIN = 'https://' + DOMAIN + '/'
# URL_MAIN = 'https://cineclix.de/'
# Movie / Series / Search Links
URL_MOVIES = URL_MAIN + 'api/v1/channel/movies?channelType=channel&restriction=&paginate=simple'
URL_SERIES = URL_MAIN + 'api/v1/channel/series?channelType=channel&restriction=&paginate=simple'
URL_SEARCH = URL_MAIN + 'api/v1/search/%s?query=%s&limit=8'
# Hoster
URL_HOSTER = URL_MAIN + 'api/v1/titles/%s?load=images,genres,productionCountries,keywords,videos,primaryVideo,seasons,compactCredits'


def load():
    logger.info("Load %s" % SITE_NAME)
    params = ParameterHandler()
    params.setParam('page', (1))
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))  # Search
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    #import pydevd_pycharm
    #pydevd_pycharm.settrace('127.0.0.1', port=12345, stdoutToServer=True, stderrToServer=True)
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    # Parameter laden
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + '&page=' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('Referer', params.getValue('sUrl'))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request())  # Lade JSON aus dem Request der URL
    if not jSearch: return  # # Wenn Suche erfolglos - Abbruch
    aResults = jSearch['channel']['content']['data']
    total = len(aResults)
    if len(aResults) == 0:
        if not sGui: oGui.showInfo()
        return
    for i in aResults:
        sId = i['id']  # ID des Films / Serie für die weitere URL
        sName = i['name']  # Name des Films / Serie
        if 'is_series' in i: isTvshow = i['is_series']  # Wenn True dann Serie
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        if 'year' in i and len(str(i['year'])) == 4: oGuiElement.setYear(
            i['year'])  # Suche bei year nach 4 stelliger Zahl
        # sDesc = i['description']
        if 'description' in i and i['description'] != '': oGuiElement.setDescription(
            i['description'])  # Suche nach Desc wenn nicht leer dann setze GuiElement
        # sThumbnail = i['poster']
        if 'poster' in i and i['poster'] != '': oGuiElement.setThumbnail(
            i['poster'])  # Suche nach Desc wenn nicht leer dann setze GuiElement
        # sFanart = i['backdrop']
        if 'backdrop' in i and i['backdrop'] != '': oGuiElement.setFanart(
            i['backdrop'])  # Suche nach Desc wenn nicht leer dann setze GuiElement
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        # Parameter übergeben
        params.setParam('entryUrl', URL_HOSTER % sId)
        params.setParam('sThumbnail', i['poster'])
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('page', int(sPageNr))
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons(sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    oRequest = cRequestHandler(entryUrl)
    oRequest.addHeaderEntry('Referer', entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    jSearch = json.loads(oRequest.request()) # Lade JSON aus dem Request der URL
    if not jSearch: return # Wenn Suche erfolglos - Abbruch
    sDesc = jSearch['title']['description'] # Lade Beschreibung aus JSON
    aResults = jSearch['seasons']['data']
    aResults = sorted(aResults, key=lambda k: k['number'])  # Sortiert die Staffeln nach Nummer aufsteigend
    total = len(aResults)
    if len(aResults) == 0:
        if not sGui: oGui.showInfo()
        return
    for i in aResults:
        sId = i['title_id'] # ID ändert sich !!!
        sSeasonNr = str(i['number']) # Staffel Nummer
        oGuiElement = cGuiElement('Staffel ' + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        if sDesc != '': oGuiElement.setDescription(sDesc)
        params.setParam('sSeasonNr', sSeasonNr)
        params.setParam('sId', sId)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes(sGui=False):
    oGui = cGui()
    params = ParameterHandler()
    # Parameter laden
    sId = params.getValue('sId')
    sSeasonNr = params.getValue('sSeasonNr')
    #https://cineclix.de/api/v1/titles/2858/seasons/2?load=episodes,primaryVideo
    sUrl = URL_MAIN + 'api/v1/titles/%s/seasons/%s?load=episodes,primaryVideo' % (sId, sSeasonNr)
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # 4 Stunden
    jSearch = json.loads(oRequest.request()) # Lade JSON aus dem Request der URL
    if not jSearch: return # Wenn Suche erfolglos - Abbruch
    aResults = jSearch['episodes']['data'] # Ausgabe der Suchresultate von jSearch
    total = len(aResults) # Anzahl aller Ergebnisse
    if len(aResults) == 0:
        if not sGui: oGui.showInfo()
        return
    for i in aResults:
        sName = i['name'] # Episoden Titel
        sEpisodeNr = str(i['episode_number']) # Episoden Nummer
        sThumbnail = i['poster'] # Episoden Poster
        oGuiElement = cGuiElement('Episode ' + sEpisodeNr + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        if 'description' in i and i['description'] != '': oGuiElement.setDescription(i['description']) # Suche nach Desc wenn nicht leer dann setze GuiElement
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        # Parameter setzen
        #https://cineclix.de/api/v1/titles/2858/seasons/2/episodes/2?load=videos,compactCredits,primaryVideo
        params.setParam('entryUrl', URL_MAIN + 'api/v1/titles/%s/seasons/%s/episodes/%s?load=videos,compactCredits,primaryVideo' % (sId, sSeasonNr, sEpisodeNr))
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showSearchEntries(entryUrl=False, sGui=False, sSearchText=''):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    # Parameter laden
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('Referer', entryUrl)
    jSearch = json.loads(oRequest.request()) # Lade JSON aus dem Request der URL
    if not jSearch: return  # Wenn Suche erfolglos - Abbruch
    aResults = jSearch['results'] # Ausgabe der Suchresultate von jSearch
    total = len(aResults) # Anzahl aller Ergebnisse
    if len(aResults) == 0: # Wenn Resultate 0 zeige Benachrichtigung
        if not sGui: oGui.showInfo()
        return
    isTvshow = False
    for i in aResults:
        if 'person' in i['model_type']: continue # Personen in der Suche ausblenden
        sId = i['id']   # ID des Films / Serie für die weitere URL
        sName = i['name'] # Name des Films / Serie
        if sSearchText.lower() and not cParser().search(sSearchText, sName.lower()): continue
        if 'is_series' in i: isTvshow = i['is_series'] # Wenn True dann Serie
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        if 'year' in i and len(str(i['year'])) == 4: oGuiElement.setYear(i['year']) # Suche bei year nach 4 stelliger Zahl
        #sDesc = i['description']
        if 'description' in i and i['description'] != '': oGuiElement.setDescription(i['description']) # Suche nach Desc wenn nicht leer dann setze GuiElement
        # sThumbnail = i['poster']
        if 'poster' in i and i['poster'] != '': oGuiElement.setThumbnail(i['poster']) # Suche nach Desc wenn nicht leer dann setze GuiElement
        # sFanart = i['backdrop']
        if 'backdrop' in i and i['backdrop'] != '': oGuiElement.setFanart(i['backdrop']) # Suche nach Desc wenn nicht leer dann setze GuiElement
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        # Parameter setzen
        params.setParam('entryUrl', URL_HOSTER % sId)
        params.setParam('sThumbnail', i['poster'])
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showHosters(sGui=False):
    oGui = sGui if sGui else cGui()
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    oRequest.addHeaderEntry('Referer', sUrl)
    jSearch = json.loads(oRequest.request())  # Lade JSON aus dem Request der URL
    if not jSearch: return  # Wenn Suche erfolglos - Abbruch
    if ParameterHandler().getValue('mediaType') == 'movie': #Bei MediaTyp Filme nutze das Result
        aResults = jSearch['title']['videos'] # Ausgabe der Suchresultate von jSearch für Filme
    else:
        aResults = jSearch['episode']['videos'] # Ausgabe der Suchresultate von jSearch für Episoden
    # total = len(aResults)  # Anzahl aller Ergebnisse
    if len(aResults) == 0:
        if not sGui: oGui.showInfo()
        return
    for i in aResults:
        sName = i['name']
        sQuality = str(i['quality'])
        if sQuality != '': sQuality = '720p'
        sUrl = i['src']
        if cConfig().isBlockedHoster(sUrl)[0]: continue  # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
        if 'youtube' in sUrl: continue # Trailer ausblenden
        hoster = {'link': sUrl, 'name': sName, 'displayedName': '%s [I][%s][/I]' % (sName, sQuality), 'quality': sQuality, 'resolveable': True}
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    # https://cineclix.de/api/v1/search/Super%20Mario?query=Super+Mario&limit=8
    # Suche mit Quote und QuotePlus beim Suchtext
    sID1 = cParser().quote(sSearchText)
    sID2 = cParser().quotePlus(sSearchText)
    showSearchEntries(URL_SEARCH % (sID1, sID2), oGui, sSearchText)