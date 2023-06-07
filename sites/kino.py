# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showGenre:     48 Stunden
    #showEntries:    6 Stunden
    #showEpisodes:   4 Stunden
    
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'kino'
SITE_NAME = 'Kino'
SITE_ICON = 'kino_ws.png'

#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'kino.ws')
URL_MAIN = 'https://' + DOMAIN + '/'
#URL_MAIN = 'https://kino.ws/'
URL_MOVIES = URL_MAIN + 'filme-kostenlos.html'
URL_SERIES = URL_MAIN + 'serien-kostenlos.html'
URL_SEARCH = URL_MAIN + 'recherche?_token=kZDYEMkRbBXOKMQbZZOnGOaR9JMeGAjXpzKtj0s3&q=%s'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()  
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies
    params.addParams({'sSubmenu': 'films', 'sUrl': URL_MAIN})
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506) + ' - ' + cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showGenre'), params)  # Genre
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series 
    params.addParams({'sSubmenu': 'Séries','sUrl': URL_MAIN})
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506) +' - '+ cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showGenre'), params)    # Genre
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))   # Search
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sSubmenu = params.getValue('sSubmenu')
    oRequest = cRequestHandler(sUrl)
    oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'title="%s.*?</ul></div></li>' % sSubmenu
    isMatch, sResult = cParser.parseSingleResult(sHtmlContent, pattern)
    pattern = 'href="([^"]+).*?>([^<]+)'
    isMatch, aResult = cParser.parse(sResult, pattern)

    for sUrl, sName in aResult:
        if sUrl.startswith('/'):
            sUrl = URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'class="short-in.*?'  # container start
    pattern += 'nl">(.*?)a\s+class.*?'  # dummy
    pattern += 'href="(http[^"]+).*?'  # url
    pattern += 'src="([^"]+).*?'  # thumbnail
    pattern += 'alt(.*?)' # info dummy
    pattern += 'short-title">([^<]+)'  # name
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    isTvshow = None
    for sDummy, sUrl, sThumbnail, sInfo, sName in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isQuality, sQuality = cParser.parseSingleResult(sDummy, 'film-ripz.*?#">([^<]+)')  # Qualität
        isInfoEpisode, sInfoEpisode = cParser.parseSingleResult(sInfo, 'mli-eps">.*?<i>([\d]+)')  # Episodenanzahl
        isTvshow, aResult = cParser.parse(sName, '\s+-\s+Staffel\s+\d+')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        if isQuality:
            oGuiElement.setQuality(sQuality)
        if isInfoEpisode:
            oGuiElement.setInfo(sInfoEpisode + ' Episoden')
        oGuiElement.setMediaType('season' if isTvshow else 'movie')
        params.setParam('entryUrl', sUrl)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui and not sSearchText:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'class="pnext">.*?<a href="([^"]+)')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # 4 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'id="episode(\d+)' # d fügt Anzahl der Episoden hinzu
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 's-desc">([^<]+)')  # Beschreibung
    total = len(aResult)
    for sName in aResult:
        oGuiElement = cGuiElement('Episode ' + sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        oGuiElement.setMediaType('episode')
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', entryUrl)
        params.setParam('sEpisode', sName)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sMediaType = params.getValue('mediaType')
    sHtmlContent = cRequestHandler(sUrl).request()
    if sMediaType == 'episode':
        sEpisode = params.getValue('sEpisode')
        pattern = 'id="episode%s.*?style' % sEpisode        # Episoden Bereich
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    else:
        pattern = '<div class="tabs-sel">.*?</div>'         # Filme
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    pattern = 'href="([^"]+).*?seriePlayer.*?</i>([^<]+)'
    isMatch, aResult = cParser.parse(aResult[0], pattern)   # Nimmt nur das 1.Result
    for sUrl, sName in aResult:
        if cConfig().isBlockedHoster(sUrl)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
        hoster = {'link': sUrl, 'name': sName}
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
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)