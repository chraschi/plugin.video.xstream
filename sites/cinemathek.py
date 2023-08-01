# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showGenre:     48 Stunden
    #showEntries:    6 Stunden
    #showSeasons:    6 Stunden
    #showEpisodes:   4 Stunden
    
import json

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'cinemathek'
SITE_NAME = 'Cinemathek'
SITE_ICON = 'cinemathek.png'

# Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'cinemathek.net')
URL_MAIN = 'https://' + DOMAIN + '/'
#URL_MAIN = 'https://cinemathek.net/'
URL_MOVIES = URL_MAIN + 'filme/'
URL_SERIES = URL_MAIN + 'serien/'
URL_NEW_EPISODES = URL_MAIN + 'episoden/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies  
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    params.setParam('sUrl', URL_NEW_EPISODES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30516), SITE_IDENTIFIER, 'showNewEpisodes'), params)  # New Episodes
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'), params)    # Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30527), SITE_IDENTIFIER, 'showRegs'), params)     # Regisseure
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))           # Search
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<ul class="sub-menu"><li id="menu-item-23517".*?</ul>' # Alle Einträge in dem Bereich suchen
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)') # sUrl + sName
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showRegs():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<ul class="sub-menu"><li id="menu-item-26052".*?</ul>' # Alle Einträge in dem Bereich suchen
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)') # sUrl + sName
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    isTvshow = False    
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=sGui is not False)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    # Für Filme und Serien Content
    pattern = '<article id=.*?'  # container start
    pattern += 'src="([^"]+).*?'  # sThumbnail
    pattern += 'href="([^"]+).*?'  # url  
    pattern += '>([^<]+).*?'  # name 
    pattern += '(.*?)</article>'  # dummy
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        # Für die Suche von Filmen und Serien
        pattern = '<article.*?'  # container start
        pattern += '<img src="([^"]+).*?'  # sThumbnail alt
        pattern += 'href="([^"]+).*?'  # url
        pattern += '>([^<]+).*?'  # name
        pattern += '(.*?)</article>'  # dummy
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    total = len(aResult)
    for sThumbnail, sUrl, sName, sDummy in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isTvshow, aResult = cParser.parse(sUrl, 'serien') # Muss nur im Serien Content auffindbar sein
        isDesc, sDesc = cParser.parseSingleResult(sDummy, '<div class="texto">([^<]+)') # Beschreibung
        if not isDesc:
            isDesc, sDesc = cParser.parseSingleResult(sDummy, 'class="contenido"><p>([^<]+)\s') # Beschreibung in der Suche

        isYear, sYear = cParser.parseSingleResult(sDummy, 'class="imdb">\S+.*?\S+.*?<span>([\d]+)') # Release Jahr
        if not isYear:
            isYear, sYear = cParser.parseSingleResult(sDummy, 'class="year">([\d]+)') # Release Jahr in der Suche
        if not isYear:
            isYear, sYear = cParser.parseSingleResult(sDummy, 'metadata"> <span>([\d]+)') # Release Jahr

        isDuration, sDuration = cParser.parseSingleResult(sDummy, '<span>([\d]+)\smin')  # Laufzeit

        isRating, sRating = cParser.parseSingleResult(sDummy, 'IMDb:([^<]+)') # IMDb Bewertung
        if not isRating:
            isRating, sRating = cParser.parseSingleResult(sDummy, 'IMDb\s([^<]+)')# IMDb Bewertung in der Suche
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if isYear:
            oGuiElement.setYear(sYear)
        if isTvshow is False: # Laufzeit bei Serie ausblenden
            if isDuration:
                oGuiElement.addItemValue('duration', sDuration)
        if isRating:
            oGuiElement.addItemValue('rating', sRating)
        # Parameter übergeben
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sDesc', sDesc)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui and not sSearchText:

        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<link[^>]*rel="next"[^>]*href="([^"]+)"') # Nächste Seite
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showNewEpisodes(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=sGui is not False)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    # Für die Suche von Neuen Episoden
    pattern = '<article.*?'  # container start
    pattern += '<img src="([^"]+).*?'  # sThumbnail alt
    pattern += 'href="([^"]+).*?'  # url
    pattern += '>([^<]+).*?'  # name
    pattern += '</h3><span>S([\d]+)'  # Staffel Nummer
    pattern += '\sE([\d]+)'  # Episoden Nummer
    pattern += '(.*?)</article>'  # dummy
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)  # neue Episoden

    total = len(aResult)
    for sThumbnail, sUrl, sName, sSeason, sEpisode, sDummy in aResult:
        isEpisode, aResult = cParser.parse(sUrl, 'episoden') # Im Episoden Content auffindbar
        isTVShowTitle, sTVShowTitle = cParser.parseSingleResult(sDummy, 'class="serie">([^<]+)')  # Serien Titel
        isYear, sYear = cParser.parseSingleResult(sDummy, '([\d]+)</span>\s<span class="serie') # Release Jahr
        if isEpisode is True:
            oGuiElement = cGuiElement('Staffel ' + sSeason + ' Episode '+ sEpisode + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        else:
            continue
        oGuiElement.setThumbnail(sThumbnail)
        if isTVShowTitle:
            oGuiElement.setTVShowTitle(sTVShowTitle)
        if isYear:
            oGuiElement.setYear(sYear)
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        # Parameter übergeben
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        cGui().addFolder(oGuiElement, params, False, total)

    if not sGui and not sSearchText:

        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, '<link[^>]*rel="next"[^>]*href="([^"]+)"') # Nächste Seite
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showNewEpisodes', params)
        cGui().setView('episodes')
        cGui().setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sDesc = params.getValue('sDesc')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    isMatch, aResult = cParser.parse(sHtmlContent, 'Season ([\d]+)') # Sucht den Staffel Eintrag und d fügt die Anzahl hinzu
    if not isMatch:
        cGui().showInfo()
        return

    total = len(aResult)
    for sSeason in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
        # Parameter übergeben
        params.setParam('Season', sSeason)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sSeason = params.getValue('Season')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
    sHtmlContent = oRequest.request()
    pattern = '>Season %s <i>.*?</ul>' % sSeason # Suche alles in diesem Bereich
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = "mark-([\d]+).*?" # Episoden Eintrag
        pattern += "img src='([^']+).*?" # sThumbnail
        pattern += "<a href='([^']+).*?" # sUrl
        pattern += ">([^<]+)</a>" # sName
        isMatch, aResult = cParser.parse(sContainer, pattern)

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'class="wp-content">(.*?)</p>')  # Beschreibung
    total = len(aResult)
    for sEpisode, sThumbnail, sUrl, sName in aResult:
        oGuiElement = cGuiElement('Episode ' + sEpisode + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        # Parameter übergeben
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    # <li id="player-option-1" class="dooplay_player_option" data-type="movie" data-post="29224" data-nume="1">
    pattern = "player-option-\d.*?" # Player Option Nr. z.B 1 für Link 1
    pattern += "type='([^']+).*?" # Eintrag [0] movie oder tv
    pattern += "post='(\d+).*?" # Eintrag [1] ist die Film oder Serien Nr.29224
    pattern += "nume='(\d).*?" # Eintrag [2] ist die Link Nr.1
    pattern += "starten!\s([^<]+)" # Eintrag [3] = sName des Link Eintrag
    releaseQuality = ">Release:.*?\s*(\d\d\d+)p"  # Hoster Release Quality Kennzeichen
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    isQuality, sQuality = cParser.parseSingleResult(sHtmlContent, releaseQuality)  # sReleaseQuality auslesen z.B. 1080
    if not isQuality: sQuality = '720'
    if isMatch:
        for sType, sID, sLink, sName in aResult:
            sUrl = 'https://cinemathek.net/wp-json/dooplayer/v2/%s/%s/%s' % (sID, sType, sLink)
            if cConfig().isBlockedHoster(sName)[0]: continue  # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
            hoster = {'link': sUrl, 'name': sName, 'displayedName': '%s [I][%sp][/I]' % (sName, sQuality), 'quality': sQuality} # Qualität Anzeige aus Release Eintrag
            hosters.append(hoster)
    if not isMatch:
        cGui().showInfo()
        return

    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    sUrl = json.loads(cRequestHandler(sUrl).request()).get("embed_url")
    # Überprüfe sUrl auf korrekte Domain
    Request = cRequestHandler(sUrl, caching=False)
    Request.request()
    sUrl = Request.getRealUrl() # hole reale sURL
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)
