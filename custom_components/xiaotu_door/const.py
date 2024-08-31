"""Constants for the XiaoTu Door integration."""

import datetime

DOMAIN = "xiaotu_door"

CONF_ACCOUNT = "account"
CONF_REFRESH_TOKEN = "refresh_token"

DEFAULT_API_HOST = "https://wap.anjucloud.com"
X_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/6.8.0(0x16080000) NetType/WIFI MiniProgramEnv/Mac MacWechat/WMPF MacWechat/3.8.7(0x13080710) XWEB/1191"
HTTPX_TIMEOUT = 30.0

AUTH_VALID_OFFSET = datetime.timedelta(hours=5)
EXPIRES_AT_OFFSET = datetime.timedelta(seconds=HTTPX_TIMEOUT * 2)
