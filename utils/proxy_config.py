# =============================================================================
# PROXY CONFIGURATION
# =============================================================================
# Edit this file to add your proxy settings.
# Proxies are OPTIONAL - set USE_PROXIES = False to disable.
# =============================================================================

# Enable/Disable proxy usage
USE_PROXIES = False  # Set to True when you have proxies configured

# =============================================================================
# PROXY LIST (Simple format: IP:PORT)
# =============================================================================
# Add your proxies here - one per Firefox instance
# Example: ["1.1.1.1:8080", "2.2.2.2:8080", "3.3.3.3:8080", "4.4.4.4:8080"]

PROXY_LIST = [
    # "proxy1_ip:port",
    # "proxy2_ip:port",
    # "proxy3_ip:port",
    # "proxy4_ip:port",
]

# =============================================================================
# AUTHENTICATED PROXIES (Format: username:password@ip:port)
# =============================================================================
# If your proxies require authentication, use this format instead.
# Note: Requires selenium-wire package (pip install selenium-wire)

USE_AUTHENTICATED_PROXIES = False  # Set to True if using auth proxies

AUTHENTICATED_PROXY_LIST = [
    # {
    #     "http": "http://username:password@ip:port",
    #     "https": "https://username:password@ip:port",
    #     "no_proxy": "localhost,127.0.0.1"
    # },
    # Add more proxy configs as needed...
]

# =============================================================================
# SINGLE PROXY MODE (All browsers use same proxy)
# =============================================================================
# If you only have one proxy, enable this and all Firefox instances will use it

USE_SINGLE_PROXY = False
SINGLE_PROXY = {
    "http": "",      # e.g., "http://1.1.1.1:8080" or "http://user:pass@1.1.1.1:8080"
    "https": "",     # e.g., "https://1.1.1.1:8080"
    "no_proxy": "localhost,127.0.0.1"
}

# =============================================================================
# HELPER FUNCTION TO GET PROXY FOR INSTANCE
# =============================================================================
def get_proxy_for_instance(instance_id):
    """
    Returns proxy config for a given Firefox instance.
    instance_id: 0-indexed instance number
    Returns: proxy string or None if no proxy
    """
    if not USE_PROXIES:
        return None
    
    if USE_SINGLE_PROXY:
        return SINGLE_PROXY if SINGLE_PROXY.get("http") else None
    
    if USE_AUTHENTICATED_PROXIES:
        if instance_id < len(AUTHENTICATED_PROXY_LIST):
            return AUTHENTICATED_PROXY_LIST[instance_id]
        return None
    
    # Simple proxy list
    if instance_id < len(PROXY_LIST):
        return PROXY_LIST[instance_id]
    return None
