from threading import Timer # Is there a Plex Framework equivalent?

TITLE               = 'FilmOn'
ART                 = 'art-default.jpg'
ICON                = 'icon-default.png'
BASE_URL            = 'http://ww.filmon.com'
API_BASE_URL        = 'http://www.filmon.com/tv/api/'
USER_AGENT          = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"
KEEP_ALIVE_INTERVAL = 60.0  #seconds

###################################################################################################

def Start():
	Plugin.AddPrefixHandler('/video/filmon', MainMenu, TITLE, ICON, ART)
	Plugin.AddViewGroup('List', viewMode = 'List', mediaType = 'items')

	# Set the default ObjectContainer attributes
	ObjectContainer.title1     = TITLE
	ObjectContainer.view_group = 'List'
	ObjectContainer.art        = R(ART)

	# Default icons for DirectoryObject and VideoClipObject in case there isn't an image
	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art   = R(ART)
	VideoClipObject.thumb = R(ICON)
	VideoClipObject.art   = R(ART)

	# Set the default cache time
	HTTP.CacheTime             = 300
	HTTP.Headers['User-agent'] = USER_AGENT

###################################################################################################
def MainMenu():
	oc = ObjectContainer()
	
	sessionKey = GetSessionKey()
		
	groupsInfo = JSON.ObjectFromURL(API_BASE_URL + "groups" + "?session_key=" + sessionKey)
	
	for group in groupsInfo:
		oc.add(
			DirectoryObject(
				key = 
					Callback(
						Channels, 
							title = group["title"], 
							id = group["group_id"], 
							sessionKey = sessionKey
					),
				title = group["title"], 
				thumb = group["logo_148x148_uri"],
				summary = group["description"]
			)
		) 
	
	return oc

####################################################################################################
@route('/video/filmon/channels')
def Channels(title, id, sessionKey):
	oc = ObjectContainer(title1 = title)
	
	channelsInfo = JSON.ObjectFromURL(API_BASE_URL + "channels" + "?session_key=" + sessionKey)
						
	for channel in channelsInfo:
		if id == channel["group_id"]:
			oc.add(
				EpisodeObject(
					url = API_BASE_URL + "channel/" + channel["id"] + "?session_key=" + sessionKey,
					title = channel["title"],
					thumb = channel["big_logo"].replace("big_logo", "extra_big_logo")
				)
			)	
		
	return oc

####################################################################################################
def GetSessionKey():
	sessionInfo = JSON.ObjectFromURL(API_BASE_URL + "init", cacheTime = 0)
	sessionKey  = sessionInfo["session_key"]
	
	t = Timer(KEEP_ALIVE_INTERVAL, KeepAlive, [sessionKey])
	t.start()
    
	return sessionKey

####################################################################################################
def KeepAlive(sessionKey):
	dummy = HTML.ElementFromURL('http://www.filmon.com/api/keep-alive?session_key=' + sessionKey, cacheTime = 0)
	
	t = Timer(KEEP_ALIVE_INTERVAL, KeepAlive, [sessionKey])
	t.start()
	
