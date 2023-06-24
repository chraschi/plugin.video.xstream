# -*- coding: utf-8 -*-
# Python 3
# Always pay attention to the translations in the menu!
# HTML LangzeitCache hinzugefügt
    #showGenre:     48 Stunden
    #showEntries:    6 Stunden
    #showSeasons:    6 Stunden
    #showEpisodes:   4 Stunden

import base64
import binascii
import random
import string

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser, cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib import jsunpacker
from itertools import zip_longest as ziplist

SITE_IDENTIFIER = 'kinoger'
SITE_NAME = 'Kinoger'
SITE_ICON = 'kinoger.png'

#Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
URL_MAIN = 'https://' + cConfig().getSetting('plugin_kinoger.domain')
URL_SERIES = URL_MAIN + '/stream/serie/'


def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30500), SITE_IDENTIFIER, 'showEntries'), params)    # New
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30511), SITE_IDENTIFIER, 'showEntries'), params)  # Series
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showGenre'))    # Genre
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'))   # Search
    cGui().setEndOfDirectory()


def showGenre():
    params = ParameterHandler()
    oRequest = cRequestHandler(URL_MAIN)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 48 # 48 Stunden
    sHtmlContent = oRequest.request()
    pattern = '<li[^>]class="links"><a href="([^"]+).*?/>([^<]+)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    if sSearchText:
        oRequest.addParameters('story', sSearchText)
        oRequest.addParameters('do', 'search')
        oRequest.addParameters('subaction', 'search')
        oRequest.addParameters('x', '0')
        oRequest.addParameters('y', '0')
        oRequest.addParameters('titleonly', '3')
        oRequest.addParameters('submit', 'submit')
    else:
        oRequest.addParameters('dlenewssortby', 'date')
        oRequest.addParameters('dledirection', 'desc')
        oRequest.addParameters('set_new_sort', 'dle_sort_main')
        oRequest.addParameters('set_direction_sort', 'dle_direction_main')
    sHtmlContent = oRequest.request()
    pattern = 'class="title".*?' # container start
    pattern += 'href="([^"]+)' # url
    pattern += '">([^<]+).*?' # name
    pattern += 'src="([^"]+)' # thumb
    pattern += '(.*?)</span>' # dummy
    isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sName, sThumbnail, sDummy in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        isTvshow = True if 'staffel' in sName.lower() or 'serie' in entryUrl or ';">S0' in sDummy else False
        isYear, sYear = cParser.parse(sName, '(.*?)\((\d*)\)') # Jahr und Name trennen
        for name, year in sYear:
            sName = name
            sYear = year
            break
        isDesc, sDesc = cParser.parseSingleResult(sDummy, '</b>([^<]+)') # Beschreibung
        isDuration, sDuration = cParser.parseSingleResult(sDummy, '(?:Laufzeit|Spielzeit).*?([\d]+)') # Laufzeit
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        oGuiElement.setThumbnail(sThumbnail)
        if isYear:
            oGuiElement.setYear(sYear)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if isDuration:
            oGuiElement.addItemValue('duration', sDuration)
        oGuiElement.setMediaType('tvshow' if isTvshow else 'movie')
        # Parameter übergeben
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('TVShowTitle', sName)
        params.setParam('entryUrl', sUrl)
        oGui.addFolder(oGuiElement, params, isTvshow, total)
    if not sGui:
        isMatchNextPage, sNextUrl = cParser().parseSingleResult(sHtmlContent, '<a[^>]href="([^"]+)">vorw')
        if isMatchNextPage:
            params.setParam('sUrl', sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)
        oGui.setView('tvshows' if 'staffel' in sName.lower() else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    # Parameter laden
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('TVShowTitle')
    oRequest = cRequestHandler(entryUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # HTML Cache Zeit 6 Stunden
    sHtmlContent = oRequest.request()
    L11 = []
    isMatchsst, sstsContainer = cParser.parseSingleResult(sHtmlContent, 'sst.show.*?</script>')
    if isMatchsst:
        sstsContainer = sstsContainer.replace('[', '<').replace(']', '>')
        isMatchsst, L11 = cParser.parse(sstsContainer, "<'([^>]+)")
        if isMatchsst:
            total = len(L11)
    L22 = []
    isMatchollhd, ollhdsContainer = cParser.parseSingleResult(sHtmlContent, 'ollhd.show.*?</script>')
    if isMatchollhd:
        ollhdsContainer = ollhdsContainer.replace('[', '<').replace(']', '>')
        isMatchollhd, L22 = cParser.parse(ollhdsContainer, "<'([^>]+)")
        if isMatchollhd:
            total = len(L22)
    L33 = []
    isMatchpw, pwsContainer = cParser.parseSingleResult(sHtmlContent, 'pw.show.*?</script>')
    if isMatchpw:
        pwsContainer = pwsContainer.replace('[', '<').replace(']', '>')
        isMatchpw, L33 = cParser.parse(pwsContainer, "<'([^>]+)")
        if isMatchpw:
            total = len(L33)
    L44 = []
    isMatchgo, gosContainer = cParser.parseSingleResult(sHtmlContent, 'go.show.*?</script>')
    if isMatchgo:
        gosContainer = gosContainer.replace('[', '<').replace(']', '>')
        isMatchgo, L44 = cParser.parse(gosContainer, "<'([^>]+)")
        if isMatchgo:
            total = len(L44)

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, '</b>([^"]+)<br><br>') # Beschreibung
    for i in range(0, total):
        try:
            params.setParam('L11', L11[i])
        except Exception:
            pass
        try:
            params.setParam('L22', L22[i])
        except Exception:
            pass
        try:
            params.setParam('L33', L33[i])
        except Exception:
            pass
        try:
            params.setParam('L44', L44[i])
        except Exception:
            pass
        i = i + 1
        oGuiElement = cGuiElement('Staffel ' + str(i), SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(i)
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        # Parameter übergeben
        params.setParam('sDesc', sDesc)
        params.setParam('sSeasonNr', i)
        cGui().addFolder(oGuiElement, params, True, total)
        cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    # Parameter laden
    sSeasonNr = params.getValue('sSeasonNr')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('TVShowTitle')
    sDesc = params.getValue('sDesc')
    L11 = []
    if params.exist('L11'):
        L11 = params.getValue('L11')
        isMatch1, L11 = cParser.parse(L11, "(http[^']+)")
    L22 = []
    if params.exist('L22'):
        L22 = params.getValue('L22')
        isMatch, L22 = cParser.parse(L22, "(http[^']+)")
    L33 = []
    if params.exist('L33'):
        L33 = params.getValue('L33')
        isMatch3, L33 = cParser.parse(L33, "(http[^']+)")
    L44 = []
    if params.exist('L44'):
        L44 = params.getValue('L44')
        isMatch4, L44 = cParser.parse(L44, "(http[^']+)")
    liste = ziplist(L11, L22, L33, L44)
    i = 0
    for sUrl in liste:
        i = i + 1
        oGuiElement = cGuiElement('Episode ' + str(i), SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(i)
        oGuiElement.setMediaType('episode')
        if sDesc:
            oGuiElement.setDescription(sDesc)
        if sThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sLinks', sUrl)
        cGui().addFolder(oGuiElement, params, False)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    headers = '&Accept-Language=de%2Cen-US%3Bq%3D0.7%2Cen%3Bq%3D0.3&Accept=%2A%2F%2A&User-Agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%3B+rv%3A99.0%29+Gecko%2F20100101+Firefox%2F99.0'
    params = ParameterHandler()
    if params.exist('sLinks'):
        sUrl = params.getValue('sLinks')
        isMatch, aResult = cParser().parse(sUrl, "(http[^']+)")
    else:
        sUrl = params.getValue('entryUrl')
        sHtmlContent = cRequestHandler(sUrl, ignoreErrors=True).request()
        pattern = "show[^>]\d,[^>][^>]'([^']+)"
        isMatch, aResult = cParser().parse(sHtmlContent, pattern)
    if isMatch:
        for sUrl in aResult:
            if 'kinoger.ru' in sUrl: # Muss neu erstellt werden
                continue

            if 'kinoger.be' in sUrl:
                oRequest = cRequestHandler(sUrl, caching=False, ignoreErrors=True)
                oRequest.addHeaderEntry('Referer', 'https://kinoger.com/')
                sHtmlContent = oRequest.request()
                isMatch, packed = cParser.parseSingleResult(sHtmlContent, '(eval\s*\(function.*?)</script>')
                if isMatch:
                    sHtmlContent = jsunpacker.unpack(packed)
                isMatch, j = cParser.parse(sHtmlContent, 'ct":"([^"]+)","iv":"([^"]+)","s":"([^"]+)')
                if isMatch:
                    try:
                        ciphertext = base64.b64decode(j[0][0])
                        salt = binascii.unhexlify(j[0][2])
                        password = 'XOmurdOgNnjMwYah'.encode('utf-8')
                        sHtmlContent = cUtil.evp_decode(ciphertext, password, salt)
                    except Exception:
                        sHtmlContent = ''
                isMatch, hUrl = cParser.parseSingleResult(sHtmlContent, 'sources.*?file.*?(http[^"]+)')
                if isMatch:
                    hUrl = hUrl.replace('\\', '')
                    oRequest = cRequestHandler(hUrl, caching=False, ignoreErrors=True)
                    oRequest.addHeaderEntry('Referer', 'https://kinoger.be/')
                    oRequest.addHeaderEntry('Origin', 'https://kinoger.be')
                    oRequest.removeNewLines(False)
                    sHtmlContent = oRequest.request()
                    pattern = 'RESOLUTION=(\d+x\d+).*?\n([^#"]+)'
                    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
                if isMatch:
                    for sQualy, sUrl in aResult:
                        sUrl = (hUrl.split('video')[0].strip() + sUrl.strip())
                        sUrl = sUrl + '|Origin=https%3A%2F%2Fkinoger.be&Referer=https%3A%2F%2Fkinoger.be%2F' + headers
                        hoster = {'link': sUrl, 'name': 'Kinoger.be [I][HD %sp][/I]' % sQualy, 'resolveable': True}
                        hosters.append(hoster)

            elif 'kinoger.pw' in sUrl:
                try:
                    url = get_streamsburl('kinoger.pw', sUrl.replace('.html', '').split('/')[4])
                    oRequest = cRequestHandler(url, caching=False, ignoreErrors=True)
                    oRequest.addHeaderEntry('Referer', sUrl)
                    oRequest.addHeaderEntry('watchsb', 'sbstream')
                    sHtmlContent = oRequest.request()
                    isMatch, aResult = cParser.parse(sHtmlContent, 'file":"([^"]+)')
                    if isMatch:
                        oRequest = cRequestHandler(aResult[0], caching=False, ignoreErrors=True)
                        oRequest.addHeaderEntry('Referer', 'https://kinoger.pw/')
                        oRequest.addHeaderEntry('Origin', 'https://kinoger.pw')
                        sHtmlContent = oRequest.request()
                        isMatch, aResult = cParser.parse(sHtmlContent, 'RESOLUTION=(\d+x\d+).*?(http[^"]+)#')
                    if isMatch:
                        for sQualy, sUrl in aResult:
                            sUrl = sUrl + '|Origin=https%3A%2F%2Fkinoger.pw&Referer=https%3A%2F%2Fkinoger.pw%2F' + headers
                            hoster = {'link': sUrl, 'name': 'StreamSB [I][HD %sp][/I]' % sQualy, 'resolveable': True}
                            hosters.append(hoster)
                except Exception:
                    pass

            elif 'kinoger.re' in sUrl:
                oRequest = cRequestHandler('https://kinoger.re/api/video/stream/get', ignoreErrors=True, jspost=True)
                oRequest.addHeaderEntry('Referer', sUrl)
                oRequest.addParameters('id', sUrl.split('/')[-1])
                sHtmlContent = oRequest.request()
                isMatch, aResult = cParser.parse(sHtmlContent, '"label":"([^"]+).*?file":"([^"]+)')
                if isMatch:
                    for sQualy, sUrl in aResult:
                        sUrl = sUrl + '|Referer=https%3A%2F%2Fkinoger.re%2F' + headers
                        hoster = {'link': sUrl, 'name': 'Kinoger.re [I][HD %s][/I]' % sQualy, 'resolveable': True}
                        hosters.append(hoster)
            elif 'start.u' in sUrl: # Da Offline überspringen
                continue

            else:
                hoster = {'link': sUrl + 'DIREKT', 'name': cParser.urlparse(sUrl)}
                hosters.append(hoster)
    if not isMatch:
        cGui().showInfo()
        return

    if hosters:
        hosters.append('getHosterUrl')
        return hosters


def getHosterUrl(sUrl=False):
    if sUrl.startswith('//'):
        sUrl = 'https:' + sUrl
    if sUrl.endswith('DIREKT'):
        Request = cRequestHandler(sUrl, caching=False)
        Request.request()
        sUrl = Request.getRealUrl()  # hole reale URL von der Umleitung
        return [{'streamUrl': sUrl[:-6], 'resolved': False}]
    else:
        return [{'streamUrl': sUrl, 'resolved': True}]


def showSearch():
    sSearchText = cGui().showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    showEntries(URL_MAIN, oGui, sSearchText)


def get_streamsburl(host, media_id): # StreamSB Url Abfrage
    # Copyright (c) 2019 vb6rocod

    def makeid(length):
        t = string.ascii_letters + string.digits
        return ''.join([random.choice(t) for _ in range(length)])

    x = '{0}||{1}||{2}||streamsb'.format(makeid(12), media_id, makeid(12))
    c1 = binascii.hexlify(x.encode('utf8')).decode('utf8')
    x = '7Vd5jIEF2lKy||nuewwgxb1qs'
    c2 = binascii.hexlify(x.encode('utf8')).decode('utf8')
    return 'https://{0}/{1}7/{2}'.format(host, c2, c1)