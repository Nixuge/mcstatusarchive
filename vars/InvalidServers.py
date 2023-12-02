class InvalidServers:
    MARK_INVALID_AFTER: int = 30 # How many failed attemps in a row to mark the server as invalid.
    RETRY_INVALID_EVERY: int = 10 # How many passes between each attempt for invalid servers

    servers_fails_noncritical: dict[str, int] # servers that have had x failed attemps in a row 
    invalid_servers:  list[str] # servers past MARK_INVALID_AFTER failed attemps in a row (ends up here = removed from the dict above)
    def __init__(self) -> None:
        self.servers_fails_noncritical = {}
        self.invalid_servers = []
    
    def is_invalid(self, server: str):
        return server in self.invalid_servers

    def mark_server_valid(self, server: str):
        self.servers_fails_noncritical.pop(server, None)
        if server in self.invalid_servers:
            self.invalid_servers.remove(server)
    
    # Returns number of failed attemps in a row
    def add_server_fail(self, server: str):
        # already invalidated
        if server in self.invalid_servers: 
            return self.MARK_INVALID_AFTER
        # nonexistent (=create key in dict)
        if not server in self.servers_fails_noncritical.keys():
            self.servers_fails_noncritical[server] = 1
            return 1
        
        # otherwise if exists
        current_fails = self.servers_fails_noncritical[server]
        new_fails = current_fails + 1
        if new_fails >= self.MARK_INVALID_AFTER: # above invalid mark
            self.invalid_servers.append(server)
            self.servers_fails_noncritical.pop(server)
        else: # below invalid mark
            self.servers_fails_noncritical[server] = new_fails
        return new_fails


INVALID_JAVA_SERVERS = InvalidServers()
# INVALID_BEDROCK_SERVERS = InvalidServers() # not yet used !