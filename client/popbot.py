import requests
from websocket import WebSocket
import nodriver as uc
import asyncio

from enum import Enum

import random
import string

class URLS(Enum):
    START_ROOM = "https://jklm.fun/api/startRoom"

async def get_grecaptcha_token():
    browser = await uc.start()
    page = await browser.get('https://jklm.fun')

    await page.get_content()
    
    privacyToggle = await page.find("/html/body/div/div[5]/div[2]/div[1]/div/form/div[2]/label[2]")
    roomCreateButton = await page.find('/html/body/div/div[5]/div[2]/div[1]/div/form/div[2]/button')

    await privacyToggle.click()
    await asyncio.sleep(0.1)
    await roomCreateButton.click()

    await page.get_content()

    while await page.evaluate("!(window['grecaptcha'] && grecaptcha.execute)", await_promise=True):
        await asyncio.sleep(0.1)

    token = await page.evaluate("grecaptcha.execute('6LdzYGslAAAAACxOZaQA5J0CxlfdJQUdWvJYoAFM', { action: 'joinRoom' })", await_promise=True)
    await page.close()

    return token

class JKLM:
    def __init__(self, username) -> None:
        # random 16 character token
        self.token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.username = username

    def start_room(self, game_id, public, room_name):

        json = {
            "name": room_name, 
            "isPublic": public,
            "gameId": game_id, # selector, popsauce, bombparty
            "creatorUserToken": self.token
        }

        res = requests.post(URLS.START_ROOM.value, json=json)



if __name__ == '__main__':
    uc.loop().run_until_complete(get_grecaptcha_token())