RESPONSE_400 = {
    "description": "Bad Request",
    "content": {
        "application/json": {
            "example": {
                "detail": "Your request could not be understood"
            }
        }
    }
}

RESPONSE_401 = {
    "description": "Unauthorized",
    "content": {
        "application/json": {
            "example": {"detail": "Authentication required"}
        }
    }
}

RESPONSE_403 = {
    "description": "Forbidden",
    "content": {
        "application/json": {
            "example": {
                "detail": "You do not have permission to perform this action"
            }
        }
    }
}

RESPONSE_404 = {
    "description": "Not Found",
    "content": {
        "application/json": {
            "example": {
                "detail": "Item not found"
            }
        }
    }
}

RESPONSE_405 = {
    "description": "Method Not Allowed",
    "content": {
        "application/json": {
            "example": {
                "detail": "HTTP method not allowed on this endpoint"
            }
        }
    }
}

RESPONSE_408 = {
    "description": "Request Timeout",
    "content": {
        "application/json": {
            "example": {
                "detail": "Request timed out"
            }
        }
    }
}

RESPONSE_409 = {
    "description": "Conflict",
    "content": {
        "application/json": {
            "example": {
                "detail": "Resource conflict"
            }
        }
    }
}

RESPONSE_500 = {
    "description": "Internal Server Error",
    "content": {
        "application/json": {
            "example": {
                "detail": "An unexpected error occurred"
            }
        }
    }
}

RESPONSE_501 = {
    "description": "Not Implemented",
    "content": {
        "application/json": {
            "example": {
                "detail": "This endpoint is not implemented"
            }
        }
    }
}
