# Todas estas mensagens de erro são falsos positivos do bandit
# Em resumo, ele acha que estamos vazando uma senha por ter "TOKEN"
# ou algo parecido no nome da variável.

INVALID_TOKEN_MESSAGE = "Invalid Firebase token"  # nosec B105
EXPIRED_TOKEN_MESSAGE = "Expired Firebase token"  # nosec B105
REVOKED_TOKEN_MESSAGE = "Revoked Firebase token"  # nosec B105
USER_DISABLED_MESSAGE = "Firebase user is disabled"  # nosec B105
CERTIFICATE_FETCH_MESSAGE = "Firebase signing key could not be fetched"  # nosec B105
CONFIGURATION_NOT_FOUND_MESSAGE = "Firebase configuration was not found"  # nosec B105
UNEXPECTED_RESPONSE_MESSAGE = "Firebase returned an unexpected response"  # nosec B105
SESSION_COOKIE_SIGN_ERROR_MESSAGE = "Session cookie could not be signed"  # nosec B105
INVALID_SESSION_COOKIE_MESSAGE = "Invalid Firebase session cookie"  # nosec B105
EXPIRED_SESSION_COOKIE_MESSAGE = "Expired Firebase session cookie"  # nosec B105
REVOKED_SESSION_COOKIE_MESSAGE = "Revoked Firebase session cookie"  # nosec B105
