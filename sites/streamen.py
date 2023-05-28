# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showGenre:     48 Stunden
    #showEntries     6 Stunden
    #showSeasons:   24 Stunden
    #showEpisodes:   4 Stunden

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser, cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'streamen'
SITE_NAME = 'Streamen'
SITE_ICON = 'streamen.png'

#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'wwv.streamen.cx')
URL_MAIN = 'https://' + DOMAIN
URL_MOVIES = URL_MAIN + '/filme.html'
URL_SERIES = URL_MAIN + '/serien.html'
URL_SEARCH = URL_MAIN + '/recherche?q=%s'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)    # Movies
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'), params)    # Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))   # Search
    cGui().setEndOfDirectory()


def showGenre(entryUrl=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()    
    pattern = '<ul id="sub-menu".*?</ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sHtmlContainer, 'href="([^"]+).*?>([^<]+)')
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
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<div[^>]*class="short-images[^"]*"[^>]*>.*?'  # start element
    pattern += '<a[^>]*href="([^"]*)"[^>]*>.*?'  # url
    pattern += '<img[^>]*src="([^"]*)".*?'  # thumbnail
    pattern += 'alt="([^"]*).*?'  # name
    pattern += '<\/div>'  # end element
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        isTvshow = True if 'serien' in sUrl else False # Wenn Serie dann True
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        # Parameter setzen und nachfolgende Parameter in die nächste Def übergeben
        params.setParam('entryUrl', sUrl) # Film bzw. Serien URL
        params.setParam('sThumbnail', sThumbnail) # Film bzw. Serien Thumb
        params.setParam('sName', sName) # Film bzw. Serien Name
        oGui.addFolder(oGuiElement, params, isTvshow, total)
        
    if not sGui and not sSearchText:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'pages-next">.*?href="([^"]+)')
        if isMatchNextPage:
            sNextUrl = URL_MAIN + sNextUrl
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 24 # HTML Cache Zeit 1 Tag
    sHtmlContent = oRequest.request()
    isMatch, aResult = cParser.parse(sHtmlContent, '<div[^>]*class="short-images[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*src="([^"]*)".*?<figcaption>Staffel\s([\d]+)') # Sucht den Staffel Eintrag und d fügt die Anzahl hinzu
    if not isMatch:
        cGui().showInfo()
        return
    
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'fsynopsis">\s<p>\s([^"]*)</p>') # Staffel Beschreibung
    total = len(aResult)
    for sUrl, sThumbnail, sSeason in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setSeason(sSeason)
        if isDesc:
            sDesc = sDesc.replace('&quot;', '"')
            oGuiElement.setDescription(sDesc)
        # Parameter setzen und nachfolgende Parameter in die nächste Def übergeben
        params.setParam('sDesc', sDesc) # Staffel Beschreibung
        params.setParam('sThumbnail', sThumbnail) # Staffel Thumb
        params.setParam('Season', sSeason) # Staffel Nr.
        params.setParam('entryUrl', sUrl)   # Staffel URL
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sSeason = params.getValue('Season')
    sThumbnail = params.getValue('sThumbnail')
    sDesc = params.getValue('sDesc')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
    sHtmlContent = oRequest.request()
    isMatch, aResult = cParser.parse(sHtmlContent, '_LI2">.*?href="([^"]+).*?Folge\s([\d]+)</span>')
    if not isMatch:
        cGui().showInfo()
        return

    total = len(aResult)
    for sUrl, sEpisode in aResult:
        oGuiElement = cGuiElement('Episode ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div data-url="([^"]+).*?player_v_DIV_5">([^<]*)\s' # sUrl, sName
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        for sUrl, sName in aResult:
            if 'ayer' in sName:
                continue
            if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
            elif sUrl.startswith('/'):
                sUrl = URL_MAIN + sUrl # URL_MAIN + übergebener Link
            hoster = {'link': sUrl, 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    if not hosters:
        cGui().showInfo()  # Setzen damit fehlerhafte Hoster angezeigt werden!
    return hosters


def getHosterUrl(sUrl=False):
    Request = cRequestHandler(sUrl, caching=False)
    Request.request()
    sUrl = Request.getRealUrl() # hole reale URL von der Umleitung
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)
