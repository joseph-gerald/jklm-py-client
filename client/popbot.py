from websocket import WebSocket
import nodriver as uc
import asyncio

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

    while True:
        if (await page.evaluate("!(window['grecaptcha'] && grecaptcha.execute)", await_promise=True)): await asyncio.sleep(0.1)
        else: break

    token = await page.evaluate("grecaptcha.execute('6LdzYGslAAAAACxOZaQA5J0CxlfdJQUdWvJYoAFM', { action: 'joinRoom' })", await_promise=True)
    await page.close()

    return token

if __name__ == '__main__':
    uc.loop().run_until_complete(get_grecaptcha_token())