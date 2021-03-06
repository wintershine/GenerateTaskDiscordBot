# GenerateTaskDiscordBot

This bot allows GenerateTask users and accounts to interact with the leaderboards and offers other features centered around the game mode

## How to set it up

**Step 1:** Enable the API and download credentials.json. This can be done here: https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the

Make sure credentials.json is stored in the same directory as the bot.

**Step 2:** Create your own discord server and bot for testing

Create your own discord server: https://support.discordapp.com/hc/en-us/articles/204849977-How-do-I-create-a-server-

Discord bot and adding it to your server: https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token

Save the token in a new file called discordbot_token.txt and place it in the same directory as the bot

**Step 3:** Install Python dependencies

If you haven't installed Python yet, download it [here](https://www.python.org/).

Install discordpy: `pip install discord-py`

Run the pip command listed here: https://developers.google.com/sheets/api/quickstart/python#step_2_install_the_google_client_library

`pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib gspread oauth2client`

**Step 4:** Run the bot

`python init.py`
