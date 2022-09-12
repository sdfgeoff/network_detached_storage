class _Config:
    STORAGE: str = "SQLITE"
    WEBSERVER_PORT: int = 8080

    WEBSERVER_BUFFER_SEND_MS: int = (
        10  # Time to wait between sending large chunks of page data
    )
    WEBSERVER_CLIENT_TIMEOUT_MS: int = (
        1000  # Max time for a client to ack transmitting data
    )


config = _Config()
