import discord
import configparser
from prefixcommand import *
import time
import pytz
import datetime
from discord.ext import tasks, commands
from datetime import datetime
import aiohttp

# If DEBUGGING turn this on to prevent bot get banned
DEBUG = True

# load KEYs from file
configname = 'DEFAULT'
configs = configparser.ConfigParser()
configs.read('config.ini')
config = configs[configname]
print("Config Loaded")

prefix          = config['prefix']
site_token      = config['site_token']
discord_token   = config['token']
site_url        = config['site_url']
guild_id        = int(config['guild_id'])
FACILITY_ID     = config['prefix']
FACILITY_NAME   = config['prefix']
SP_Channel_ID   = int(config['SP_Channel_ID'])
SNR_Channel_ID  = int(config['SNR_Channel_ID'])

guild = []
SENIOR_STAFF    = []
FACILITY_STAFF  = []
TRAINING_STAFF  = []
ACTIVE          = []
WM              = []

intents = discord.Intents.all()
client = discord.Client(intents=intents)

L_TREQ = []

active_vatsim_users = set()
original_nicknames = {}
last_callsigns = {}

artccId = "ZOB"
discord_url = "https://api.vatsim.net/v2/members/discord/"
vnas_live_datafeed = "https://live.env.vnas.vatsim.net/data-feed/controllers.json"

TARGET_CATEGORY_ID = 1391225677432225935

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

@client.event
async def on_ready():
    log(f'Logged on as {client.user}!')
    monitor_voice_and_sync.start()
    # Initialize Golbal Variables
    global guild,SENIOR_STAFF,FACILITY_STAFF,TRAINING_STAFF, WM
    guild = client.get_guild(guild_id)
    #guild = await client.fetch_guild(guild_id)

    SENIOR_STAFF    =  discord.utils.get(guild.roles,name="Senior Staff")
    FACILITY_STAFF  =  discord.utils.get(guild.roles,name="Facility Staff")
    TRAINING_STAFF  =  discord.utils.get(guild.roles,name="Training Staff")
    WM              =  discord.utils.get(guild.roles,name="WM")

    # Start Loop Tasks
    if not quaterHourLooped_tasks.is_running():
        quaterHourLooped_tasks.start()
        print("quaterHourLooped_tasks Started")
    if not dayilyLooped_tasks.is_running():
        dayilyLooped_tasks.start()
        print("dayilyLooped_tasks Started")
    if not reminder_task.is_running():
        reminder_task.start()
        print("reminder_task Started")

@client.event
async def on_member_join(member):
    await syncroles(member, guild) # try to syncrole on member join

@client.event
async def on_raw_reaction_add(payload):
    if(str(payload.emoji) == '📢' and payload.channel_id == int(SP_Channel_ID) and not payload.member.bot):
        await payload.member.add_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

@client.event
async def on_raw_reaction_remove(payload):
    member = discord.utils.get(guild.members, id = payload.user_id)
    if(str(payload.emoji) == '📢' and payload.channel_id == int(SP_Channel_ID) and not member.bot):
        await member.remove_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

@client.event
async def on_message(message): # all reaction from message

    if (message.content.startswith(prefix)):
        noCommand = True
        content = message.content[1:].lower().split(' ')
        command = content[0]

        if(command == "treq" or command == "trainingrequest"):
            msg = await trainingRequest(message,command,guild)
            if (msg):
                L_TREQ.append([msg,time.time()])
            noCommand = False
        elif (command == "sync"):
            await syncroles(message.author, guild)
            noCommand = False
        elif(command == "live"):
            await syncroles(message.author,guild,live=True)
            noCommand = False
        elif(command == "mysession"):
            await myAppointment(message,guild)
            noCommand = False


        if(SENIOR_STAFF in message.author.roles or FACILITY_STAFF in message.author.roles or TRAINING_STAFF in message.author.roles):
            if(command == "spontaneous" or command == "sp" ):
                await spontaneous(message,command,guild)
                noCommand = False
            elif(command == 'syncid'):
                try: 
                    usrid = int(message.content.replace(prefix+command,"").replace(" ",""))
                    usr = guild.get_member(usrid)
                    good = await syncroles(usr, guild)
                    if good == 1:
                        await message.author.send("User has been synced!")
                    elif good == -1:
                        await message.author.send("User has not been synced! Error Occurs")
                    else:
                        await message.author.send("User has not link their account on the website")

                except Exception as e:
                    print("erro in syncid : ")
                    print(e)
                    
                noCommand = False
            
        if (SENIOR_STAFF in message.author.roles or FACILITY_STAFF in message.author.roles):
            if(command == "welcomemessage"):
                await welcomeMessage(message)
                noCommand = False
            elif(command == "spontaneous_embed"):
                await spontaneous_embed(message)
                noCommand = False
            elif(command == "debugmsg"):
                await debugMsg(message)
                noCommand = False
            elif(command == "addevent"):
                await addEvent(message,guild)
                noCommand = False
            elif(command == "waitlist"):
                await waitlist(guild)
                noCommand = False
            elif(command == "closethread"):
                await closethread(message,guild)
                noCommand = False
            
            elif(command == "reminder"):
                print("Working on sending reminders")
                await sendTrainingReminder(guild)
                noCommand = False
            '''
            elif(command == "updatefieldstatus"):
                await updateStatusBoard(guild)
                noCommand = False
            '''

        if (SENIOR_STAFF in message.author.roles or WM in message.author.roles):
            if(command == "activity"):
                await activity(message,guild)
                noCommand = False
            elif(command == "removeroles"):
                await removeroles(message,guild)
                noCommand = False
        if (noCommand):
            await message.author.send('**Error:**\n Insufficient Permission or Command Not Found!')
        
        if not(command == "activity" or command == "removeroles"):
            await message.delete(delay=1.0)

async def get_vatsim_cid_from_discord(discord_user_id: int) -> str | None:
    url = f"{discord_url}{discord_user_id}"
    headers = {'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("user_id")
            else:
                return None

async def check_if_connected_to_vatsim(vatsim_cid):
    headers = {'Accept': 'application/json'}

    async with aiohttp.ClientSession() as session:
        async with session.get(vnas_live_datafeed, headers=headers) as resp:
            if resp.status != 200:
                log(f"[check_if_connected_to_vatsim] Failed to fetch controller data: HTTP {resp.status}")
                return False, None

            data = await resp.json()

    controller_list = data.get("controllers", [])

    for controller in controller_list:
        if controller.get("artccId") != artccId:
            continue

        vatsim_data = controller.get("vatsimData")
        positions = controller.get("positions", [])

        if vatsim_data and str(vatsim_data.get("cid")) == str(vatsim_cid):
            callsign = vatsim_data.get("callsign")
            for pos in positions:
                if pos.get("positionType") == "Artcc":
                    callsign = pos.get("positionName")
                    break
            return True, callsign

    return False, None

@tasks.loop(seconds=15)
async def monitor_voice_and_sync():
    log("[monitor_voice_and_sync] Monitoring connection status")
    for guild in client.guilds:
        for vc in guild.voice_channels:
            if vc.category and vc.category.id == TARGET_CATEGORY_ID:
                for member in vc.members:
                    if member.bot:
                        continue

                    vatsim_cid = await get_vatsim_cid_from_discord(member.id)
                    if not vatsim_cid:
                        continue

                    is_connected, current_callsign = await check_if_connected_to_vatsim(vatsim_cid)

                    if is_connected:
                        if member.id not in original_nicknames:
                            original_nicknames[member.id] = member.nick or member.display_name

                        if (member.id not in active_vatsim_users or
                            last_callsigns.get(member.id) != current_callsign):

                            await syncCallsignToNickname(member, current_callsign)
                            last_callsigns[member.id] = current_callsign
                            active_vatsim_users.add(member.id)

                    else:
                        if member.id in active_vatsim_users:
                            original = original_nicknames.pop(member.id, None)
                            if original:
                                try:
                                    await member.edit(nick=original)
                                    log(f"[Nickname Reset] Restored {member.name} to '{original}'")
                                except discord.Forbidden:
                                    log(f"[Nickname Reset] Missing permissions to restore nickname for {member.name}")
                            active_vatsim_users.remove(member.id)
                            last_callsigns.pop(member.id, None)

@client.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    act_role = discord.utils.get(guild.roles, name="Active Controller")

    if after.channel and after.channel.category and after.channel.category.name == 'Controlling Floor':
        if member.id not in original_nicknames:
            original_nicknames[member.id] = member.nick or member.display_name

        if act_role:
            await member.add_roles(act_role)
        vatsim_cid = await get_vatsim_cid_from_discord(member.id)
        if not vatsim_cid:
            log(f"[on_voice_state_update] No VATSIM CID found for {member.name}")
            return

        is_connected, current_callsign = await check_if_connected_to_vatsim(vatsim_cid)
        if is_connected and current_callsign:
            await syncCallsignToNickname(member, current_callsign)

    elif before.channel and before.channel.category and before.channel.category.name == 'Controlling Floor':
        still_in_category = (
            after.channel and after.channel.category and after.channel.category.name == 'Controlling Floor'
        )

        if not still_in_category:
            original = original_nicknames.pop(member.id, None)
            if original:
                try:
                    await member.edit(nick=original)
                    log(f"[on_voice_state_update] Restored nickname for {member.name} to '{original}'")
                except discord.Forbidden:
                    log(f"[on_voice_state_update] Missing permissions to restore nickname for {member.name}")
            if act_role:
                await member.remove_roles(act_role)

async def syncCallsignToNickname(member: discord.Member, raw_callsign: str):
    try:
        callsign_clean = raw_callsign.replace("_", " ")

        suffix = ""
        if member.nick and "|" in member.nick:
            suffix = member.nick.split("|", 1)[1].strip()

        new_nickname = f"{callsign_clean} | {suffix}" if suffix else callsign_clean

        await member.edit(nick=new_nickname)
        log(f"[syncCallsignToNickname] Nickname updated to: '{new_nickname}'")

    except Exception as e:
        log(f"[syncCallsignToNickname] Error: {e}")
        
@tasks.loop(seconds=900)       
async def quaterHourLooped_tasks():
    global L_TREQ
    L_TREQ = await deleteTreq(L_TREQ)
    if not DEBUG:
        await updateStatusBoard(guild)

@tasks.loop(seconds = 43200.0)
async def dayilyLooped_tasks():
    pass

reminderTime = datetime.time(hour=7, minute=0, tzinfo=pytz.timezone('US/Eastern'))
@tasks.loop(time = reminderTime)
async def reminder_task():
    await sendTrainingReminder(guild)
    await waitlist(guild)
    print("Reminder Sent!")

client.run(discord_token)