import discord
import configparser
from prefixcommand import *
import time

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



'''
print("Discord.py Version:",end = '')
print(discord.__version__)
print('Prefix = ',end='')
print(prefix)
'''

class MyClient(discord.Client):
    L_TREQ = []
    t_start = time.time()
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        # Initialize Golbal Variables
        global guild,SENIOR_STAFF,FACILITY_STAFF,TRAINING_STAFF, WM
        guild = await self.fetch_guild(guild_id)
        SENIOR_STAFF    =  discord.utils.get(guild.roles,name="Senior Staff")
        FACILITY_STAFF  =  discord.utils.get(guild.roles,name="Facility Staff")
        TRAINING_STAFF  =  discord.utils.get(guild.roles,name="Training Staff")
        WM              =  discord.utils.get(guild.roles,name="WM")

    async def on_member_join(self,member):
        await syncroles(member, guild) # try to syncrole on member join

    async def on_reaction_add(self,reaction,user):
        if(reaction.emoji == '📢' and reaction.message.channel.id == int(SP_Channel_ID) and not user.bot):
            await user.add_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

    async def on_reaction_remove(self,reaction, user):
        if(reaction.emoji == '📢' and reaction.message.channel.id == int(SP_Channel_ID) and not user.bot):
            await user.remove_roles(discord.utils.get(guild.roles,name="Spontaneous Training"))

    async def on_message(self, message): # all reaction from message
        self.L_TREQ = await deleteTreq(self.L_TREQ)
        if((time.time()-self.t_start)>43200):
            self.t_start = time.time()
            await waitlist(guild)

        if (message.content.startswith(prefix)):
            noCommand = True
            content = message.content[1:].lower().split(' ')
            command = content[0]

            if(command == "treq" or command == "trainingrequest"):
                msg = await trainingRequest(message,command,guild)
                if (msg):
                    self.L_TREQ.append([msg,time.time()])
                noCommand = False
            elif (command == "sync"):
                await syncroles(message.author, guild)
                noCommand = False
            elif(command == "live"):
                await syncroles(message.author,guild,live=True)
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


    async def on_voice_state_update(self, member, before, after):
        act_role = discord.utils.get(guild.roles,name= "Active Controller")
        if (after.channel == None or not after.channel.category.name == 'Controlling Floor'):
            await member.remove_roles(act_role)
        elif(after.channel.category.name == 'Controlling Floor'):
            await member.add_roles(act_role)
            

def main():

    # discord intents
    intents = discord.Intents.all()
    '''    
    intents.dm_messages = True
    intents.messages = True
    intents.guild_reactions = True
    intents.guilds = True
    intents.members = True
    intents.voice_states = True
    intents.reactions = True
    '''
    client = MyClient(intents=intents)
    client.run(discord_token)



if __name__=='__main__':
    main()