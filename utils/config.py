import os

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Excel Paths
SENDER_EXCEL_PATH = os.path.join(DATA_DIR, "sender_list.xlsx")
RECIPIENT_EXCEL_PATH = os.path.join(DATA_DIR, "recipient_list.xlsx")

# Timeouts
DEFAULT_TIMEOUT = 10
LONG_TIMEOUT = 30
SHORT_TIMEOUT = 5

# Browser Config
BROWSER_NAME = "firefox"
HEADLESS = False
DETACH = True
INCOGNITO = True

# Multi-Firefox Parallel Config
PARALLEL_FIREFOX_INSTANCES = 4  # Number of Firefox browsers to run simultaneously
STAGGER_DELAY_MIN = 2  # Minimum seconds between each browser launch
STAGGER_DELAY_MAX = 5  # Maximum seconds between each browser launch

# Mail Sender Config
FIXED_TO_EMAIL = "zoedebtcollector@gmail.com"

# Browser Paths configuration
# Users can update these paths to match their system installation
BROWSER_PATHS = {
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ],
    "firefox": [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ],
    "brave": [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
    ],

    "vivaldi": [
        rf"C:\Users\{os.getlogin()}\AppData\Local\Vivaldi\Application\vivaldi.exe",
        r"C:\Program Files\Vivaldi\Application\vivaldi.exe"
    ]
}
