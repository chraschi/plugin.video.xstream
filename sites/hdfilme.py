# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showGenre:     48 Stunden
    #showYears:     48 Stunden
    #showEpisodes:   4 Stunden


from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'hdfilme'
SITE_NAME = 'HD Filme'
SITE_ICON = 'hdfilme.png'

#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_'+ SITE_IDENTIFIER +'.domain', 'hdfilme.mom')
URL_MAIN = 'https://' + DOMAIN + '/'
#URL_MAIN = 'https://hdfilme.mom/'
URL_NEW = URL_MAIN + 'kinofilme-online/'
URL_KINO = URL_MAIN + 'aktuelle-kinofilme-im-kino/'
URL_MOVIES = URL_MAIN + 'kinofilme-online'
URL_SERIES = URL_MAIN + 'serienstream-deutsch/'
URL_SEARCH = URL_MAIN + 'index.php?do=search&subaction=search&story=%s'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_NEW)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30500), SITE_IDENTIFIER, 'showEntries'), params)  # New
    params.setParam('sUrl', URL_KINO)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30501), SITE_IDENTIFIER, 'showEntries'), params)  # Current films in the cinema
    params.setParam('sUrl', URL_MOVIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30502), SITE_IDENTIFIER, 'showEntries'), params)  # Movies
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'), params)# Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))# Search
    cGui().setEndOfDirectory()


def showGenre(entryUrl=False):
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48  # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = 'Genre">Genre.*?</ul>'
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
    isTvshow = False
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    iPage = int(params.getValue('page'))
    oRequest = cRequestHandler(entryUrl + 'page/' + str(iPage) if iPage > 0 else entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    pattern = '<div class="box-product' # Container Start
    pattern += '(.*?)<h3.*?'  # info dummy
    pattern += 'href="([^"]+).*?' # URL
    pattern += '">([^<]+).*?' # Name
    pattern += '(.*?)</li>' # dummy
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sInfo, sUrl, sName, sDummy in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        # Abfrage der voreingestellten Sprache
        sLanguage = cConfig().getSetting('prefLanguage')
        if (sLanguage == '1' and 'English*' in sName):   # Deutsch
            continue
        if (sLanguage == '2' and not 'English*' in sName):   # English
            continue
        elif sLanguage == '3':    # Japanisch
            cGui().showLanguage()
            continue
        isThumbnail, sThumbnail = cParser.parseSingleResult(sInfo, 'data-src="([^"]+)')  # Thumbnail
        isYear, sYear = cParser.parseSingleResult(sDummy, '([\d]+)\s</p>')  # Release Jahr
        isQuality, sQuality = cParser.parseSingleResult(sDummy, 'quality-product">([^<]+)')  # Qualität
        isTvshow = True if 'taffel' in sName else False
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes' if isTvshow else 'showHosters')
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        if isThumbnail:
            sThumbnail = URL_MAIN + sThumbnail
            oGuiElement.setThumbnail(sThumbnail)
        if isYear:
            oGuiElement.setYear(sYear)
        if isQuality:
            oGuiElement.setQuality(sQuality)
        oGuiElement.setMediaType('season' if isTvshow else 'movie')
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
        oGui.setView('tvshows' if isTvshow else 'movies')
        oGui.setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    sHtmlContent = oRequest.request()
    isMatch, aResult = cParser.parse(sHtmlContent, '"><a href="#">([^<]+)')
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '"description"[^>]content="([^"]+)')
    total = len(aResult)
    for sName in aResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', entryUrl)
        params.setParam('episode', sName)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sHtmlContent = cRequestHandler(ParameterHandler().getValue('entryUrl')).request()
    if ParameterHandler().getValue('episode'):
        pass
        pattern = '%s<.*?</ul>' % ParameterHandler().getValue('episode')
        isMatch, sHtmlContent = cParser.parseSingleResult(sHtmlContent, pattern)
    isMatch, aResult = cParser().parse(sHtmlContent, 'link="([^"]+)')
    if isMatch:
        sQuality = '720p'
        for sUrl in aResult:
            sName = cParser.urlparse(sUrl)
            if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
            if 'youtube' in sUrl:
                continue
            elif 'vod' in sUrl:
                continue
            elif sUrl.startswith('//'):
                 sUrl = 'https:' + sUrl
            hoster = {'link': sUrl, 'name': cParser.urlparse(sUrl), 'displayedName': '%s [I][%s][/I]' % (sName, sQuality), 'quality': sQuality, 'resolveable': True}
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