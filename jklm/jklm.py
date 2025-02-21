import requests
import websocket

from enum import Enum

import base64
import random
import string
import time
import json

from .exceptions import BannedFromRoomException, KickedFromRoomException, RoomLookupFailedException, RoomNotFoundException, RoomConnectionException, RoomCreationException, RateLimitException

import threading
import logging

logging.basicConfig(level=logging.INFO)

class URLS(Enum):
    START_ROOM = "https://jklm.fun/api/startRoom"
    JOIN_ROOM = "https://jklm.fun/api/joinRoom"

def send_and_recv(ws, message):
    ws.send(message)
    return ws.recv()

def parse_socket_io_message(message):
    try:
        split = message.split("[", 1)
        code = split[0]
        
        data = json.loads("[" + split[1])

        return code, data
    except Exception as e:
        logging.error("Failed to parse message", message)

class RoomEntry:
    def __init__(self, beta, chatMode, details, gameId, isPublic, name, playerCount, roomCode) -> None:
        """
        Room entry object

        :param beta: Whether the room is in beta
        :param chatMode: The chat mode
        :param details: The details
        :param gameId: The game ID
        :param isPublic: Whether the room is public
        :param name: The name of the room
        :param playerCount: The player count
        :param roomCode: The room code
        """

        self.beta = beta
        self.chat_mode = chatMode
        self.details = details
        self.game_id = gameId
        self.is_public = isPublic
        self.name = name
        self.player_count = playerCount
        self.room_code = roomCode

class JKLM:
    def __init__(self, username: str, pfp: bytes = None, connection: dict = None, token: str = None, proxy: dict = None) -> None:
        """
        Initialize the JKLM client

        :param str username: The username to use
        :param bytes pfp: The profile picture to use (default None)
        :param str token: The token to use (default None)
        :param dict proxy: The proxy to use (default None)

        :example:

        >>> session = JKLM("username", "token", {
        >>>     "host": "proxy_host",
        >>>     "port": "proxy_port",
        >>>     "type": "proxy_type",
        >>>     "auth": ("proxy_username", "proxy_password")
        >>> })
        """
        
        # random 16 character token
        self.token = token or ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.username = username

        self.connection = connection
        self.has_pfp = pfp is not None

        if self.has_pfp:
            if (len(pfp) > 10_000):
                raise ValueError("Profile picture must be less than 10KB")

            self.pfp = pfp
            self.pfp_b64 = base64.b64encode(pfp).decode("utf-8")

        if len(self.username) > 20:
            raise ValueError("Username must be less than 20 characters")

        self.proxy = proxy

        self.proxy_host = None
        self.proxy_port = None
        self.proxy_type = None
        self.proxy_auth = None

        self.proxy = None
        self.proxies = None

        if (proxy):
            self.proxy_host = proxy["host"]
            self.proxy_port = proxy["port"]
            self.proxy_type = proxy["type"]
            self.proxy_auth = proxy["auth"]

            self.proxy = f"http://{self.proxy_auth[0]}:{self.proxy_auth[1]}@{self.proxy_host}:{self.proxy_port}"
            self.proxies = {
                "http": self.proxy,
                "https": self.proxy
            }

        self.chat_socket = websocket.WebSocket()
        self.game_socket = websocket.WebSocket()

        self.room = None
        self.reconnect_attempts = 0

    def get_room_server(self, roomId: str, retries: int = 0):
        """"
        Get the server for the given room

        :param str roomId: The room code
        :param int retries: The amount of retries (default 0)
        :param dict proxies: The proxies to use (default None)

        :return: The server for the room

        :example:

        >>> get_room_server("YKZA")
        """

        try:
            data = {
                "roomCode": roomId
            }

            res = requests.post(URLS.JOIN_ROOM.value, json=data, proxies=self.proxies)

            json = res.json()

            if "errorCode" in json:
                match json["errorCode"]:
                    case "noSuchRoom":
                        raise RoomNotFoundException("The room does not exist")
                    case _:
                        raise RoomLookupFailedException("Unknown error: " + json["errorCode"])

            if "url" not in json:
                return None
            return json["url"].split("/")[2]
        except Exception as e:
            if isinstance(e, RoomNotFoundException) or isinstance(e, RoomLookupFailedException):
                raise e

            return self.get_room_server(roomId, retries + 1) if retries < 5 else None

    def start_room(self, game_id: str, public: bool, room_name: str):
        """
        Start a room with the given parameters

        :param str game_id: The game to play (selector, popsauce, bombparty)
        :param boolean public: Whether the room is public
        :param str room_name: The name of the room

        :return: e.g { "url": "https://jklm.fun/room/YKZA", "roomCode": "YKZA" }

        :example:

        >>> session.start_room("popsauce", False, "Sigma Oasis")
        """

        if not isinstance(public, bool):
            raise ValueError("\"public\" must be a boolean")

        json = {
            "name": room_name, 
            "isPublic": public,
            "gameId": game_id, # selector, popsauce, bombparty
            "creatorUserToken": self.token
        }

        res = None
        retries = 0

        while not res and retries < 5:
            try:
                retries += 1
                res = requests.post(URLS.START_ROOM.value, json=json, proxies=self.proxies)
            except:
                pass

        if (res.status_code == 429):
            raise RateLimitException("Rate limited: " + res.text)

        if not res:
            raise RoomCreationException("Failed to create room")
        
        try:
            data = res.json()
        except:
            raise RoomCreationException("Failed to create room: " + res.text)

        return {
            "url": data["url"],
            "room_code": data["roomCode"]
        }

    def connect(self, room_id: str, grecaptcha_token: str = "", chat_handler: callable = None, game_handler: callable = None):
        """
        Connect to the given room

        :param str room_id: The room code
        :param str grecaptcha_token: The grecaptcha token (seems they have removed it but here incase it comes back)
        :param function chat_handler: The function to handle chat packets (default None)
        :param function game_handler: The function to handle game packets (default None)

        :return: None

        :example:

        >>> session.connect("YKZA", "grecaptcha_token", chat_handler, game_handler)
        """

        self.server = self.get_room_server(room_id)
        self.room_id = room_id

        self.chat_handler = chat_handler
        self.game_handler = game_handler

        self.connect_to_chat_socket(grecaptcha_token)
        self.connect_to_game_socket()

    def connect_to_chat_socket(self, grecaptcha_token):
        """
        Connect to the chat socket

        :param str grecaptcha_token: The grecaptcha token (seems they have removed it but here incase it comes back)

        :return: None

        :example:

        >>> session.connect_to_chat_socket()
        """

        ws = self.chat_socket
        ws.connect(f"wss://{self.server}/socket.io/?EIO=4&transport=websocket", http_proxy_host=self.proxy_host, http_proxy_port=self.proxy_port, http_proxy_auth=self.proxy_auth, http_proxy_type=self.proxy_type)
        
        # initialize chat socket

        ws.recv() # 0{"sid":"Tp2hb6M6o91cCgRGASbq","upgrades":[],"pingInterval":25000,"pingTimeout":20000,"maxPayload":1000000}
        res = send_and_recv(ws, "40") # 40{"sid":"bCBt0pqO0h66bkWaASbr"}
        
        # send "joinRoom" instruction

        payload = ["joinRoom",{
            "roomCode": self.room_id,
            "userToken": self.token,
            "nickname": self.username,
            "language": "en-US",
            "auth": self.connection,
            "picture": self.pfp_b64 if self.has_pfp else None,
        }]

        ws.send(f"420{json.dumps(payload)}")

        res = ws.recv() # 42["setStyleProperties",{}]
        
        if (res == "41"):
            raise RoomConnectionException("Failed to connect to room (new update?)")
        
        code, data = parse_socket_io_message(res)

        if (code == "42" and data[0] == "kicked"):
            raise RoomConnectionException("Failed to connect to room: " + data[1])
        
        res = ws.recv() # 430[{"roomEntry":{"roomCode":"YKZA","name":"Guest1405's room","isPublic":false,"gameId":"popsauce","playerCount":1,"chatMode":"enabled","beta":null,"details":"English"},"selfPeerId":0,"selfRoles":["leader"],"scripts":null}]

        if (res == "41"):
            raise BannedFromRoomException("You are banned from this room")

        code, data = parse_socket_io_message(res)
        
        room_entry = data[0]["roomEntry"]
        
        self.room = RoomEntry(
            room_entry["beta"],
            room_entry["chatMode"],
            room_entry["details"] if "details" in room_entry else None,
            room_entry["gameId"],
            room_entry["isPublic"],
            room_entry["name"],
            room_entry["playerCount"],
            room_entry["roomCode"]
        )

        self.peer_id = data[0]["selfPeerId"]
        self.roles = data[0]["selfRoles"]

        threading.Thread(target=self.keep_chat_alive).start()

    def join_round(self):
        """
        Join the round

        :return: None

        :example:

        >>> session.join_round()
        """

        self.game_socket.send('42["joinRound"]')

    def start_round(self):
        """
        Start the round

        :return: None

        :example:

        >>> session.start_round()
        """

        self.game_socket.send('42["startRound"]')

    def submit_guess(self, guess: str):
        """
        Submit a guess (popsauce)

        :param str guess: The guess to submit

        :return: None
        """

        self.game_socket.send(f'42["submitGuess","{guess}"]')

    def type(self, word: str, submit: bool):
        """
        Type a word for BombParty

        :param str word: The word to type
        :param bool submit: Whether to submit the word

        :return: None

        :example:

        >>> session.type("cat", True) # submit the word "cat"
        >>> session.type("ca", False) # type the word "ca" but don't submit
        """

        self.game_socket.send(f'42["setWord","{word}",{json.dumps(submit)}]')

    def open_rules(self):
        """
        Open the rules

        :return: None

        :example:

        >>> session.open_rules()
        """

        self.game_socket.send('42["setRulesLocked",false]')

    def close_rules(self):
        """
        Close the rules

        :return: None

        :example:

        >>> session.close_rules()
        """

        self.game_socket.send('42["setRulesLocked",true]')

    def set_tag_ops(self, tag_ops: dict):
        """
        Set the tag operations (popsauce) open settings as host in popsauce if confused

        :param dict tag_ops: The tag operations

        :return: None

        :example:

        >>> session.set_tag_ops([
        >>>     {
        >>>         "op": "intersection",
        >>>         "tag": "Easy"
        >>>     }
        >>> ])
        """

        payload = json.dumps(tag_ops)
        self.game_socket.send(f'42["setTagOps",{payload}]')

    def set_rules(self, rule: str, value: str):
        """
        Set the rules

        :param str rule: The rule to set
        :param str value: The value to set

        :return: None

        :example:

        >>> session.set_rules("challengeDuration", 5)
        """

        self.game_socket.send(f'42["setRules",{json.dumps({rule: value})}]')

    def start_round_now(self):
        """
        Start the round now

        :return: None

        :example:

        >>> session.start_round_now()
        """
        self.game_socket.send('42["startRoundNow"]')

    def send_chat_message(self, message: str):
        """
        Send a chat message

        :param str message: The message to send

        :return: None

        :example:

        >>> session.send_chat_message("Hello world")
        """

        self.chat_socket.send(f'42["chat", "{message}"]')

    def connect_to_game_socket(self):
        """
        Connect to the game socket

        :return: None

        :example:

        >>> session.connect_to_game_socket()
        """

        ws = self.game_socket
        ws.connect(f"wss://{self.server}/socket.io/?EIO=4&transport=websocket", http_proxy_host=self.proxy_host, http_proxy_port=self.proxy_port, http_proxy_auth=self.proxy_auth, http_proxy_type=self.proxy_type)
        
        # initialize game socket

        ws.recv() # 0{"sid":"kdmocUK_vPURxfHSATOw","upgrades":[],"pingInterval":25000,"pingTimeout":20000,"maxPayload":1000000}
        send_and_recv(ws, "40") # 40{"sid":"g9iP9JbLnIPkL5BHATOx"}
        
        # send "joinGame" instruction
        
        payload = ["joinGame", self.room.game_id, self.room.room_code, self.token]
        res = send_and_recv(ws, f"42{json.dumps(payload)}")

        code, data = parse_socket_io_message(res) # 42["setup",{"serverNow":1739741098091,"rules":{"dictionaryId":{"value":"en","items":[{"value":"de","label":"German"},{"value":"en","label":"English"},{"value":"es","label":"Spanish"},{"value":"fr","label":"French"},{"value":"hu","label":"Hungarian"}]},"scoreGoal":{"value":100,"min":50,"max":1000,"step":10},"scoring":{"value":"timeBased","items":[{"value":"timeBased"},{"value":"constant"}]},"challengeDuration":{"value":20,"min":5,"max":30},"visibleGuesses":{"value":true},"shorthands":{"value":true},"tagOps":{"value":[{"op":"union","tag":"Mainstream"},{"op":"difference","tag":"Hard"}]}},"publicTags":["Mainstream","Easy","Medium","Hard","1950s","1960s","1970s","1980s","1990s","Animated movies","Anime & Manga","Architecture","Art","Board games","Brands","Capital cities","Cartoons","Comic books","Countries","Flags","French","Fruits & vegetables","Game of Thrones","Geography","Images","Indie games","Internet & Memes","K-pop","Literature","Local flags","Logos","Movies","Music","Nature","Personalities","Pokémon","Rap","Series","Software & Apps","Sport","Superheroes","TV Shows","Technology","Texts","The Witcher","Video games","Videos & Streams","Yu-Gi-Oh!"],"filteredQuoteCount":3496,"totalQuoteCount":9806,"constants":{"maxPlayers":100,"minPlayers":2,"maxSourceLength":50,"startTimerDuration":15,"challengeResultDuration":5,"submitRateLimit":{"interval":300,"max":5}},"milestone":{"name":"seating","startTime":null,"rulesLocked":true,"lastRound":null},"players":[],"selfPeerId":0,"selfRoles":["leader"],"leaderPeerId":0}]

        self.game = data[1]

        threading.Thread(target=self.keep_game_alive).start()

    def keep_chat_alive(self):
        """
        The chat socket keep alive loop

        :return: None

        :example:

        >>> session.keep_chat_alive()
        """

        handler_exception = False

        while True:
            msg = self.chat_socket.recv()

            if msg == "2":
                self.chat_socket.send("3")
            else:
                if isinstance(msg, bytes):
                    if self.chat_handler:
                        self.chat_handler(-1, msg)
                else:
                    try:
                        if msg == "41":
                            self.chat_handler(0, ("BAN", "You are banned from this room"))
                            raise BannedFromRoomException("You are banned from this room")

                        code, data = parse_socket_io_message(msg)

                        if (code == "42" and data[0] == "kicked"):
                            self.chat_handler(0, ("KICK", "You got kicked for: " + data[1]))
                            raise BannedFromRoomException("You got kicked for: " + data[1])

                        self.reconnect_attempts = 0
                        
                        if (self.chat_handler):
                            try:
                                self.chat_handler(code, data)
                            except Exception as e:
                                handler_exception = True
                                raise e
                    except Exception as e:
                        if isinstance(e, BannedFromRoomException) or isinstance(e, KickedFromRoomException):
                            break

                        if handler_exception:
                            raise e
                        
                        logging.error("Failed to handle message: " + msg)
                        logging.error("Reconnecting... in 1s")

                        time.sleep(1)

                        self.reconnect_attempts += 1

                        if self.reconnect_attempts > 5:
                            break

                        self.connect_to_chat_socket("")

                        break

    def keep_game_alive(self):
        """
        The game socket keep alive loop

        :return: None

        :example:

        >>> session.keep_game_alive()
        """

        handler_exception = False

        while True:
            msg = self.game_socket.recv()

            if msg == "2":
                self.game_socket.send("3")
            else:
                if isinstance(msg, bytes):
                    if self.game_handler:
                        self.game_handler(-1, msg)
                else:
                    try:
                        if msg == "41":
                            self.game_handler(0, ("BAN", "You are banned from this room"))
                            raise BannedFromRoomException("You are banned from this room")

                        code, data = parse_socket_io_message(msg)

                        if (code == "42" and data[0] == "kicked"):
                            self.game_handler(0, ("KICK", "You got kicked for: " + data[1]))
                            raise BannedFromRoomException("You got kicked for: " + data[1])
                        
                        self.reconnect_attempts = 0

                        if (self.game_handler):
                            try:
                                self.game_handler(code, data)
                            except Exception as e:
                                handler_exception = True
                                raise e
                    except Exception as e:
                        if isinstance(e, BannedFromRoomException) or isinstance(e, KickedFromRoomException):
                            break

                        if handler_exception:
                            raise e

                        logging.error("Failed to handle message: " + msg)
                        logging.error("Reconnecting... in 1s")

                        time.sleep(1)

                        self.reconnect_attempts += 1

                        if self.reconnect_attempts > 5:
                            break

                        self.connect_to_game_socket()
                        self.join_round()

                        break

if __name__ == '__main__':
    pass