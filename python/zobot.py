import discord
import configparser
from prefixcommand import *
import time
from zoneinfo import ZoneInfo
import pytz
import datetime
from discord.ext import tasks, commands
import json

import aiohttp

# If DEBUGGING turn this on to prevent bot get banned
DEBUG = False

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
SNR_Channel_ID  = int(config['SNR_Channel_ID'])

guild = []
SENIOR_STAFF    = []
FACILITY_STAFF  = []
TRAINING_STAFF  = []
ACTIVE          = []
WM              = []

intents = discord.Intents.all()
client = discord.Client(intents=intents)

#Relief Settings
ALERT_THRESHOLD = 30

L_TREQ = []

# Load center name
try:
    with open("center.json", "r") as f:
        centers = json.load(f)
except FileNotFoundError:
    centers = {}

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

@client.event
async def on_ready():
    log(f'Logged on as {client.user}!')
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
    if not monitor_active_controller.is_running():
        monitor_active_controller.start()
        print("monitor_active_controller Started")

@client.event
async def on_member_join(member):
    await syncroles(member, guild) # try to syncrole on member join

@client.event
async def on_raw_reaction_add(payload):
    channel = discord.utils.get(guild.channels,id = payload.channel_id)
    if(str(payload.emoji) == '📢' and channel.name == "spontaneous-training" and not payload.member.bot):
        await payload.member.add_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

@client.event
async def on_raw_reaction_remove(payload):
    member = discord.utils.get(guild.members,id = payload.user_id)
    channel = discord.utils.get(guild.channels,id = payload.channel_id) 
    if(str(payload.emoji) == '📢' and channel.name == "spontaneous-training") and not member.bot:
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
        elif(command == "mysession" or command == "myappointment"):
            await myAppointment(message,guild)
            noCommand = False
        elif command == "relief":
            await requestRelief(message,command,guild)
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



@tasks.loop(seconds=60)
async def monitor_active_controller():
    # Load active controller list
    actives = await webQuery_async(site_url + '/api/data/bot/activeControllers.php', site_token)

    # Load existing nickname records
    try:
        with open("nicknames.json", "r") as f:
            nicknames = json.load(f)
    except FileNotFoundError:
        nicknames = {}

    currn_active = set()

    # Process all currently active controllers
    for controller in actives:
        discord_id = controller['discord_id']
        if not discord_id:
            print(f"{controller['cid']} does not have discord linked")
            continue

        currn_active.add(discord_id)

        member = guild.get_member(int(discord_id))
        if not member:
            print(f"Discord member {discord_id} not found in guild.")
            continue

        # Determine new nickname based on role
        if controller['type'] == 'Center':
            newName = centers[controller['position_name'][-2:]] + controller['position_name'][-2:] + ' | ' + controller['OI']
        else:
            newName = controller['default_callsign'] + ' | ' + controller['OI']

        # Save original name if not yet stored
        if discord_id not in nicknames:
            nicknames[discord_id] = {
                "discord_id": discord_id,
                "original_name": member.display_name
            }

        # Update nickname if changed (fixes position switching)
        if member.display_name != newName:
            try:
                await member.edit(nick=newName)
                print(f"Updated nickname for {member.name} → {newName}")
            except discord.Forbidden:
                print(f"Missing permission to update nickname for {member.name}")

    # if controllers exist, check to see if their si a lot of pilots on their frequency
    if actives:
        try:
            workload = await webQuery_async(site_url + "/api/data/ids/workload?json=1", site_token)
        except Exception as e:
            print(f"workload fetch failed: {e}")
            return

        buckets = (workload or {}).get("controllers", [])
        if not isinstance(buckets, list) or not buckets:
            return

        alerts: list[tuple[str, int, str]] = []  # (callsign, pilot_count, frequency)

        for b in buckets:
            freq = (b or {}).get("frequency")
            if not freq:
                continue

            pilot_count = b.get("pilot_count")
            if pilot_count is None:
                pilot_count = len(b.get("pilots") or [])
            pilot_count = int(pilot_count)

            if pilot_count <= ALERT_THRESHOLD:
                continue

            # workload payload controllers on that frequency
            ctrls = b.get("controllers") or []
            for c in ctrls:
                callsign = c.get("callsign") or c.get("vnas_callsign")
                if callsign:
                    alerts.append((callsign, pilot_count, freq))

        if not alerts:
            return

        # Send alerts
        for callsign, count_on_freq, freq in alerts:
            await send_relief_workload_alert(
                alert_type="workload",
                guild=guild,
                callsign=callsign,
                on_frequency=count_on_freq,
                frequency=freq,
                cooldown_seconds=20 * 60,
            )

    # Restore names for controllers who are no longer active
    to_delete = []
    for discord_id, data in nicknames.items():
        if discord_id not in currn_active:
            member = guild.get_member(int(discord_id))
            if member:
                try:
                    await member.edit(nick=data["original_name"])
                    print(f"Restored nickname for {member.name}")
                    to_delete.append(discord_id)
                except discord.Forbidden:
                    print(f"Missing permission to restore nickname for {member.name}")
            else:
                print(f"Member with Discord ID {discord_id} not found for restoration.")

    # Clean up JSON dict
    for discord_id in to_delete:
        del nicknames[discord_id]

    # Save updated JSON
    with open("nicknames.json", "w") as f:
        json.dump(nicknames, f, indent=2)

@client.event
async def on_voice_state_update(member, before, after):
    act_role = discord.utils.get(guild.roles,name= "Active Controller")
    if (after.channel == None or not after.channel.category.name == 'Sterile Controlling Floor'):
        await member.remove_roles(act_role)
    elif(after.channel.category.name == 'Sterile Controlling Floor'):
        await member.add_roles(act_role)
        
@tasks.loop(seconds=900)       
async def quaterHourLooped_tasks():
    global L_TREQ
    L_TREQ = await deleteTreq(L_TREQ)
    if not DEBUG:
        await updateStatusBoard(guild)

@tasks.loop(seconds = 43200.0)
async def dayilyLooped_tasks():
    pass

reminderTime = datetime.time(7, 0, tzinfo=ZoneInfo("America/New_York"))
@tasks.loop(time = reminderTime)
async def reminder_task():
    await sendTrainingReminder(guild)
    #await waitlist(guild)
    print("Reminder Sent!")

#Create thread when event starts
@client.event
async def on_scheduled_event_update(before,after):
    # Detect transition to "active" (event starting)
    if (
        before.status != discord.EventStatus.active
        and after.status == discord.EventStatus.active
    ):
        channel = discord.utils.get(guild.channels,name = "event-debrief")
        if channel is None:
            print("Thread parent channel not found")
            return

        # Create a thread with the same name as the event
        thread = await channel.create_thread(
            name="[debrief]"+after.name,
            type=discord.ChannelType.public_thread,
            auto_archive_duration=4320  # 72 hours
        )
client.run(discord_token)