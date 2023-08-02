from webQuery import webQuery
import configparser
import discord
from datetime import datetime, timedelta
import requests
from discord.ext import tasks, commands

configname = 'DEFAULT'
configs = configparser.ConfigParser()
configs.read('config.ini')
config = configs[configname]

prefix          = config['prefix']
site_token      = config['site_token']
discord_token   = config['token']
site_url        = config['site_url']
guild_id        = int(config['guild_id'])
FACILITY_ID     = config['FACILITY_ID']
FACILITY_NAME   = config['FACILITY_NAME']
SP_Channel_ID   = int(config['SP_Channel_ID'])
SNR_Channel_ID  = int(config['SNR_Channel_ID'])

async def syncroles(user, guild , live = False):
    query = site_url+'/api/data/bot/?discord_id='+str(user.id)
    try:
        usrdata = webQuery(query,site_token)
        if (not usrdata['status']=='None'): #Successfully query data from website
            name = str()
            fullname = str()
            
            if(usrdata['pref_name']):
                name = usrdata['pref_name']
            else:
                if(int(usrdata['discord_nick_pref'])):
                    name = usrdata['first_name'] 
                else:
                    name = usrdata['first_name'] + ' '+usrdata['last_name']

            if(not usrdata['type']=='lim'):
                # HOME or VISITING controller

                # LIVE
                if(live):
                    if(user.display_name.find('LIVE')==-1):
                        fullname = name + ' | LIVE'
                        onLIVE = True
                    else:
                        fullname = name + ' | ' + usrdata['initials']
                        onLIVE = False
                
                        if(usrdata['type'] == 'loa'):
                            fullname = name + ' | ' + usrdata['facility']
                        else:
                            fullname = name + ' | ' + usrdata['initials']

                        if(usrdata['facility']=='ZHQ'):
                            fullname = name + ' | VATUSA#'; 
                        if (usrdata['rating'] == 'ADM'):
                            fullname = name + ' | VAT???#'; 
                        if (usrdata['mentor'] == 'Yes'):
                            fullname = name + ' | MTR'; 
                        if (usrdata['ins'] == 'Yes'):
                            fullname = name + ' | INS'; 
                        if (not usrdata['staff'] == ''):
                            fullname = name + ' | '+ usrdata['staff']
                else:
                    if(usrdata['type'] == 'loa'):
                        fullname = name + ' | ' + usrdata['facility']
                    else:
                        fullname = name + ' | ' + usrdata['initials']

                    if(usrdata['facility']=='ZHQ'):
                        fullname = name + ' | VATUSA#'; 
                    if (usrdata['rating'] == 'ADM'):
                        fullname = name + ' | VAT???#'; 
                    if (usrdata['mentor'] == 'Yes'):
                        fullname = name + ' | MTR'; 
                    if (usrdata['ins'] == 'Yes'):
                        fullname = name + ' | INS'; 
                    if (not usrdata['staff'] == ''):
                        fullname = name + ' | '+ usrdata['staff']

                await user.edit(nick = fullname)

                # REMOVE ROLES
                await removeAllRoles(user)

                # ADD ROLES 
                role = discord.utils.get(guild.roles,name= "VATSIM Controller")
                await user.add_roles(role)
                rating = discord.utils.get(guild.roles,name= usrdata['rating'])
                await user.add_roles(rating)

                if(usrdata['type']=='vis'):
                    primRole = discord.utils.get(guild.roles,name="Visiting Controller")
                else:
                    primRole = discord.utils.get(guild.roles,name= FACILITY_ID+ " Controller")
                await user.add_roles(primRole)

                # FACILITY STAFF?
                if (usrdata['staff'] == "EC" or usrdata['staff'] == "WM" or usrdata['staff'] == "FE" or usrdata['staff'] == "AEC" or usrdata['staff'] == "AWM" or usrdata['staff'] == "AFE"):
                    staffRole = discord.utils.get(guild.roles,name= "Facility Staff")
                    await user.add_roles(staffRole)

                if (usrdata['staff'] == "WT" or usrdata['staff'] == "ET" or usrdata['staff'] == "FET"):
                    staffRole = discord.utils.get(guild.roles,name= "Facility Team Member")
                    await user.add_roles(staffRole)

                # TRAINING STAFF?
                if(usrdata['mentor']=='Yes' or usrdata['ins']=='Yes'):
                    tStaffRole = discord.utils.get(guild.roles,name= "Training Staff")
                    await user.add_roles(tStaffRole)


                if(usrdata['facility'] == 'ZHQ' or usrdata['facility'] == 'ADM'):
                    dictator = discord.utils.get(guild.roles,name= "VATSIM/VATUSA Staff")
                    await user.add_roles(dictator)

            else:
                # limit user (pilot)
                await user.edit(nick = name)
                await removeAllRoles(user)
                await user.add_roles(discord.utils.get(guild.roles,name= "Pilot"))

            #Populate Embeds
            if live:
                if(not onLIVE):
                    embed = discord.Embed(colour=0x600080, title='LIVE Mode Deactivated', url=site_url)
                    embed.add_field(name='Successfully Deactivate LIVE Mode',
                            value="We have reset your nickname to it's original state. Thank you for abiding by all of the policies and we hope your stream went well. Happy Controlling!",
                            inline=False)
                    embed.set_footer(text='Maintained by the v' + FACILITY_ID + ' Web Services Team')
                else:
                    embed = discord.Embed(colour=0x600080, title='LIVE Mode Activated', url=site_url)
                    embed.add_field(name='Follow The Policies',
                            value='Please remember that your stream is subject to the Facility Operations Policy (https://vats.im/' + FACILITY_ID + '/fop) and VATSIM Code of Conduct (https://vats.im/coc) and to abide by all rules enforcing streams on the Discord and live network respectively.',
                            inline=False)
                    embed.add_field(name='Reset Nickname',
                            value='Once you have finished your streaming, and all of your content is to prestine quality and your audience is contempt you may reset your nickname by re-sending this command (**!live**). Happy Controlling!',
                            inline=False)
                    embed.set_footer(text='Maintained by the v' + FACILITY_ID + ' Web Services Team')
            else:
                embed = discord.Embed(colour=0x32cd32, title='Roles Synced', url=site_url)
                embed.add_field(name='Successfully Synced Roles',
                        value='Thank you for joining the Virtual ' + FACILITY_NAME + ' Discord. Your roles & nickname have been synced according to our ARTCC site.',
                        inline=False)
                embed.set_footer(text='Maintained by the v' + FACILITY_ID + ' Web Services Team')
                
            await user.send(embed=embed)
            return 1
        else:
            embed = discord.Embed(colour=0xf70d1a, title='Account Not Linked', url=site_url)
            embed.add_field(name='Please Link Account',
                    value='If you have not already done so please link your Discord account to our ARTCC site (' + site_url + '), and re-execute the command.',
                    inline=False)
            embed.set_footer(text='Maintained by the v' + FACILITY_ID + ' Web Services Team')
            await user.send(embed=embed)
            return 0
    except: # catch excpets when not matching is found on the website
        print('Error in sycroles. Username:'+ user.display_name + ' ID:'+ str(user.id))
        return -1


async def removeAllRoles(user):
    await user.edit(roles=[])

async def welcomeMessage(message):
    embed = discord.Embed(colour=0xf70d1a, title='Welcome to '+FACILITY_ID, url=site_url)
    embed.add_field(name='Introduction',
                value='Welcome to the Virtual ' + FACILITY_NAME + ' Official Discord Server; the primary communication method for all means regarding the ARTCC. If you are new to the Discord please keep in mind that all means of communications either voice or text are covered under the VATSIM Code of Conduct and the VATSIM Cleveland ARTCC Discord Policy. We want to ensure a safe community and a great experience for our pilots, controllers, and staff to properly communicate, coordinate, navigate, and educate.',
                inline=False)
    embed.add_field(name='Linking Your Site Account',
                value='The Virtual ' + FACILITY_NAME + ' utilizes this Discord Bot, and our facility website (' + site_url + ') to seamlessy and efficiently link the two systems together and provide roles and information effectively to all pilots and home/visiting controllers. If you have not already linked your account please navigate to our site and login, navigating to your "Profile" to link your Discord account to the site; or if not a rostered controller (i.e. pilot): the "Discord" button under your name in the navigation bar.',
                inline=False)
    embed.add_field(name='Linking To Discord',
                value='Once you have properly linked your Discord account to our facility website you may now proceed to the most important step in initially syncing your roles via a command. To properly utilize the system type **!sync**, and let our robots tinker away and grant your roles.',
                inline=False)
    await message.channel.send(embed = embed)
    return

async def spontaneous_embed(message):
    embed = discord.Embed(colour=0x2664D8, title='Spontaneous Training', url=site_url)
    embed.add_field(name='What is Spontaneous Training?',
                value='Spontaneous Training is a venue for both students and training staff to post impromptu training availability in this channel. Do note that this source of availability **DOES NOT** guarantee that you will receive training, but instead is offered as a courtesy on behalf of the training staff. You MUST follow the rules listed below to use this system.',
                inline=False)
    embed.add_field(name='What happens if I have a session scheduled already?',
                value='To be notified of Spontaneous Training availability being posted by training staff, react to this message with a 📢.',
                inline=False)
    embed.add_field(name='How do I get notified?',
                value='Once you have properly linked your Discord account to our facility website you may now proceed to the most important step in initially syncing your roles via a command. To properly utilize the system type **!sync**, and let our robots tinker away and grant your roles.',
                inline=False)
    embed.add_field(name='Note',
                value='This is not a venue to encourage soliciting, and we recommend being respectful when coordinating times with training staff for Spontaneous Training or sessions outside of the normal training schedule available on Setmore. If you have any questions or concerns regarding training, reach out to the Training Administrator (TA) or an appropriate member of the training staff.',
                inline=False)
    embed.add_field(name='Rules',
                value='1.You must be prepared for your session. If you come to a spontaneous training session unprepared, it may result in the loss of privileges to use this system.\n2.**You must be prepared for an immediate start within the availability window that you provide. If you are not ready to start when contacted by a training staff member, your request will be deleted.**\n3.Your availability window must be within 6 hours of your posting and you may not post future availability. Availability must only be posted when you are free.\n4.Do not direct message or tag training staff members unless they reach out to you or have posted their own availability in this channel.\n5.Requests should be made in **Eastern** time.\n6.Messages will be deleted at the end of the day.\n7.There is **NO GUARANTEE** that your request will be picked up. Training staff are all volunteers and will get to your request if they can.',
                inline=False)
    embed.add_field(name='Command for Training Requests',
                value='!treq [Type of Session] t: [Availability Window]\n\nExample: !treq ITG-1 t: 3pm Eastern to 9pm Eastern',
                inline=False)
    msg = await message.channel.send(embed = embed)
    await msg.add_reaction('📢')
    return
async def spontaneous(message,command,guild):
    if (message.channel.id == SP_Channel_ID):
        content = message.content.replace(prefix+command,"")
        limit = []
        if "l:" in message.content:
            decoded = message.content.split("l:")
            limit = decoded[1]

        if limit:
            embed = discord.Embed(
                color=0xFFCC00,
                title="Spontaneous Training Available",
                url=site_url
            )
            embed.add_field(
                name="Training Staff",
                value=f'<@{message.author.id}>',
                inline=False
            )
            embed.add_field(
                name="Date/Time",
                value=decoded[0],
                inline=False
            )
            embed.add_field(
                name="Session Type(s) Unavailable",
                value=limit,
                inline=False
            )
            embed.set_footer(text = 'Maintained by the v'+FACILITY_ID+' Web Services Team and Training Department')
        else:
            embed = discord.Embed(
                color=0xFFCC00,
                title="Spontaneous Training Available",
                url=site_url
            )
            embed.add_field(
                name="Training Staff",
                value=f'<@{message.author.id}>',
                inline=False
            )
            embed.add_field(
                name="Date/Time",
                value=content,
                inline=False
            )
            embed.set_footer(text = 'Maintained by the v'+FACILITY_ID+' Web Services Team and Training Department')

        sp_role = discord.utils.get(guild.roles,name="Spontaneous Training")
        await message.channel.send(f'<@&{sp_role.id}>',embed = embed)
    else:
        await message.author.send("Incorrect Channel")

async def trainingRequest(message,command,guild):
    if (message.channel.id == SP_Channel_ID):
        content = message.content.replace(prefix+command,"")
        if "t:" in content:
            decoded = content.split("t:")
            time = decoded[1]
            embed = discord.Embed(
                color=0xFFCC00,
                title="Spontaneous Training Available",
                url=site_url
            )
            embed.add_field(
                name="Student",
                value=f'<@{message.author.id}>',
                inline=False
            )
            embed.add_field(
                name="Session Type",
                value=decoded[0],
                inline=False
            )
            embed.add_field(
                name="Date/Time",
                value=time,
                inline=False
            )
            embed.set_footer(text = 'Maintained by the v'+FACILITY_ID+' Web Services Team and Training Department')
            await message.channel.send(embed = embed, delete_after=432000) #auto delete after 12 hrs
        else:
            await message.author.send('**ERROR**\n Missing Parameter')
    else:
        await message.author.send('**ERROR**\n Incorrect Channel')


async def activity(message,client):
    count = 0
    embed = discord.Embed(colour=0xFF2E2E, title='Activity Notification', url=site_url)
    embed.add_field(name='Reminder of Activity',
                value='Hello! You are receiving this notification as you have yet to fulfill your activity requirements for v' + FACILITY_ID + ' this month! We encourage you to get on position or schedule a training session at the next available time prior to the end of calendar month in order to fulfill your activity requirements. A reminder that we have, on a standard month, at least one host or support events that you are able to look forward to this next upcoming month alongside various days of training slot times that you can take advantage of to further your virtual air traffic career. We would hate to lose you as a controller within our facility as each and every member is a vital part of both the air traffic operations and also the community within!',
                inline=False)
    embed.add_field(name='inimum Activity Requirement (OBS)',
                value='If you are an Observer (OBS), it is required per 7210.3 to fulfill at least one complete training session each calendar month.',
                inline=False)
    embed.add_field(name='Minimum Activity Requirement (S1+)',
                value='If you are a Student 1 (S1) rated controller or higher, it is required per 7210.3 to fulfill two hours on a live position each calendar month.',
                inline=False)
    embed.add_field(name='Leave of Absence',
                value='If you are unable to meet the activity requirements you may request a Leave of Absence (LOA) per 7210.3 3.4. The minimum length for a LOA is 30 days and the maximum length is 90 days. Controllers in active duty military/armed forces will be permitted up to 24 months of LOA for miltary related deployment or duties but they must complete a checkout with the TA or Instructor upon their return.',
                inline=False)
    
    query = message.content.replace(prefix+'activity ',"")
    query = query.replace(" ",",")
    users = webQuery(site_url + '/api/data/bot/search/?ois='+query,site_token)
    for usrid in users:
        if (usrid):
            user = await client.fetch_member(usrid)
            if (user):
                await user.send(embed = embed)
                count += 1
        else:
            print("User Not Found!")
    
    await message.reply('Sent '+str(count)+ ' activity message(s).')
    return

async def removeroles(message,guild):
    count = 0
    query = message.content.replace(prefix+'removeroles ',"")
    query = query.replace(" ",",")
    users = webQuery(site_url + '/api/data/bot/search/?ois='+query,site_token)
    for usrid in users:
        if (usrid):
            user = await guild.fetch_member(usrid)
            if (user):
                await user.edit(roles=[])
                await user.add_roles(await discord.utils.get(guild.roles,name= "VATSIM Controller"))
                count += 1
        else:
            print("User Not Found!")
    
    await message.reply('Removed '+str(count)+ ' role(s).')
    return

async def addEvent(message,guild):
    eventid = message.content.lower().replace(prefix+'addevent ',"")
    query = site_url+'/api/data/bot/event.php?event_id='+str(eventid)
    event = webQuery(query,site_token)
    if (not event['id']=='None'):
        startTime = datetime.strptime(event['event_date']+' '+event['time_start'] + ' +0000','%Y-%m-%d %H%M %z')
        endTime = datetime.strptime(event['event_date']+' '+event['time_end'] + ' +0000','%Y-%m-%d %H%M %z')

        if(endTime<startTime):
            endTime += timedelta(days=1)

        if(len(event['description'])>1000):
            event['description'] = event['description'][0:996]+'...'

        event_img = requests.get(event['banner_path']).content

        channel = await guild.fetch_channel(964655381932539914) # breifing room

        await guild.create_scheduled_event(name=event['name'], 
                                           entity_type = discord.EntityType['voice'],
                                           channel = channel,
                                           start_time=startTime,
                                           privacy_level = discord.PrivacyLevel['guild_only'],
                                           end_time=endTime,
                                           description=event['description'],
                                           image = bytearray(event_img),
                                           )
        await message.author.send("Event Added!")
    else:
        await message.author.send(f"**ERROR**\nEvent {eventid} Not Found")

async def debugMsg(message):
    embed = discord.Embed(colour=0x2664D8, title='Spontaneous Training', url=site_url)
    embed.add_field(name='Debug Message',
                value=message.content.lower().replace(prefix+'debugmsg ',""),
                inline=False)
    await message.author.send(embed = embed)
    return


async def waitlist(guild):
        channel = await guild.fetch_channel(int(SNR_Channel_ID))

        # fetch count info
        query = site_url+'/api/data/bot/vis_loa.php?'
        counts = webQuery(query,site_token)
        # create embed msg
        if (int(counts['visit']) and int(counts['loa'])):
            embed = discord.Embed(colour=0x2664D8, title='Bi-Daily Waitlist Information', url=site_url)
            embed.add_field(name='Visitor Apllication',
                        value=f"{counts['visit']} Pending Visitor Apllication(s)",
                        inline=False)
            embed.add_field(name='LOA Request',
                        value=f"{counts['loa']} Pending LOA Request(s)",
                        inline=False)
        elif(int(counts['visit'])):
            embed = discord.Embed(colour=0x2664D8, title='Waitlist Information', url=site_url)
            embed.add_field(name='Visitor Apllication',
                        value=f"{counts['visit']} Pending Visitor Apllication(s)",
                        inline=False)
        elif(int(counts['loa'])):
            embed = discord.Embed(colour=0x2664D8, title='Waitlist Information', url=site_url)
            embed.add_field(name='LOA Request',
                        value=f"{counts['loa']} Pending LOA Request(s)",
                        inline=False)
        else:
            return
        await channel.send(embed = embed)