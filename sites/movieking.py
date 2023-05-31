# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showGenre:     48 Stunden
    #showEntries:    6 Stunden

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'movieking'
SITE_NAME = 'MovieKing'
SITE_ICON = 'movieking.png'

#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'movieking.io')
URL_MAIN = 'https://' + DOMAIN + '/'
#URL_MAIN = 'https://movieking.io/'
URL_KINO = URL_MAIN + 'cinema'
URL_MOVIES = URL_MAIN + 'movies.html'
URL_YEAR = URL_MAIN + 'year.html'
URL_SEARCH = URL_MAIN + 'search?q=%s'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_KINO)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30501), SITE_IDENTIFIER, 'showEntries'), params)  # Current films in the cinema     
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies
    params.setParam('sUrl', URL_YEAR)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30508), SITE_IDENTIFIER, 'showGenre'), params)    # Release Year
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'), params)    # Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))   # Search
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48 # 48 Stunden
    sHtmlContent = oRequest.request()      
    if 'year' in entryUrl:
        pattern = 'section-opt.*?id="footer">'
        isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    else:
        pattern = '>Genre.*?.*?class="dropdown">'
        isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'href="([^"]+)">([^<]+)'
        isMatch, aResult = cParser.parse(sHtmlContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
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
    pattern = '<div class="latest-.*?'  # container start
    pattern += 'data-src="([^"]+).*?' # Thumb
    pattern += 'class="video_quality">(.*?)<h3>.*?'  # dummy
    pattern += 'href="([^"]+)">([^<]+).*?'  # url + name

    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sThumbnail, sDummy, sUrl, sName in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        isQuality, sQuality = cParser.parseSingleResult(sDummy, 'label-primary">([^"]+)\s</span>')  # Qualität

        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        if isQuality:
            if 'PISODES' in sQuality:
                continue
            oGuiElement.setQuality(sQuality)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', sUrl)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'pagination.*?<a href="([^"]+)" data-ci-pagination-page="\d" rel="next">')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<a href="([^"]+)"\sclass="btn movie-player.*?>([^<]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        for sUrl, sName in aResult:
            if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
            hoster = {'link': sUrl, 'name': sName }
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    Request = cRequestHandler(sUrl, caching=False)
    sHtmlContent = Request.request()
    pattern = 'embed-item".*?src="(http[^"]+)'
    isMatch, sUrl = cParser.parseSingleResult(sHtmlContent, pattern)
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)
