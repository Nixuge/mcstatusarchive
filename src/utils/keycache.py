# Note: This class is unused in code rn. It was meant to find which properties in the status responses were unused.
# Keeping it just in case i need it again.

from mcstatus.responses import JavaStatusResponse


class KeyCache:
    cache: dict[str, dict[tuple, str]] = {}
    

def key_checker(ip: str, status: JavaStatusResponse):
    raw = status.raw
    
    unknown: dict[tuple, str] = {}
    
    for key in raw.keys():
        if key not in ("players", "version", "modinfo", "forgeData", "description", "favicon", "enforcesSecureChat",):
                       
                    #    "preventsChatReports", "previewsChat", "isModded", "betterStatus", "cosmic"):
            unknown[(key,)] = raw[key]
    
    # Unimplemented
    # bs = raw.get("betterStatus", {}) # pyright: ignore[reportGeneralTypeIssues]
    # for key in bs.keys():
    #     if key not in ("name", "isMetaData", "version"):
    #         unknown[("betterStatus", key)] = bs[key]
    
    # c = raw.get("cosmic", {}) # pyright: ignore[reportGeneralTypeIssues]
    # for key in c.keys():
    #     if key not in ("proxy"):
    #         unknown[("cosmic", key)] = c[key]
    
    # Implemented
    p = raw["players"]
    for key in p.keys():
        if key not in ("max", "online", "sample"):
            unknown[("players", key)] = p[key]
    
    v = raw["version"]
    for key in v.keys():
        if key not in ("protocol", "name"):
        # if key not in ("protocol", "name", "supportedVersions"): # supportedVersions is unimplemented
            unknown[("version", key)] = v[key]
    
    m = raw.get("modinfo", {})
    if m:
        for key in m.keys():
            if key not in ("modList", "type"):
                unknown[("version", key)] = m[key]
    
    m2 = raw.get("forgeData", {})
    if m2:
        for key in m2.keys():
            if key not in ("modList", "type", "fmlNetworkVersion", "d"):
                unknown[("version", key)] = m2[key]
        
    KeyCache.cache[ip] = unknown
