# DiscordBot
 
A discord bot written in Python.

Files not version controlled but are necessary for the bot to run:
- `.env` contains all environment variables for the bot, they are loaded by `dotenv.load_dotenv()` in the main program.
```
token={discord-token}
simc={path-to-local-simc-binary}
```
- `apikey.txt`: Blizzard API key which SimulationCraft will be using to pull character information from WoW Armory
```
{client-id}:{secret}
```
