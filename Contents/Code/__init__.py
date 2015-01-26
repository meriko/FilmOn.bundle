from hashlib import md5

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
def ValidatePrefs():
    if Prefs['login'] and Prefs['email'] and Prefs['password']:
        Dict.Reset()
        Dict['Login'] = True
    
        [sessionKey, loginStatus] = GetSessionParameters()
    
        if loginStatus:
            return ObjectContainer(
                header = "Login success",
                message = "Successfully logged in"
            )
        else:
            return ObjectContainer(
                header = "Login failure",
                message = "Invalid username or password.\r\nPlease note that the account must include a paid subscription"
            )
    
###################################################################################################
@handler(PREFIX, TITLE, thumb = ICON, art = ART)
def MainMenu():

    try:
        if Prefs['custom']:
            try:
                data = XML.ObjectFromString(Resource.Load('custom.xml'))
                Log("Using custom layout")
                return Custom(data)
            except:
                Log("Preference to use custom layout, but custom.xml file not found or corrupt!")
        else:
            Log("Using standard layout")  
    except:
        Log("Attempted to use custom layout but something went wrong. Using standard layout ...")

    oc = ObjectContainer()

    oc.add(
        PrefsObject(
            title = 'Preferences',
            summary = 'Set email and password to get access to HD streams\r\nSign up for an account at www.filmon.com'
        )
    )

    [sessionKey, loginStatus] = GetSessionParameters()
    
    if loginStatus:
        title = 'Favorites'
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        Favorites,
                        title = title
                    ),
                title = title,
                thumb = 'http://www.filmon.com/tv/themes/filmontv/images/category/favorites_stb.png'
            )
        )
        
        title = 'Recordings'
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        Recordings,
                        title = title
                    ),
                title = title 
            )
        )
    
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
@route(PREFIX + '/custom')
def Custom(data):
    oc = ObjectContainer()

    [sessionKey, loginStatus] = GetSessionParameters()
    channelsInfo = JSON.ObjectFromURL(API_BASE_URL + "channels" + "?session_key=" + sessionKey)
    
    for custom_channel in data.xpath("//Channels/Channel/@name"):
        for channel in channelsInfo:
            if custom_channel.lower().strip() == channel["title"].lower().strip():
                
                oc.add(
                    EpisodeObject(
                        url = API_BASE_URL + "channel/" + channel["id"] + "?session_key=" + sessionKey,
                        title = channel["title"],
                        thumb = channel["big_logo"].replace("big_logo", "extra_big_logo")
                    )
                )

    oc.add(
        PrefsObject(
            title = 'Preferences',
            summary = 'Set email and password to get access to HD streams\r\nSign up for an account at www.filmon.com'
        )
    )

    return oc    

####################################################################################################
@route(PREFIX + '/favorites')
def Favorites(title):
    oc = ObjectContainer(title2 = title)

    [sessionKey, loginStatus] = GetSessionParameters()
    group = JSON.ObjectFromURL(API_BASE_URL + "favorites?session_key=%s&run=get" % sessionKey)
    
    for field in group['result']:
        channel = JSON.ObjectFromURL(API_BASE_URL + "channel/%s?session_key=%s" % (field['channel_id'], sessionKey))
        
        oc.add(
            EpisodeObject(
                url = API_BASE_URL + "channel/" + str(channel["id"]) + "?session_key=" + sessionKey,
                title = channel["title"],
                thumb = channel["big_logo"].replace("big_logo", "extra_big_logo")
            )
        )
    
    if len(oc) < 1:
        oc.header  = "Sorry"
        oc.message = "No favorites found! Add your favorites on www.filmon.com"
    
    return oc
    
####################################################################################################
@route(PREFIX + '/recordings')
def Recordings(title):
    oc = ObjectContainer(title2 = title)

    [sessionKey, loginStatus] = GetSessionParameters()
    data = JSON.ObjectFromURL(API_BASE_URL + "dvr/list?session_key=%s&format=json" % sessionKey)
    
    for recording in data['recordings']:
        if recording['status'] != 'Recorded':
            continue
        
        oc.add(
            CreateVideoClipObject(
                url = recording["stream_url"],
                title = recording["title"],
                summary = recording["description"],
                duration = int(recording['length']) * 1000,
                thumb = 'http://static.filmon.com/couch/channels/%s/extra_big_logo.png' % recording['channel_id']
            )
        )
    
    if len(oc) < 1:
        oc.header  = "Sorry"
        oc.message = "No recordings found! Add your recordings on www.filmon.com"
    
    return oc

####################################################################################################
@route(PREFIX + '/channels')
def Channels(title, id):
    oc = ObjectContainer(title2 = title)
    
    [sessionKey, loginStatus] = GetSessionParameters()
    channelsInfo = JSON.ObjectFromURL(API_BASE_URL + "channels" + "?session_key=" + sessionKey)
    
    for channel in channelsInfo:
        if id == channel["group_id"] and (not Prefs['onlyfree'] or channel['is_free_sd_mode'] == '1'):
            oc.add(
                EpisodeObject(
                    url = API_BASE_URL + "channel/" + channel["id"] + "?session_key=" + sessionKey,
                    title = channel["title"],
                    thumb = channel["big_logo"].replace("big_logo", "extra_big_logo")
                )
            )   
    
    
    if len(oc) < 1:
        oc.header  = "Sorry"

        if Prefs['onlyfree']:
            oc.message = "No free channels found! You can preview channels in this group by changing the preference 'Only show free channels'"
        else:
            oc.message = "No channels found!"
    
    return oc

####################################################################################################
@route(PREFIX + '/createvideoclipobject', duration = int, include_container = bool)
def CreateVideoClipObject(url, title, summary, duration, thumb, include_container = False):
    vco = VideoClipObject(
        key =
            Callback(
                CreateVideoClipObject,
                url = url,
                title = title,
                summary = summary,
                duration = duration,
                thumb = thumb,
                include_container = True
            ),
        rating_key = url,
        title = title,
        thumb = thumb,
        summary = summary,
        duration = duration,
        items = [
            MediaObject(
                parts = [
                    PartObject(key = HTTPLiveStreamURL(url = url))
                ],
                video_resolution = 'sd',
                audio_channels = 2
            )
        ]
    )
    
    if include_container:
        return ObjectContainer(objects = [vco])
    else:
        return vco

####################################################################################################
def GetSessionParameters():
    # Here we utilize the HTTP cache, which is set to API session timeout
    # i.e if/when the current session times out, we automatically get a new
    # session key. If within the time out period, the cache function will
    # return the current key
    #
    # Since no event when a client is exiting the plugin exist(?), the keep-alive
    # request can not be used by this plugin since the server would
    # request keep-alive forever(and thus building up numerous API sessions)...
    sessionInfo = JSON.ObjectFromURL(API_BASE_URL + "init?channelProvider=ipad&app_id=iphone-html5&app_secret=%s&supported_streaming_protocol=livehttp" % String.Decode('JTVCZXFnYnBsZg__'))
    sessionKey  = sessionInfo["session_key"]
    
    if 'Login' in Dict:
        if not Login(sessionKey):
            # If a login fail, we will only retry if the preferences are
            # changed/updated
            del Dict['Login']
    else:
        Log('No login attempted')
    
    return [sessionKey, 'Login' in Dict]

####################################################################################################
def Login(sessionKey):
    if Prefs['login'] and Prefs['email'] and Prefs['password']:
        postData               = {}
        postData['login']      = Prefs['email']
        postData['password']   = md5(Prefs['password']).hexdigest()
        postData['sessionkey'] = sessionKey

        try:        
            loginURL = API_BASE_URL + 'login' + "?session_key=" + sessionKey
            content  = HTTP.Request(url = loginURL, values = postData).content
            Log('Successfully logged in!')
            return True
        except:
            Log('Login failed!')
            return False
    else:
        Log('Attempted to login but not all required settings are set')
        return True
