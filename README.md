![image](https://github.com/user-attachments/assets/321a2c60-9a57-4b7a-b89b-166795fa7711)

# jklm-py-client
Flexible JKLM.fun client built for Python 3

## ✨ Features
- Versatile implementation allowing you to build anything
- Integrated JKLM client functions (chat, join, etc)
- Proxy support allows safe and anonymous connection
- Simple to use api

# Installation
Install via pip
```sh
pip install -U jklm
```
# Documentation
1. [Make A Room](#make-a-room)
2. [Simple Usage](#simple-usage)
3. [Proxy Usage](#proxy-usage)
4. [Set A Profile Picture](#set-a-profile-picture)
5. [Connections (Twitch, Discord)](#connections-twitch-discord)
6. [Chat Client](#chat-client)
7. [PopSauce](#pop-sauce)
    - [Challenge Hasher](#challenge-hasher)
    - [Auto-Answer](#auto-answer)
8. [Bomb Party](#bomb-party)
    - Someone make a PR

## PopSauce Answers
> [!NOTE]  
> As of **18/02/25** only **9775/9806** *(~99.7%)* of **PopSauce** are indexed due to the nature of scraping them `x log(x)` 

### [popsauce.zip](answers/popsauce.zip)
> heavy zipped folder of *all the questions, answers and data (image, etc)

### [popsauce_pairs.txt](answers/popsauce_pairs.txt)
> light weight txt file of all the `challenge_hash:answer` pairings

### [extract_pairs.py](answers/extract_pairs.py)
> simple script to extract pairs from the unzipped popsauce folder to popsauce_pairs.txt

## Make A Room
Here is an example of how to create a room
```python
from jklm import JKLM

jklm = JKLM("BOT")

res = jklm.start_room("selector", True, "test")
print(res) # {'url': 'https://falcon.jklm.fun', 'room_code': 'RNGG'}
```

## Simple Usage
Here is a simple example of how to connect to a room and join a round *(gamemode agnostic)*
```python
from jklm import JKLM

def main(room_id):
    username = "EXAMPLE_BOT"

    # Initialize JKLM session
    session = JKLM(username)

    try:
        # Attempt to connect to specified room
        session.connect(room_id)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        # Handle connection failures gracefully
        print("[X] Failed to join room:", e)
        return

    # Join active game round after successful connection
    session.join_round()

if __name__ == '__main__':
    # Launch bot and join room "ABUM"
    main("ABUM")
```

## Proxy Usage
Here is an example of how to connect to a room using a proxy
```python
from jklm import JKLM

def main(room_id):
    username = "EXAMPLE_BOT"

    proxy = {
        "host": "...",
        "port": 8080,
        "type": "http", # http, https, socks4, socks5
        "auth": ("username", "password")
    }

    # Initialize JKLM session
    session = JKLM(username, proxy=proxy)

    try:
        # Attempt to connect to specified room
        session.connect(room_id)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        # Handle connection failures gracefully
        print("[X] Failed to join room:", e)
        return

    # Join active game round after successful connection
    session.join_round()

if __name__ == '__main__':
    # Launch bot and join room "ABUM"
    main("ABUM")
```

## Set A Profile Picture
Here is an example of how to set a profile picture
```python
from jklm import JKLM
import time

import psutil
import os


def main(room_id):
    image = open("logo.png", "rb").read() # Try to keep image 128x128

    username = "BOT_" + str(time.time())[-5:]
    session = JKLM(username, pfp=image)

    try:
        session.connect(room_id)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        print("[X] Failed to join room:", e)
        return

    input("")
    current_system_pid = os.getpid()

    ThisSystem = psutil.Process(current_system_pid)
    ThisSystem.terminate()


if __name__ == '__main__':
    main("KMPW")
```

## Connections (Twitch, Discord)
Here is an example of how to connect to a room using a twitch or discord account
```python
from jklm import JKLM
import time

import psutil
import os


def main(room_id):
    image = open("logo.png", "rb").read() # Try to keep image 128x128

    username = "BOT_" + str(time.time())[-5:]
    session = JKLM(username, pfp=image, connection={
        "service": "twitch", # twitch, discord
        "username": "jklm_bot", # Isn't validated
        "token": "YOUR_TOKEN", # Validated
        "expiration": 0 # Isn't validated
    })

    try:
        session.connect(room_id)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        print("[X] Failed to join room:", e)
        return

    input("")
    current_system_pid = os.getpid()

    ThisSystem = psutil.Process(current_system_pid)
    ThisSystem.terminate()


if __name__ == '__main__':
    main("KMPW")
```

## Chat Client
Here is an example of how to connect to a room and chat back and forth with other users
```python
from jklm import JKLM
import time

import psutil
import os

def main(room_id):
    
    username = "BOT_" + str(time.time())[-5:]
    session = JKLM(username)

    def chat_handler(code, raw_data):
        event = raw_data[0]
        data = raw_data[1]

        # 0 CODE = Kicked from room (event = TYPE ["KICKED" | "BAN"], data = INFO)

        if (code == 0):
            print("[X] Kicked from room:", data)
            return

        match event:
            case "chat":
                message = raw_data[2]

                print(f"[CHAT] {data['nickname']}: {message}")
                pass
            case "chatterAdded":
                print(f"[+] {data} joined the room")
            case "chatterRemoved":
                print(f"[-] {data} left the room")
            case "setPlayerCount":
                print(f"[!] {data} players in the room")
            case _:
                print(f"[UNHANDLED CHAT EVENT] {event}:", data)

    try:
        session.connect(room_id, chat_handler=chat_handler)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        print("[X] Failed to join room:", e)
        return

    try:
        while True:
            message = input("")

            if message == "":
                raise KeyboardInterrupt

            session.send_chat_message(message)

            time.sleep(1)

            if session.reconnect_attempts > 5:
                print("Reconnect attempts exceeded")
                current_system_pid = os.getpid()

                ThisSystem = psutil.Process(current_system_pid)
                ThisSystem.terminate()
                break
    except KeyboardInterrupt:
        current_system_pid = os.getpid()

        ThisSystem = psutil.Process(current_system_pid)
        ThisSystem.terminate()

if __name__ == '__main__':
    main("ABUM")
```

# Pop Sauce

## Challenge Hasher
Here is an example of how to hash a challenge
```python
from jklm import JKLM
import time

import hashlib

import psutil
import os

expecting_image = False
challenge = {
    "end_time": 0,
    "image": None,
    "prompt": None,
    "text": None,
    "hash": None
}

def sha1(input):
    if isinstance(input, str):
        input = input.encode()
    return hashlib.sha1(input).hexdigest()

def main(room_id):
    global expecting_image, challenge
    
    username = "BOT_" + str(time.time())[-5:]
    session = JKLM(username)

    def game_handler(code, raw_data):
        global expecting_image, challenge
        event = raw_data[0]
        data = raw_data[1]

        # -1 CODE = Image data
        # 0 CODE = Kicked from room (event = TYPE ["KICKED" | "BAN"], data = INFO)

        if (code == 0):
            print("[X] Kicked from room:", data)
            return

        if (code == -1):
            asset_type = challenge["image"]["type"]
            extension = ""

            match asset_type:
                case "image/svg+xml":
                    extension = "svg"
                case "image/png":
                    extension = "png"
                case "image/jpeg":
                    extension = "jpeg"

            challenge["hash"] = sha1(challenge["prompt"].encode() + raw_data)
            challenge["image"]["extension"] = extension

            print("[?] Challenge Hash:", challenge["hash"])
            print("[?] Image has been saved to image." + extension)

            with open("image." + extension, "wb") as f:
                f.write(raw_data)

            return

        match event:
            case "startChallenge":
                print("\n[!] New Challenge Started")

                challenge["end_time"] = data["endTime"]
                challenge["image"] = data["image"]
                challenge["prompt"] = data["prompt"]
                challenge["text"] = data["text"]

                if challenge["image"]:
                    expecting_image = True
                    print("[?] Image Challenge", challenge["prompt"])
                else:
                    expecting_image = False
                    challenge["hash"] = sha1(challenge["prompt"] + challenge["text"])

                    print("[?] Text Challenge:", challenge["prompt"])
                    print("[?] Challenge Hash:", challenge["hash"])
                    print("[?]", challenge["text"])


            case "endChallenge":
                print("\n[!] Challenge Ended")
                print("[X] Correct Answer:", data["source"])
                
            case "setPlayerState":
                event, peer_id, data = raw_data
                    
                guess = data["guess"]
                found_answer = data["hasFoundSource"]
                points = data["points"]
                elapsed_time = data["elapsedTime"]

                player = list(filter(lambda x: x["profile"]["peerId"] == peer_id, session.game["players"]))[0]

                if found_answer:
                    print(f"[!] {player['profile']['nickname']} with {points} points guessed it in {elapsed_time} seconds")
                else:
                    print(f"[!] {player['profile']['nickname']} with {points} points guessed {guess}")

            case "updatePlayer":
                event, peer_id, data, online = raw_data

                player = list(filter(lambda x: x["profile"]["peerId"] == peer_id, session.game["players"]))[0]

                if online:
                    print(f"[+] {player['profile']['nickname']} reconnected to the game")
                else:
                    print(f"[-] {player['profile']['nickname']} disconnected from the game")

            case "addPlayer":
                print(f"[+] {data['profile']['nickname']} joined the game")

            case _:
                print(f"[UNHANDLED GAME EVENT] {event}:", raw_data)

    try:
        session.connect(room_id, game_handler=game_handler)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        print("[X] Failed to join room:", e)
        return

    session.join_round()

    # Checks if a challenge is already started

    if ("challenge" in session.game["milestone"]):
        print("\n[!] Challenge already started")
        
        current_challenge = session.game["milestone"]["challenge"]
        
        # If the challenge has ended but the next one hasn't started yet endTime will be null
        challenge["end_time"] = current_challenge["endTime"] if "endTime" in current_challenge else 0
        challenge["image"] = current_challenge["image"]
        challenge["prompt"] = current_challenge["prompt"]
        challenge["text"] = current_challenge["text"]

        if challenge["image"]:
            expecting_image = True
            print("[?] Image Challenge", challenge["prompt"])
        else:
            expecting_image = False

            challenge["hash"] = sha1(challenge["prompt"] + challenge["text"])

            print("[?] Text Challenge:", challenge["prompt"])
            print("[?]", challenge["text"])
            print("[?] Challenge Hash:", challenge["hash"])

    input("")
    current_system_pid = os.getpid()

    ThisSystem = psutil.Process(current_system_pid)
    ThisSystem.terminate()

if __name__ == '__main__':
    main("ABUM")
```

## Auto-Answer
Here is an example of how to auto-answer and send the answer to the chat
```python
from jklm import JKLM
import requests
import time

import hashlib

import psutil
import os

expecting_image = False
challenge = {
    "end_time": 0,
    "image": None,
    "prompt": None,
    "text": None,
    "hash": None
}

res = requests.get("https://cdn.jsdelivr.net/gh/joseph-gerald/jklm-py-client@main/answers/popsauce_pairs.txt")
answers = {x.split(":", 1)[0]: x.split(":", 1)[1].strip() for x in res.text.split("\n") if x}

def sha1(input):
    if isinstance(input, str):
        input = input.encode()
    return hashlib.sha1(input).hexdigest()

def main(room_id):
    global expecting_image, challenge
    
    username = "BOT_" + str(time.time())[-5:]
    session = JKLM(username)

    def game_handler(code, raw_data):
        global expecting_image, challenge
        event = raw_data[0]
        data = raw_data[1]

        # -1 CODE = Image data
        # 0 CODE = Kicked from room (event = TYPE ["KICKED" | "BAN"], data = INFO)

        if (code == 0):
            print("[X] Kicked from room:", data)
            return

        if (code == -1):
            asset_type = challenge["image"]["type"]
            extension = ""

            match asset_type:
                case "image/svg+xml":
                    extension = "svg"
                case "image/png":
                    extension = "png"
                case "image/jpeg":
                    extension = "jpeg"

            challenge["hash"] = sha1(challenge["prompt"].encode() + raw_data)
            challenge["image"]["extension"] = extension

            print("[?] Challenge Hash:", challenge["hash"])
            
            answer = answers.get(challenge["hash"])

            if answer:
                print("[!] Answer is indexed:", answer)
                session.submit_guess(answer)
                session.send_chat_message(answer)
            else:
                print("[!] Answer was not indexed")

            return

        match event:
            case "startChallenge":
                print("\n[!] New Challenge Started")

                challenge["end_time"] = data["endTime"]
                challenge["image"] = data["image"]
                challenge["prompt"] = data["prompt"]
                challenge["text"] = data["text"]

                if challenge["image"]:
                    expecting_image = True
                    print("[?] Image Challenge", challenge["prompt"])
                else:
                    expecting_image = False
                    challenge["hash"] = sha1(challenge["prompt"] + challenge["text"])

                    print("[?] Text Challenge:", challenge["prompt"])
                    print("[?] Challenge Hash:", challenge["hash"])
                    print("[?]", challenge["text"])

                    answer = answers.get(challenge["hash"])
                    if answer:
                        print("[!] Answer is indexed:", answer)
                        session.submit_guess(answer)
                        session.send_chat_message(answer)
                    else:
                        print("[!] Answer was not indexed")


            case "endChallenge":
                print("\n[!] Challenge Ended")
                print("[X] Correct Answer:", data["source"])
                
            case "setPlayerState":
                event, peer_id, data = raw_data
                    
                guess = data["guess"]
                found_answer = data["hasFoundSource"]
                points = data["points"]
                elapsed_time = data["elapsedTime"]

                print(f"[!] {peer_id} {data}")
                
                if peer_id == session.peer_id:
                    return

                player = list(filter(lambda x: x["profile"]["peerId"] == peer_id, session.game["players"]))[0]

                if found_answer:
                    print(f"[!] {player['profile']['nickname']} with {points} points guessed it in {elapsed_time} seconds")
                else:
                    print(f"[!] {player['profile']['nickname']} with {points} points guessed {guess}")

            case "updatePlayer":
                event, peer_id, data, online = raw_data

                player = list(filter(lambda x: x["profile"]["peerId"] == peer_id, session.game["players"]))[0]

                if online:
                    print(f"[+] {player['profile']['nickname']} reconnected to the game")
                else:
                    print(f"[-] {player['profile']['nickname']} disconnected from the game")

            case "addPlayer":
                print(f"[+] {data['profile']['nickname']} joined the game")

            case _:
                print(f"[UNHANDLED GAME EVENT] {event}:", raw_data)

    try:
        session.connect(room_id, game_handler=game_handler)
        print("[.] Successfully joined", room_id)
    except Exception as e:
        print("[X] Failed to join room:", e)
        return

    session.join_round()

    # Checks if a challenge is already started

    if ("challenge" in session.game["milestone"]):
        print("\n[!] Challenge already started")
        
        current_challenge = session.game["milestone"]["challenge"]
        
        # If the challenge has ended but the next one hasn't started yet endTime will be null
        challenge["end_time"] = current_challenge["endTime"] if "endTime" in current_challenge else 0
        challenge["image"] = current_challenge["image"]
        challenge["prompt"] = current_challenge["prompt"]
        challenge["text"] = current_challenge["text"]

        if challenge["image"]:
            expecting_image = True
            print("[?] Image Challenge", challenge["prompt"])
        else:
            expecting_image = False

            challenge["hash"] = sha1(challenge["prompt"] + challenge["text"])

            print("[?] Text Challenge:", challenge["prompt"])
            print("[?]", challenge["text"])
            print("[?] Challenge Hash:", challenge["hash"])

    input("")
    current_system_pid = os.getpid()

    ThisSystem = psutil.Process(current_system_pid)
    ThisSystem.terminate()

if __name__ == '__main__':
    main("ABUM")
```

# Bomb Party
soon™️
