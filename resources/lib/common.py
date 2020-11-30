# -*- coding: utf-8 -*-
import xbmcaddon, sys
addonID = 'plugin.video.xstream'
addon = xbmcaddon.Addon(addonID)
addonName = addon.getAddonInfo('name')
if sys.version_info[0] == 2:
    from xbmc import translatePath
    addonPath = translatePath(addon.getAddonInfo('path')).decode('utf-8')
    profilePath = translatePath(addon.getAddonInfo('profile')).decode('utf-8')
else:
    from xbmcvfs import translatePath
    addonPath = translatePath(addon.getAddonInfo('path'))
    profilePath = translatePath(addon.getAddonInfo('profile'))
