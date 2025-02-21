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

    def chat_handler(code, raw_data):
        global expecting_image, challenge
        event = raw_data[0]
        data = raw_data[1]

        # -1 CODE = Image data
        # 0 CODE = Kicked from room (event = TYPE ["KICKED" | "BAN"], data = INFO)

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
        session.connect(room_id, "token", chat_handler, game_handler)
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

    print("\n[!] Chatting is enabled")
    print("\n[!] Any message without a prefix will be sent as a chat message")
    print("[!] Prefix your message with ! to send it as a guess")

    try:
        while True:
            message = input("")

            if message == "":
                raise KeyboardInterrupt

            if message.startswith("!"):
                message = message[1:]
                session.send_guess(message)
            else:
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
    main("CBTT")