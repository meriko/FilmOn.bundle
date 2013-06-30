from threading import Timer # Is there a Plex Framework equivalent?

TITLE               = 'FilmOn'
ART                 = 'art-default.jpg'
ICON                = 'icon-default.png'
BASE_URL            = 'http://ww.filmon.com'
API_BASE_URL        = 'http://www.filmon.com/tv/api/'
USER_AGENT          = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"
API_SESSION_TIMEOUT = 300 - 1  # seconds, 300 = according to API spec, - 1 = margin

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
	HTTP.CacheTime             = API_SESSION_TIMEOUT
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
							title = group["title"].title(), 
							id = group["group_id"]
					),
				title = group["title"].title(), 
				thumb = group["logo_148x148_uri"],
				summary = group["description"]
			)
		) 
	
	return oc

####################################################################################################
@route('/video/filmon/channels')
def Channels(title, id):
	oc = ObjectContainer(title1 = title)
	
	sessionKey   = GetSessionKey()
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
	# Here we utilize the HTTP cache, which is set to API session timeout
	# i.e if/when the current session times out, we automatically get a new
	# session key. If within the time out period, the cache function will
	# return the current key
	#
	# Since no event when a client is exiting the plugin exist(?), the keep-alive
	# request can not be used by this plugin since the server would
	# request keep-alive forever(and thus building up numerous API sessions)...
	sessionInfo = JSON.ObjectFromURL(API_BASE_URL + "init")
	sessionKey  = sessionInfo["session_key"]
    
	return sessionKey

	
