# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser, cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'hd-streams_org'
SITE_NAME = 'HD-Streams.org'
SITE_ICON = 'hdstreams_org.png'
URL_MAIN = 'https://hd-streams.org/'
URL_FILME = URL_MAIN + 'movies?perPage=54'
URL_SERIE = URL_MAIN + 'seasons?perPage=54'
URL_POPULAR = URL_MAIN + 'popular'
URL_SEARCH = URL_MAIN + 'search?q=%s&movies=true&seasons=true&actors=true&didyoumean=true&extended=true'


def load():
    logger.info('Load %s' % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_FILME)
    oGui.addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showMenu'), params)
    params.setParam('sUrl', URL_SERIE)
    oGui.addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showMenu'), params)
    params.setParam('sUrl', URL_POPULAR)
    oGui.addFolder(cGuiElement('Beliebt', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showMenu():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    params.setParam('sUrl', sUrl + '&orderBy=date&order=desc')
    cGui().addFolder(cGuiElement('Hinzugefügt', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', sUrl + '&orderBy=vote_average&order=desc')
    cGui().addFolder(cGuiElement('Bewertung', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', sUrl + '&orderBy=release_date&order=desc')
    cGui().addFolder(cGuiElement('Erstaustrahlung', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', sUrl + '&order=desc')
    cGui().addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    params.setParam('sUrl', sUrl + '&order=desc')
    cGui().addFolder(cGuiElement('Jahr', SITE_IDENTIFIER, 'showYear'), params)
    params.setParam('sUrl', sUrl + '&orderBy=title&order=asc')
    cGui().addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, aResult = cParser.parse(sHtmlContent, "text: '([^']+)', value: '(\d+)")
    if not isMatch:
        cGui().showInfo()
        return

    for sName, sID in aResult:
        params.setParam('sUrl', sUrl + '&genre[]=' + sID)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showYear():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, 'source.years.*?;')
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, '(\d+)')
    if not isMatch:
        cGui().showInfo()
        return

    for sID in aResult:
        params.setParam('sUrl', sUrl + '&year[]=' + sID)
        cGui().addFolder(cGuiElement(sID, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    if sSearchText:
        sHtmlContent = cRequestHandler(URL_MAIN).request()
        pattern = '<meta name="csrf-token" content="([^"]+)">'
        isMatch, token = cParser.parseSingleResult(sHtmlContent, pattern)
        oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
        oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
        oRequest.addHeaderEntry('X-CSRF-TOKEN', token)
        sHtmlContent = oRequest.request()
        pattern = '{"title":"([^"]+)","original_title(?:":""|":"[^"]+"),"url":"([^"]+)","src":"([^"]+)'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    else:
        oRequest = cRequestHandler(entryUrl)
        sHtmlContent = oRequest.request()
        pattern = 'href="([^"]+)"[^>]class="card.*?src="(?:([^"]+)?).*?card__title">([^<]+)'
        isMatch, aResult = cParser.parse(sHtmlContent, pattern)
        if not isMatch:
            pattern = 'href="([^"]+)"><div.*?src="([^"]+).*?0">([^<]+)'
            isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl1, sThumbnail1, sName1 in aResult:
        if sSearchText:
            sName = sUrl1
            sUrl = sThumbnail1
            sThumbnail = sName1
        else:
            sUrl = sUrl1
            sThumbnail = sThumbnail1
            sName = sName1
        if sSearchText and not cParser.search(sSearchText, sName.replace('<b>', '').replace('</b>', '')):
            continue
        isMatch, sYear = cParser.parse(sName, '(.*?)\((\d*)\)')
        for name, year in sYear:
            sName = name
            sYear = year
            break
        isTvshow = True if "series" in sUrl else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail
        oGuiElement.setThumbnail(sThumbnail)
        if sYear:
            oGuiElement.setYear(sYear)
        params.setParam('entryUrl', sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, 'href="([^"]+)"[^>]*rel="next"')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'series' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sTVShowTitle = params.getValue('sName')
    sUrl = params.getValue('entryUrl')
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    pattern = 'lazy"[^>*]src="([^"]+)" alt="([^"]+)">.*?loadEpisode[^>]*(\d+),'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        oGui.showInfo()
        return

    isSeason, sSeason = cParser.parseSingleResult(sHtmlContent, '">Staffel[^>]*(\d+)<')
    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, 'v-card__text">([^<]+)')
    isFanart, sFanart = cParser.parseSingleResult(sHtmlContent, "background-image.*?'([^']+)")
    total = len(aResult)
    for sThumbnail, sName, sEpisodeNr in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        if isSeason:
            oGuiElement.setSeason(sSeason[0])
            oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
        if isFanart:
            oGuiElement.setFanart(URL_MAIN + sFanart)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        params.setParam('sEpisodeNr', sEpisodeNr)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    hosters = []
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    isToken, sToken = cParser.parseSingleResult(sHtmlContent, 'csrf-token[^>]*content="([^"]+)')
    if isToken:
        if 'season' in sUrl:
            sEpisodeNr = params.getValue('sEpisodeNr')
            pattern = "loadEpisodeStream[^>]'%s'[^>]*'(\d+)'.*?'([^']+)'.*?'([^']+).*?title>([^<]+)" % sEpisodeNr
            isMatch, aResult = cParser.parse(sHtmlContent, pattern)
            if isMatch:
                for hNr, sQuality, sLang, sName in aResult:
                    sLink = getLinks(sUrl, sEpisodeNr, hNr, sLang, sQuality, sToken)
                    hoster = {'link': sLink, 'name': cParser.urlparse(sLink)}
                    hosters.append(hoster)
                if hosters:
                    hosters.append('getHosterUrl')
                return hosters
        else:
            pattern = "recaptcha[^>]'(\d+)',[^>]'(\d+)',[^>]'([^']+)',[^>]'([^']+)'"
            isMatch, aResult = cParser.parse(sHtmlContent, pattern)
            if isMatch:
                for sEpisodeNr, hNr, sLang, sQuality in aResult:
                    sLink = getLinks(sUrl, sEpisodeNr, hNr, sLang, sQuality, sToken)
                    hoster = {'link': sLink, 'name': cParser.urlparse(sLink)}
                    hosters.append(hoster)
                if hosters:
                    hosters.append('getHosterUrl')
                return hosters


def getLinks(sUrl, e, h, sLang, sQuality, sToken):
    import base64, json, binascii
    oRequest = cRequestHandler(sUrl + '/stream')
    oRequest.addHeaderEntry('X-CSRF-TOKEN', sToken)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', sUrl)
    oRequest.addParameters('e', e)
    oRequest.addParameters('h', h)
    if sLang:
        oRequest.addParameters('lang', sLang)
    if sQuality:
        oRequest.addParameters('q', sQuality)
    oRequest.addParameters('grecaptcha', '')
    sHtmlContent = oRequest.request()
    Data = json.loads(sHtmlContent)
    tmp = Data.get('d', '') + Data.get('c', '') + Data.get('iv', '') + Data.get('f', '') + Data.get('h', '') + Data.get('b', '')
    tmp = json.loads(base64.b64decode(tmp))
    salt = binascii.unhexlify(tmp['s'])
    ciphertext = base64.b64decode(tmp['ct'][::-1])
    b = base64.b64encode(sToken[::-1].encode('utf-8'))
    tmp = cUtil.evp_decode(ciphertext, b, salt)
    tmp = json.loads(base64.b64decode(tmp))
    ciphertext = base64.b64decode(tmp['ct'][::-1])
    salt = binascii.unhexlify(tmp['s'])
    b = ''
    a = sToken
    for idx in range(len(a) - 1, 0, -2):
        b += a[idx]
    if Data.get('e', None):
        b += '1'
    else:
        b += '0'
    tmp = cUtil.evp_decode(ciphertext, b.encode('utf-8'), salt)
    return json.loads(tmp)


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_SEARCH % cParser.quotePlus(sSearchText), oGui, sSearchText)
