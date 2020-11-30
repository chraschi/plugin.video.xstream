# -*- coding: utf-8 -*-
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib import common
from resources.lib import pyaes
import re, hashlib, sys, xbmc
try:
    from urlparse import urlparse
    from htmlentitydefs import name2codepoint
    from urllib import quote, unquote, quote_plus, unquote_plus
except ImportError:
    from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlparse
    from html.entities import name2codepoint


class cParser:
    @staticmethod
    def parseSingleResult(sHtmlContent, pattern):
        aMatches = re.compile(pattern).findall(sHtmlContent)
        if len(aMatches) == 1:
            aMatches[0] = cParser.__replaceSpecialCharacters(aMatches[0])
            return (True, aMatches[0])
        return (False, aMatches)

    @staticmethod
    def __replaceSpecialCharacters(s):
        s = s.replace('\\/', '/').replace('&amp;', '&').replace('\\u00c4', 'Ä').replace('\\u00e4', 'ä')
        s = s.replace('\\u00d6', 'Ö').replace('\\u00f6', 'ö').replace('\\u00dc', 'Ü').replace('\\u00fc', 'ü')
        s = s.replace('\\u00df', 'ß').replace('\\u2013', '-').replace('\\u00b2', '²').replace('\\u00b3', '³')
        s = s.replace('\\u00e9', 'é').replace('\\u2018', '‘').replace('\\u201e', '„').replace('\\u201c', '“')
        s = s.replace('\\u00c9', 'É').replace('\\u2026', '...').replace('\\u202fh', 'h').replace('\\u2019', '’')
        s = s.replace('\\u0308', '̈').replace('\\u00e8', 'è').replace('#038;', '').replace('\\u00f8', 'ø')
        s = s.replace('／', '/').replace('\\u00e1', 'á').replace('&#8211;', '-').replace('&#8220;', '“').replace('&#8222;', '„')
        s = s.replace('&#8217;', '’').replace('&#8230;', '…').replace('&#039;', "'")
        return s

    @staticmethod
    def parse(sHtmlContent, pattern, iMinFoundValue=1, ignoreCase=False):
        sHtmlContent = cParser.__replaceSpecialCharacters(sHtmlContent)
        if ignoreCase:
            aMatches = re.compile(pattern, re.DOTALL | re.I).findall(sHtmlContent)
        else:
            aMatches = re.compile(pattern, re.DOTALL).findall(sHtmlContent)
        if len(aMatches) >= iMinFoundValue:
            return (True, aMatches)
        return (False, aMatches)

    @staticmethod
    def replace(pattern, sReplaceString, sValue):
        return re.sub(pattern, sReplaceString, sValue)

    @staticmethod
    def search(sSearch, sValue):
        return re.search(sSearch, sValue, re.IGNORECASE)

    @staticmethod
    def escape(sValue):
        return re.escape(sValue)

    @staticmethod
    def getNumberFromString(sValue):
        pattern = '\\d+'
        aMatches = re.findall(pattern, sValue)
        if len(aMatches) > 0:
            return int(aMatches[0])
        return 0

    @staticmethod
    def urlparse(sUrl):
        return urlparse(sUrl).netloc.title()

    @staticmethod
    def urlDecode(sUrl):
        return unquote(sUrl)

    @staticmethod
    def urlEncode(sUrl, safe=''):
        return quote(sUrl, safe)

    @staticmethod
    def unquotePlus(sUrl):
        return unquote_plus(sUrl)

    @staticmethod
    def quotePlus(sUrl):
        return quote_plus(sUrl)

    @staticmethod
    def B64decode(text):
        import base64
        if sys.version_info[0] == 2:
            b = base64.b64decode(text)
        else:
            b = base64.b64decode(text).decode('utf-8')
        return b


class logger:
    @staticmethod
    def info(sInfo):
        if sys.version_info[0] == 2:
            logger.__writeLog(sInfo, cLogLevel=xbmc.LOGNOTICE)
        else:
            logger.__writeLog(sInfo, cLogLevel=xbmc.LOGINFO)

    @staticmethod
    def debug(sInfo):
        logger.__writeLog(sInfo, cLogLevel=xbmc.LOGDEBUG)

    @staticmethod
    def error(sInfo):
        logger.__writeLog(sInfo, cLogLevel=xbmc.LOGERROR)

    @staticmethod
    def fatal(sInfo):
        logger.__writeLog(sInfo, cLogLevel=xbmc.LOGFATAL)

    @staticmethod
    def __writeLog(sLog, cLogLevel=xbmc.LOGDEBUG):
        params = ParameterHandler()
        try:
            if sys.version_info[0] == 2:
                if isinstance(sLog, unicode):
                    sLog = '%s (ENCODED)' % (sLog.encode('utf-8'))
            if params.exist('site'):
                site = params.getValue('site')
                sLog = "\t[%s] -> %s: %s" % (common.addonName, site, sLog)
            else:
                sLog = "\t[%s] %s" % (common.addonName, sLog)
            xbmc.log(sLog, cLogLevel)
        except Exception as e:
            xbmc.log('Logging Failure: %s' % (e), cLogLevel)
            pass


class cUtil:
    @staticmethod
    def removeHtmlTags(sValue, sReplace=''):
        p = re.compile(r'<.*?>')
        return p.sub(sReplace, sValue)

    @staticmethod
    def unescape(text):
        def fixup(m):
            text = m.group(0)
            if not text.endswith(';'): text += ';'
            if text[:2] == '&#':
                try:
                    if text[:3] == '&#x':
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                try:
                    text = unichr(name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text

        if isinstance(text, str):
            try:
                text = text.decode('utf-8')
            except:
                try:
                    text = text.decode('utf-8', 'ignore')
                except:
                    pass
        return re.sub("&(\\w+;|#x?\\d+;?)", fixup, text.strip())

    @staticmethod
    def cleanse_text(text):
        if text is None: text = ''
        text = cUtil.removeHtmlTags(text)
        if sys.version_info[0] == 2:
            text = cUtil.unescape(text)
            if isinstance(text, unicode):
                text = text.encode('utf-8')
        return text

    @staticmethod
    def evp_decode(cipher_text, passphrase, salt=None):
        if not salt:
            salt = cipher_text[8:16]
            cipher_text = cipher_text[16:]
        key, iv = cUtil.evpKDF(passphrase, salt)
        decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(key, iv))
        plain_text = decrypter.feed(cipher_text)
        plain_text += decrypter.feed()
        return plain_text.decode("utf-8")

    @staticmethod
    def evpKDF(pwd, salt, key_size=32, iv_size=16):
        temp = b''
        fd = temp
        while len(fd) < key_size + iv_size:
            h = hashlib.md5()
            h.update(temp + pwd + salt)
            temp = h.digest()
            fd += temp
        key = fd[0:key_size]
        iv = fd[key_size:key_size + iv_size]
        return key, iv
