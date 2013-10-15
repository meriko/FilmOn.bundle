TITLE               = 'FilmOn'
PREFIX              = '/video/filmon'
ART                 = 'art-default.jpg'
ICON                = 'icon-default.png'
API_BASE_URL        = 'http://www.filmon.com/tv/api/'
USER_AGENT          = "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25"
API_SESSION_TIMEOUT = 300 - 1  # seconds, 300 = according to API spec, - 1 = margin

###################################################################################################

def Start():
	# Set the default ObjectContainer attributes
	ObjectContainer.title1 = TITLE
	ObjectContainer.art    = R(ART)

	# Set the default cache time and user agent
	HTTP.CacheTime             = API_SESSION_TIMEOUT
	HTTP.Headers['User-agent'] = USER_AGENT

###################################################################################################
@handler(PREFIX, TITLE, thumb = ICON, art = ART)
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
@route(PREFIX + '/channels')
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
	sessionInfo = JSON.ObjectFromURL(API_BASE_URL + "init?channelProvider=ipad&app_id=iphone-html5&app_secret=%5Beqgbplf&supported_streaming_protocol=livehttp")
	sessionKey  = sessionInfo["session_key"]
    
	return sessionKey


