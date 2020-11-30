# -*- coding: utf-8 -*-
import sys, os, xbmcaddon, xbmcgui

AddonName = xbmcaddon.Addon().getAddonInfo('name')
if sys.version_info[0] == 2:
    from xbmc import translatePath
    NIGHTLY_VERSION_CONTROL = os.path.join(translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8'), "update_sha")
else:
    from xbmcvfs import translatePath
    NIGHTLY_VERSION_CONTROL = os.path.join(translatePath(xbmcaddon.Addon().getAddonInfo('profile')), "update_sha")


def infoDialog(message, heading=AddonName, icon='', time=5000, sound=False):
    if icon == '': icon = xbmcaddon.Addon().getAddonInfo('icon')
    elif icon == 'INFO': icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING': icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR': icon = xbmcgui.NOTIFICATION_ERROR
    xbmcgui.Dialog().notification(heading, message, icon, time, sound=sound)


if os.path.isfile(NIGHTLY_VERSION_CONTROL) == False or xbmcaddon.Addon().getSetting('DevUpdateAuto') == 'true' or xbmcaddon.Addon().getSetting('enforceUpdate') == 'true':
    from resources.lib import updateManager
    status = updateManager.devAutoUpdates(True)
    if status == True: infoDialog("Auto Update abgeschlossen", sound=False, icon='INFO', time=3000)
    if status == False: infoDialog("Auto Update mit Fehler beendet", sound=True, icon='ERROR')
    # if status == None: infoDialog("Keine neuen Updates gefunden", sound=False, icon='INFO', time=3000)
    if xbmcaddon.Addon().getSetting('enforceUpdate') == 'true': xbmcaddon.Addon().setSetting('enforceUpdate', 'false')

# "setting.xml" wenn notwendig Indexseiten aktualisieren
try:
    if xbmcaddon.Addon().getSetting('newSetting') == 'true':
        from resources.lib.handler.pluginHandler import cPluginHandler
        cPluginHandler().getAvailablePlugins()
except:
    pass
