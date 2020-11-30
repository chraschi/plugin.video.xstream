# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'movietown_org'
SITE_NAME = 'MovieTown'
SITE_ICON = 'movietown.png'
URL_MAIN = 'https://movietown.org/'
URL_LIST = URL_MAIN + 'secure/titles?type=%s&page=%s&perPage=25&genre=%s'
URL_GET = URL_MAIN + 'secure/titles/%s?titleId=%s'
URL_SEARCH = URL_MAIN + 'secure/search/%s?type=&limit=20'
URL_GENRES_LIST = {'Abenteuer', 'Action', 'Animation', 'Anime', 'Biographie', 'Bollywood', 'Dokumentation', 'Drama', 'Erotik', 'Familie', 'Fantasy', 'History', 'Horror', 'Kinder', 'Komödie', 'Krieg', 'Krimi', 'Liebesfilm', 'Musik', 'Mystery', 'Romantik', 'Science-Fiction', 'Sonstige', 'Sport', 'Thriller', 'Trickfilm', 'Western'}


def load():
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_LIST)
    params.setParam('type', 'movie')
    cGui().addFolder(cGuiElement('Filme', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Film Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    params.setParam('type', 'series')
    cGui().addFolder(cGuiElement('Serien', SITE_IDENTIFIER, 'showEntries'), params)
    cGui().addFolder(cGuiElement('Serien Genre', SITE_IDENTIFIER, 'showGenresList'), params)
    cGui().addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    cGui().setEndOfDirectory()


def showGenresList():
    for key in sorted(URL_GENRES_LIST):
        params = ParameterHandler()
        params.setParam('genre', key)
        cGui().addFolder(cGuiElement(key, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    genre = params.getValue('genre')
    if not genre: genre = ''
    type = params.getValue('type')
    iPage = int(params.getValue('page'))
    if iPage <= 0:
        iPage = 1
    sUrl = URL_LIST % (type, str(iPage), genre)
    oRequest = cRequestHandler(sUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = '"id":([\d]+),"name":"([^"]+).*?year":([\d]+),"description":"([^"]+).*?poster":"([^"]+)","backdrop":"([^"]+)","runtime":([\d]+).*?is_series":([^,]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sId, sName, sYear, sDesc, sThumbnail, sFanart, sDuration, isserie in aResult:
        isTvshow = True if 'true' in isserie else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        oGuiElement.addItemValue('duration', int(sDuration))
        params.setParam('entryUrl', URL_GET % (sId, sId))
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, 'next_page_url":".*?page=([\d]+)')
        if isMatchNextPage:
            params.setParam('page', (iPage + 1))
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sHtmlContent = cRequestHandler(sUrl).request()
    isMatch, aResult = cParser().parse(sHtmlContent, 'number":([\d]+)')
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parse(sHtmlContent, 'description","content":"([^"]+)')
    total = len(aResult)
    for sSeasonNr in aResult:
        oGuiElement = cGuiElement('Staffel ' + sSeasonNr, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc[0])
        params.setParam('sSeasonNr', sSeasonNr)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sSeasonNr = params.getValue('sSeasonNr')
    sThumbnail = params.getValue('sThumbnail')
    sUrl = sUrl + '&seasonNumber=%s' % sSeasonNr
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'name":"([^"]+)".*?season_id":\d+,"season_number":%s,"episode_number":([\d]+)' % sSeasonNr
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        oGui.showInfo()
        return

    total = len(aResult)
    for sName, sEpisodeNr in aResult:
        isDesc, sDesc = cParser.parse(sHtmlContent, 'name":"%s","description":"([^"]+)' % sName)
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc[0])
        params.setParam('entryUrl', sUrl + '&episodeNumber=' + sEpisodeNr)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    sUrl = ParameterHandler().getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    pattern = 'name":"([^"]+)","thumbnail":null,"url":"([^"]+)'
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    hosters = []
    if isMatch:
        for sName, sUrl in aResult:
            if 'youtube' not in sUrl:
                hoster = {'link': sUrl, 'name': sName}
                hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    return [{'streamUrl': sUrl, 'resolved': False}]


def showSearchEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = '"id":([\d]+),"name":"([^"]+).*?year":([\d]+),"description":"([^"]+).*?poster":"([^"]+).*?is_series":([^,]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sId, sName, sYear, sDesc, sThumbnail, isserie in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        isTvshow = True if 'true' in isserie else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setYear(sYear)
        oGuiElement.setDescription(sDesc)
        params.setParam('entryUrl', URL_GET % (sId, sId))
        params.setParam('sThumbnail', sThumbnail)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showSearchEntries(URL_SEARCH % cParser().quotePlus(sSearchText), oGui, sSearchText)
