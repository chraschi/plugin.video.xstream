# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'hdfilme'
SITE_NAME = 'HDfilme'
SITE_ICON = 'hdfilme.png'
URL_MAIN = 'https://hdfilme.cx/'
URL_MOVIES = URL_MAIN + 'filme1?'
URL_SHOWS = URL_MAIN + 'serien1?'
URL_SEARCH = URL_MAIN + 'search?key=%s'


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMenu'), params)
    params.setParam('sUrl', URL_SHOWS)
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showMenu'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()


def showMenu():
    params = ParameterHandler()
    baseURL = params.getValue('sUrl')
    params.setParam('sUrl', baseURL + 'sort=top&sort_type=desc')
    cGui().addFolder(cGuiElement('Update', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'sort=year&sort_type=desc')
    cGui().addFolder(cGuiElement('Year', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'sort=name&sort_type=desc')
    cGui().addFolder(cGuiElement('Name', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'sort=imdb_rate&sort_type=desc')
    cGui().addFolder(cGuiElement('IMDB', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'sort=rate_point&sort_type=desc')
    cGui().addFolder(cGuiElement('Rate', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL + 'sort=view_total&sort_type=desc')
    cGui().addFolder(cGuiElement('View', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', baseURL)
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    entryUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(entryUrl).request()
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, 'Genre</option>.*?</div>')
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, 'value="([^"]+)">([^<]+)')
    if not isMatch:
        cGui().showInfo()
        return

    for sID, sName in sorted(aResult, key=lambda k: k[1]):
        params.setParam('sUrl', entryUrl + 'category=' + sID + '&country=&sort=&key=&sort_type=desc')
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + '&page=' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('Referer', URL_MAIN)
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    if not sSearchText:
        oRequest.addParameters('load', 'full-page')
    sHtmlContent = oRequest.request()
    pattern = '<ul[^>]class="products row">(.*?)</ul>'
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, pattern)
    if isMatch:
        pattern = '<div class="box-product clearfix" data-popover.*?href="([^"]+).*?data-src="([^"]+).*?title=".*?">([^<]+)'
        isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sThumbnail, sName in aResult:
        sName = sName.replace(' stream', '')
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        sThumbnail = sThumbnail.replace('_thumb', '')
        isMatch, sYear = cParser.parse(sName, '(.*?)\((\d*)\)')
        for name, year in sYear:
            sName = name
            sYear = year
            break

        isTvshow = True if 'staffel' in sUrl or 'staffel' in sName else False
        if 'sort=year&sort_type=desc' in entryUrl and not isTvshow:
            sName += ' (' + str(sYear) + ')'
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        if sYear:
            oGuiElement.setYear(sYear)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui and not sSearchText:
        sPageNr = int(params.getValue('page'))
        if sPageNr == 0:
            sPageNr = 2
        else:
            sPageNr += 1
        params.setParam('page', int(sPageNr))
        params.setParam('sUrl', entryUrl)
        oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if URL_SHOWS in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    sUrl = cParser.urlEncode(params.getValue('entryUrl'), ':|/') + '/folge-1'
    sThumbnail = params.getValue('sThumbnail')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'data-episode-id="([\d]+).*?folge.*?([\d]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    isMatch, sID = cParser.parse(sHtmlContent, 'data-movie-id="([\d]+)')
    if not isMatch:
        cGui().showInfo()
        return

    total = len(aResult)
    for eID, eNr in aResult:
        oGuiElement = cGuiElement('Folge ' + eNr, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('eID', eID)
        params.setParam('sID', sID[0])
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    eID = ParameterHandler().getValue('eID')
    sID = ParameterHandler().getValue('sID')
    rUrl = ParameterHandler().getValue('entryUrl')
    sUrl = cParser.urlEncode(ParameterHandler().getValue('entryUrl'), ':|/') + '/deutsch'
    if not eID and not sID:
        oRequest = cRequestHandler(sUrl)
        oRequest.addHeaderEntry('Origin', URL_MAIN)
        oRequest.addHeaderEntry('Referer', sUrl)
        sHtmlContent = oRequest.request()
        pattern = 'data-movie-id="(\d+).*?data-episode-id="(\d+)"'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
        if isMatch:
            sID = aResult[0][0]
            eID = aResult[0][1]

    oRequest = cRequestHandler(URL_MAIN + 'movie/load-stream/' + sID + '/' + eID + '?')
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', rUrl)
    sHtmlContentBase = oRequest.request()
    isMatch, hUrl = cParser().parse(sHtmlContentBase, 'urlVideo = "([^"]+)')

    if isMatch:
        oRequest = cRequestHandler(hUrl[0])
        oRequest.addHeaderEntry('Referer', sUrl)
        oRequest.addHeaderEntry('Origin', URL_MAIN)
        sHtmlContent = oRequest.request()
        url = cParser().urlparse(hUrl[0])
        pattern = 'RESOLUTION=\d+x([\d]+)([^#]+)'
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
        if isMatch:
            for sQualy, sUrl in aResult:
                sUrl = 'https://' + url + sUrl + '|Origin=https%3A%2F%2Fhdfilme.cx%2F&Referer=https%3A%2F%2Fhdfilme.cx%2F'
                hoster = {'link': sUrl, 'name': sQualy}
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
