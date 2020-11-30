# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'topstreamfilm'
SITE_NAME = 'Topstreamfilm'
SITE_ICON = 'topstreamfilm.png'
URL_MAIN = 'https://topstreamfilm.com/'
URL_MOVIES = URL_MAIN + 'filme-stream-b/'
URL_SHOWS = URL_MAIN + 'serien/'
URL_POPULAR = URL_MAIN + 'beliebte-filme-serien/'
URL_SEARCH = URL_MAIN + '?s=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_SHOWS)
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_POPULAR)
    cGui().addFolder(cGuiElement('Beliebte', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MOVIES).request()
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, 'KATEGORIEN.*?</ul>')
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, 'href="([^"]+).*?>([^<]+)')
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
    sHtmlContent = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False)).request()
    pattern = 'TPost C.*?href="([^"]+).*?src="([^"]+)(.*?)</article>'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sThumbnail, sDummy in aResult:
        isName, sName = cParser.parse(sDummy, 'Title">([^<]+)')
        isDuration, sDuration = cParser.parseSingleResult(sDummy, 'time">(.*?)<')
        isYear, sYear = cParser.parseSingleResult(sDummy, 'date_range">(\d{4})')
        isDesc, sDesc = cParser.parseSingleResult(sDummy, 'Description">([^"]+)</p>')
        isRating, sRating = cParser.parseSingleResult(sDummy, 'star">([^<]+)')
        sThumbnail = 'https:' + sThumbnail
        if sSearchText and not cParser().search(sSearchText, sName[0]):
            continue
        isTvshow = True if 'Season' in sDummy or 'TV' in sDummy else False
        oGuiElement = cGuiElement(sName[0], SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if isDuration:
            oGuiElement.addItemValue('duration', FormatTime(sDuration))
        if isYear:
            oGuiElement.setYear(sYear)
        if isRating:
            oGuiElement.addItemValue('rating', sRating)
        params.setParam('entryUrl', sUrl)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui and not sSearchText:
        pattern = 'next page-numbers" href="([^"]+)'
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, pattern)
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'Season' in sDummy or 'TV' in sDummy else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    isMatch, aResult = cParser.parse(sHtmlContent, 'Season <span>([\d]+)')
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'class="Description">(.*?)</p>')
    total = len(aResult)
    for sSeason, in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeason, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setThumbnail(params.getValue('sThumbnail'))
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('Season', sSeason)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sSeason = params.getValue('Season')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = 'Season <span>%s.*?></tbody>' % sSeason
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = 'Num">([\d]+).*?href="([^"]+)'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'class="Description">(.*?)</p>')
    total = len(aResult)
    for sEpisode, sUrl in aResult:
        oGuiElement = cGuiElement('Folge ' + sEpisode, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setSeason(sSeason)
        oGuiElement.setEpisode(sEpisode)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(params.getValue('sThumbnail'))
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', sUrl)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    entryUrl = ParameterHandler().getValue('entryUrl')
    oRequest = cRequestHandler(entryUrl)
    sHtmlContent = oRequest.request()
    isMatch, sUrl = cParser().parseSingleResult(sHtmlContent, '" src="([^"]+)" f')
    if isMatch:
        oRequest = cRequestHandler(sUrl)
        sHtmlContent = oRequest.request()
        isMatch, sUrl = cParser().parseSingleResult(sHtmlContent, '" src="([^"]+)" f')
    if isMatch:
        oRequest = cRequestHandler(sUrl[:-1])
        sHtmlContent = oRequest.request()
        isMatch, sId = cParser().parseSingleResult(sHtmlContent, "var id = trde[^>]'([^']+)")
        isMatch, sUrl = cParser().parseSingleResult(sHtmlContent, "iframe.src = '([^']+)")
    if isMatch:
        oRequest = cRequestHandler(sUrl + sId[::-1], caching=False)
        sHtmlContent = oRequest.request()
        sUrl = oRequest.getRealUrl()
        isMatch, id = cParser.parseSingleResult(sUrl, 'id=([^"]+)')
        netloc = cParser.urlparse(sUrl)
        import time
        m3u8 = 'https://{0}/playlist/{1}/{2}'.format(netloc, id, int(time.time() * 1000))
    if isMatch:
        oRequest = cRequestHandler(m3u8)
        oRequest.addHeaderEntry('Referer', sUrl)
        oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
        sHtmlContent = oRequest.request()
        isMatch, aResult = cParser().parse(sHtmlContent, 'RESOLUTION=\d+x([\d]+)([^#]+)')
    for sQ, sUrl in aResult:
        hoster = {'link': 'https://{0}{1}'.format(netloc, sUrl), 'name': sQ}
        hosters.append(hoster)
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


def FormatTime(dig):
    import re
    if dig:
        t = re.findall('(\d+)h[^>](\d+)m', dig)
        if t:
            if t[0][0] >= '1':
                h = int(t[0][0]) * 60
                return h + int(t[0][1])
            else:
                return int(t[0][1])
        else:
            t = re.findall('(\d+)', dig)
            if t:
                return int(t[0])
    if not dig:
        return 0
