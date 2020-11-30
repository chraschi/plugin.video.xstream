# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'alleserien_com'
SITE_NAME = 'Alleserien'
SITE_ICON = 'alleserien_com.png'
URL_MAIN = 'https://alleserien.com/'
URL_FILME = URL_MAIN + 'filme'
URL_SERIEN = URL_MAIN + 'serien'
URL_SEARCH = URL_MAIN + 'search?search=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('page', 1)
    params.setParam('type', 'Alle')
    params.setParam('sUrl', URL_FILME)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('sUrl', URL_SERIEN)
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showContentMenu'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'), params)
    cGui().setEndOfDirectory()


def showContentMenu():
    params = ParameterHandler()
    params.setParam('sortBy', 'latest')
    cGui().addFolder(cGuiElement('Neueste Release', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sortBy', 'best')
    cGui().addFolder(cGuiElement('Am besten bewertet', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sortBy', 'name')
    cGui().addFolder(cGuiElement('Sortiert nach Name', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'))
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'divider.*?<div[^>]class'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, '#">(.*?)<')
    if not isMatch:
        cGui().showInfo()
        return

    for sName in aResult:
        params.setParam('type', sName)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    import time
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    sortBy = params.getValue('sortBy')
    page = params.getValue('page')
    type = params.getValue('type')
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    isMatch, url = cParser.parseSingleResult(sHtmlContent, ",url.*?'([^']+)")
    isMatch, token = cParser.parseSingleResult(sHtmlContent, "token':'([^']+)',")
    oRequest = cRequestHandler(url, ignoreErrors=(sGui is not False))
    if sSearchText:
        oRequest.addParameters('search', sSearchText)
        page = '1'
        type = 'Alle'
        sortBy = 'latest'
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addParameters('_token', token)
    oRequest.addParameters('from', 1900)
    oRequest.addParameters('page', page)
    oRequest.addParameters('rating', 0)
    oRequest.addParameters('sortBy', sortBy)
    oRequest.addParameters('to', time.strftime('%Y', time.localtime()))
    oRequest.addParameters('type', type)
    sHtmlContent = oRequest.request()
    pattern = '<a title=[^>]"(.*?)" href=[^>]"([^"]+).*?src=[^>]"([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sName, sUrl, sThumbnail in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        isTvshow = True if 'folge' in sUrl else False
        oGuiElement = cGuiElement(sName[:-1], SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail[:-1])
        oGuiElement.setFanart(sThumbnail[:-1])
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sName', sName)
        params.setParam('entryUrl', sUrl[:-1])
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        pattern = 'Next.*?data-p=[^>]"([\d]+).*?d-flex'
        isMatch, sUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatch:
            params.setParam('page', sUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'folge' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = '<div[^>]class="collapse[^>]m.*?id="s([\d]+)">'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '<p>([^<]+)')
    if not isMatch:
        cGui().showInfo()
        return

    total = len(aResult)
    for sSeasonNr in aResult[::-1]:
        oGuiElement = cGuiElement('Staffel ' + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('sSeasonNr', sSeasonNr)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sSeasonNr = params.getValue('sSeasonNr')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'id="s%s">.*?</table>' % sSeasonNr
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, "href = '([^']+).*?episodeNumber.*?>([\d]+)")
        isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '<p>([^<]+)')
    if not isMatch:
        cGui().showInfo()
        return

    total = len(aResult)
    for sUrl, sEpisodeNr in aResult[::-1]:
        oGuiElement = cGuiElement('Folge ' + sEpisodeNr, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setFanart(sThumbnail)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl, ignoreErrors=True).request()
    isMatch, aResult = cParser().parse(sHtmlContent, '<iframe[^>]src="([^"]+)')
    if not isMatch:
        pattern = '"partItem" data-id="([\d]+).*?data-controlid="([\d]+).*?e/([^"]+).png'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        if 'alleserien' in aResult[0]:
            result, hash = cParser().parseSingleResult(sHtmlContent, 'o/([^"]+)')
            oRequest = cRequestHandler(aResult[0] + '?do=getVideo')
            oRequest.addHeaderEntry('Referer', ParameterHandler().getValue('entryUrl'))
            oRequest.addHeaderEntry('Origin', 'http://alleserienplayer.com')
            oRequest.addHeaderEntry('Host', 'alleserienplayer.com')
            oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
            oRequest.addParameters('do', 'getVideo')
            oRequest.addParameters('hash', hash[0])
            oRequest.addParameters('r', ParameterHandler().getValue('entryUrl'))
            sHtmlContent = oRequest.request()
            isMatch, aResult = cParser().parse(sHtmlContent, 'file":"([^"]+).*?label":"([^"]+)')
            if isMatch:
                for sUrl, sName in aResult:
                    hoster = {'link': sUrl, 'name': sName}
                    hosters.append(hoster)
    else:
        if isMatch:
            result, token = cParser().parseSingleResult(sHtmlContent, "_token':'([^']+)")
            for ID, controlid, sName in aResult:
                oRequest = cRequestHandler('https://alleserien.com/getpart')
                oRequest.addParameters('_token', token[0])
                oRequest.addParameters('PartID', ID)
                oRequest.addParameters('ControlID', controlid)
                sHtmlContent = oRequest.request()
                result, link = cParser().parseSingleResult(sHtmlContent, 'src="([^"]+)')
                hoster = {'link': link, 'name': sName}
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
    showEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)
