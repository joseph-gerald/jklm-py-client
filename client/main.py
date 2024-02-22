import nodriver as uc
import popbot

async def main():
    token = await popbot.get_grecaptcha_token()
    print(token)

if __name__ == '__main__':
    uc.loop().run_until_complete(main())