# -*- coding: utf-8 -*-
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui
from resources.lib.tools import logger
import re
try:
    from urllib2 import Request, urlopen
    from urllib import urlencode
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode


class cJDownloader2Handler:
    def sendToJDownloader2(self, sUrl):
        if self.__checkConfig() is False:
            cGui().showError('JDownloader2', 'Settings ueberpruefen', 5)
            return False

        if self.__checkConnection() is False:
            cGui().showError('JDownloader2', 'Verbindung fehlgeschlagen (JD2 oder External CNL Port support aus?)', 5)
            return False

        if self.__download(sUrl) is True:
            cGui().showInfo('JDownloader2', 'Link gesendet', 5)
            return True
        return False

    def __client(self, path, params):
        sHost = self.__getHost()
        sPort = self.__getPort()
        ENCODING = 'utf-8'
        url = 'http://{}:{}/{}'.format(sHost, sPort, path)
        if params is not None:
            headers = {'Content-Type': 'application/x-www-form-urlencoded;charset={}'.format(ENCODING), }
            request = Request(url, urlencode(params).encode(ENCODING), headers)
        else:
            request = Request(url)
        return urlopen(request).read().decode(ENCODING).strip()

    def __download(self, sFileUrl):
        logger.info('JD2 Link: ' + str(sFileUrl))
        params = {'passwords': 'myPassword', 'source': 'http://jdownloader.org/spielwiese', 'urls': sFileUrl, 'submit': 'Add Link to JDownloader', }
        if self.__client('flash/add', params).lower() == 'success':
            return True
        else:
            return False

    def __checkConfig(self):
        logger.info('check JD2 Addon setings')
        bEnabled = cConfig().getSetting('jd2_enabled')
        if (bEnabled == 'true'):
            return True
        return False

    def __getHost(self):
        return cConfig().getSetting('jd2_host')

    def __getPort(self):
        return cConfig().getSetting('jd2_port')

    def __checkConnection(self):
        logger.info('check JD2 Connection')
        try:
            output = self.__client('jdcheck.js', None)
            pattern = re.compile(r'jdownloader\s*=\s*true', re.IGNORECASE)
            if pattern.search(output) != None:
                return True
        except Exception:
            return False
        return False
