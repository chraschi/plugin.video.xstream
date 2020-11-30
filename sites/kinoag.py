# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'kinoag'
SITE_NAME = 'Kino AG'
SITE_ICON = 'kinoag.png'
URL_MAIN = 'https://kino.ag'
URL_FILME = URL_MAIN + '/filme/'
URL_SEARCH = URL_MAIN + '/search/?search=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'Genre'), params)
    cGui().addFolder(cGuiElement('Jahr', SITE_IDENTIFIER, 'Year'))
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), params)
    cGui().setEndOfDirectory()


def Genre():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_FILME).request()
    pattern = 'class="descendant".*?href="([^"]+)">([^<]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        if 'filme' in sUrl and not 'year' in sUrl:
            params.setParam('sUrl', URL_MAIN + sUrl)
            cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def Year():
    params = ParameterHandler()
    import datetime
    List = list(range(1970, datetime.datetime.now().year + 1))
    for y in List[::-1]:
        params.setParam('sUrl', URL_MAIN + '/y/' + str(y))
        cGui().addFolder(cGuiElement(str(y), SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    pattern = 'class="lazy" data-src="([^"]+).*?href="([^"]+).*?link_title">([^<]+).*?links2">(\d{4}),'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sThumbnail, sUrl, sName, sYear in aResult:
        sThumbnail = URL_MAIN + sThumbnail
        if 'serial' in sUrl:
            continue
        if sSearchText and not cParser.search(sSearchText, sName):
            continue
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setYear(sYear)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, 'class="pagination.*?</strong>[^>]*<a[^>]href="([^"]+)')
        if isMatchNextPage:
            params.setParam('sUrl', URL_MAIN + sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('movies')
        oGui.setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, sUrl = cParser.parseSingleResult(sHtmlContent, 'iplayer[^>]*src="([^"]+)')
    if isMatch:
        oRequest = cRequestHandler(sUrl)
        sHtmlContent = oRequest.request()
        pattern = 'var file = "([^"]+)"'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if isMatch:
            for sUrl in aResult:
                try:
                    base = cParser.B64decode(cParser.replace('//(.*?)=', '', sUrl[2:]))
                    hoster = {'link': base, 'name': cParser.urlparse(base)}
                    hosters.append(hoster)
                except:
                    pass
        if hosters:
            hosters.append('getHosterUrl')
        return hosters


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': True}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)
