# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'movie4k_space'
SITE_NAME = 'Movie4k Space'
SITE_ICON = 'movie4k_space.png'
SITE_GLOBAL_SEARCH = False
URL_MAIN = 'https://movie4k.space'
URL_FILME = URL_MAIN + '/filme'
URL_SEARCH = URL_MAIN + '/search/?search=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    pattern = '<div class="group-film-small">.*? </div>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'href="([^"]+)"[^>]title="([^"]+).*?src="([^"]+)'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail in aResult:
        sThumbnail = URL_MAIN + sThumbnail
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('movie')
        params.setParam('entryUrl', URL_MAIN + sUrl)
        oGui.addFolder(oGuiElement, params, False, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, 'class="active"><strong>.*?href="([^"]+)')
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
        oRequest = cRequestHandler(sUrl, caching=False)
        oRequest.request()
        sUrl = oRequest.getRealUrl()
        oRequest = cRequestHandler(sUrl)
        sHtmlContent = oRequest.request()
        pattern = 'var file = "([^"]+)"'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
        if isMatch:
            for sUrl in aResult:
                try:
                    base = cParser.B64decode(cParser.replace('//(.*?)=', '', sUrl[2:]))
                    hoster = {'link': base, 'name': base}
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
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)
