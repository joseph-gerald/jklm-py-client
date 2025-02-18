from jklm import JKLM
import time

import hashlib

import psutil
import os

def sha1(input):
    if isinstance(input, str):
        input = input.encode()
    return hashlib.sha1(input).hexdigest()

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