
class BannedFromRoomException(Exception):
    # Raised when the user is banned from the room
    pass

class RoomNotFoundException(Exception):
    # Raised when the room is not found
    pass

class KickedFromRoomException(Exception):
    # Raised when the user is kicked from the room
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class RoomLookupFailedException(Exception):
    # Raised when the room lookup fails
    def __init__(self, message):
        super().__init__(message)
        self.message = message