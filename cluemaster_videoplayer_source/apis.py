
api_initial = "https://deviceapi.cluemaster.io"
# dev-api_initial = "https://dev-deviceapi.cluemaster.io"

# master apis
DEVICES_FILES_API = api_initial + "/api/Device/GetDeviceFiles/{device_unique_code}"
GENERATE_API_TOKEN_API = api_initial + "/api/Auth/PostGenerateApiKey"
ROOM_INFO_API = api_initial + "/api/Device/GetRoomInfo/{device_unique_code}"
DEVICE_REQUEST_API = api_initial + "/api/Device/GetDeviceRequest/{device_unique_code}"
POST_DEVICE_API = api_initial + "/api/Device/{device_unique_code}/{deviceRequestId}"
GET_TIMER_REQUEST = api_initial + "/api/Device/GetTimerRequest/{}"
GET_GAME_START_END_TIME = api_initial + "/api/Device/GetGameTimerStartEndTime/{}"
GAME_DETAILS_API = api_initial + "/api/Device/GetGameDetails/{}"
GAME_INTRO_REQUEST = api_initial + "/api/Device/GetGameIntroRequest/{}"
GET_GAME_TIMER = api_initial + "/api/Device/GetGameTimer/{}"
POST_GAME_CLUE_STATUS = api_initial + "/api/Device/PostGameClueStatus/{game_ids}/{clue_ids}"
IDENTIFY_DEVICE_API = api_initial + "/api/Device/IdentifyDevice/{device_unique_code}"
GET_SHUTDOWN_RESTART_REQUEST = api_initial + "/api/Device/GetShutdownRestartRequest/{unique_code}"
GET_GAME_CLUE_API = api_initial + "/api/Device/GetGameClue/{initial_gameId}"
POST_GAME_CLUE = api_initial + "/api/Device/PostGameClue/{gameId}/{gameClueId}"
DOWNLOAD_FILES_REQUEST = api_initial + "/api/Device/DownloadFilesRequest/{unique_code}"
GET_DEVICE_EXIST = api_initial + "/api/Device/GetDeviceExist/{unique_code}"
GET_VIDEO_PLAYER_FILES_API = api_initial + "/api/Device/GetVideoPlayerFiles/{device_unique_code}"
