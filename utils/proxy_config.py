# =============================================================================
# PROXY CONFIGURATION
# =============================================================================
# Edit this file to add your proxy settings.
# Proxies are OPTIONAL - set USE_PROXIES = False to disable.
# =============================================================================

# Enable/Disable global proxy usage
USE_PROXIES = True

# =============================================================================
# MODE CONFIGURATION
# =============================================================================
# SYSTEM MODE: ONE PROXY PER INSTANCE (Best for bulk mail)
USE_SINGLE_PROXY = False            # MUST be False for per-instance proxies
USE_AUTHENTICATED_PROXIES = False   # Check if you have user:pass proxies

# =============================================================================
# PROXY LIST (Simple format: IP:PORT)
# =============================================================================
# Add your proxies here - one per Firefox instance
# Format: "IP:PORT" (e.g., "127.0.0.1:8080")

PROXY_LIST = [
    "192.168.1.10:8000",
    "192.168.1.11:8000",
    
    # Add more IPs here if you have more instances...
]

# =============================================================================
# ADVANCED / UNUSED CONFIGURATIONS
# =============================================================================

# [UNUSED in Mode 2] Authenticated Proxies
AUTHENTICATED_PROXY_LIST = [
    {
        "http": "http://username:password@ip:port",
        "https": "https://username:password@ip:port",
        "no_proxy": "localhost,127.0.0.1"
    },
]

# [UNUSED in Mode 2] Single Proxy Default
SINGLE_PROXY = {
    "http": "http://username:password@ip:port",
    "https": "https://username:password@ip:port",
    "no_proxy": "localhost,127.0.0.1"
}

# =============================================================================
# HELPER FUNCTION
# =============================================================================
def get_proxy_for_instance(instance_id):
    """
    Returns proxy config for a given Firefox instance.
    """
    if not USE_PROXIES:
        return None
    
    # 1. Single Proxy Mode
    if USE_SINGLE_PROXY:
        return SINGLE_PROXY if SINGLE_PROXY.get("http") else None
    
    # 2. Authenticated Proxy Mode
    if USE_AUTHENTICATED_PROXIES:
        if instance_id < len(AUTHENTICATED_PROXY_LIST):
            return AUTHENTICATED_PROXY_LIST[instance_id]
        return None
    
    # 3. Standard List Mode (Targeted)
    if instance_id < len(PROXY_LIST):
        return PROXY_LIST[instance_id]
    
    return None
