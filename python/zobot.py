import discord
import configparser
from prefixcommand import *
import time
import pytz
import datetime
from discord.ext import tasks, commands


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

@client.event
async def on_ready():

    print(f'Logged on as {client.user}!')
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

    #DEBUG

@client.event
async def on_member_join(member):
    await syncroles(member, guild) # try to syncrole on member join

@client.event
async def on_reaction_add(reaction,user):
    if(reaction.emoji == '📢' and reaction.message.channel.id == int(SP_Channel_ID) and not user.bot):
        await user.add_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

@client.event
async def on_reaction_remove(reaction, user):
    if(reaction.emoji == '📢' and reaction.message.channel.id == int(SP_Channel_ID) and not user.bot):
        await user.remove_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

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
                #TODO 
                pass
            
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
            '''
            elif(command == "reminder"):
                await sendTrainingReminder(guild)
                noCommand = False
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

@client.event
async def on_voice_state_update(member, before, after):
    act_role = discord.utils.get(guild.roles,name= "Active Controller")
    if (after.channel == None or not after.channel.category.name == 'Controlling Floor'):
        await member.remove_roles(act_role)
    elif(after.channel.category.name == 'Controlling Floor'):
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

reminderTime = datetime.time(hour=7, minute=0, tzinfo=pytz.timezone('US/Eastern'))
@tasks.loop(time = reminderTime)
async def reminder_task():
    await sendTrainingReminder(guild)
    await waitlist(guild)
    print("Reminder Sent!")

client.run(discord_token)
