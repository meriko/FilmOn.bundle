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
    oc = ObjectContainer()

    oc.add(
        PrefsObject(
            title = 'Preferences',
            summary = 'Set email and password to get access to HD streams\r\nSign up for an account at www.filmon.com'
        )
    )

    [sessionKey, loginStatus] = GetSessionParameters()
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
