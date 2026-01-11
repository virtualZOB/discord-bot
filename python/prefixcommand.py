from webQuery import getPFieldStatus, schedulerQuery, webQuery_async
import configparser
import discord
from datetime import datetime, timedelta
import requests
import pytz
import asyncio
from typing import Optional

from time import time
import html

configname = 'DEFAULT'
configs = configparser.ConfigParser()
configs.read('config.ini')
config = configs[configname]

prefix          = config['prefix']
site_token      = config['site_token']
discord_token   = config['token']
scheduler_token = config['scheduler_token']
scheddy_token   = config['SCHEDDY_API_MASTER_KEY']
site_url        = config['site_url']
guild_id        = int(config['guild_id'])
FACILITY_ID     = config['FACILITY_ID']
FACILITY_NAME   = config['FACILITY_NAME']
SNR_Channel_ID  = int(config['SNR_Channel_ID'])

DTW_SB_ID = int(config['DTW_SB'])
CLE_SB_ID = int(config['CLE_SB'])
PIT_SB_ID = int(config['PIT_SB'])
BUF_SB_ID = int(config['BUF_SB'])

_last_workload_alert: dict[str, float] = {}

Relief_Subscribe_Message_ID = int(config.get("Relief_Subscribe_Message_ID", "0"))
Relief_Subscribe_Emoji = config.get("Relief_Subscribe_Emoji", "📣")

UTC = pytz.UTC

FLAG_KEY = {
    "S1": "s1",
    "S2": "s2",
    "S3": "s3",
    "C1": "c1",
    "C3": "c3",
}

RANK = {"OBS": 0, "S1": 1, "S2": 2, "S3": 3, "C1": 4, "C3": 5}

async def syncroles(user, guild , live = False):
    query = site_url+'/api/data/bot/?discord_id='+str(user.id)
    try:
        usrdata = await webQuery_async(query,site_token)
        
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
                        if (usrdata['mentor_name'] == 'Mentor'):
                            fullname = name + ' | MTR'; 
                        else:
                            fullname = name + ' | MIT'; 
                            role = discord.utils.get(guild.roles,name= "MIT")
                            await user.add_roles(role)
                    if (usrdata['ins'] == 'Yes'):
                        fullname = name + ' | INS'; 
                        role = discord.utils.get(guild.roles,name= "Instructors")
                        await user.add_roles(role)
                    if (not usrdata['staff'] == ''):
                        fullname = name + ' | '+ usrdata['staff']

                await user.edit(nick = fullname)
                # REMOVE ROLES
                await removeAllRoles(user)

                # ADD ROLES 
                role = discord.utils.get(guild.roles,name= "VATSIM Controller")
                await user.add_roles(role)

                if(usrdata['type']=='vis'):
                    primRole = discord.utils.get(guild.roles,name="Visiting Controller")
                else:
                    primRole = discord.utils.get(guild.roles,name= FACILITY_ID+ " Controller")
                await user.add_roles(primRole)

                # FACILITY STAFF?
                if (usrdata['staff'] == "EC" or usrdata['staff'] == "WM" or usrdata['staff'] == "FE" or usrdata['staff'] == "AEC" or usrdata['staff'] == "AWM" or usrdata['staff'] == "AFE"):
                    staffRole = discord.utils.get(guild.roles,name= "ZOB Facility Staff")
                    await user.add_roles(staffRole)

                if (usrdata['staff'] == "WT" or usrdata['staff'] == "ET" or usrdata['staff'] == "FET"):
                    staffRole = discord.utils.get(guild.roles,name= "ZOB Facility Staff")
                    await user.add_roles(staffRole)

                # TRAINING STAFF?
                if((usrdata['mentor']=='Yes' and usrdata['mentor_name'] == 'Mentor') or usrdata['ins']=='Yes'):
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
    except Exception as e: # catch excpets when not matching is found on the website
        print('Error in sycroles. Username:'+ user.display_name + ' ID:'+ str(user.id))
        print(e)
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

async def optionalRolesMessage(guild):
    channel = discord.utils.get(guild.channels,name="role-assignments")
    embed = discord.Embed(colour=0x2664D8, title='Optional Roles')
    embed.add_field(name='Why Optional Roles?',
                value='Optional roles in Discord help reduce unwanted pings by letting members choose which notifications they receive. This prevents notification fatigue, avoids overusing @everyone mentions, and ensures messages reach only interested users, creating a cleaner and more respectful server experience.',
                inline=False)
    embed.add_field(name='Group Flight Role ✈️',
            value='Click this role to sign up for community group flights—all pilots are welcome.',
            inline=False)
    embed.add_field(name='Game Night Role 🎮',
            value='Click this role to join community game nights—all users are welcome.',
            inline=False)
    embed.set_footer(text = 'Maintained by the v'+FACILITY_ID+' Web Services Team')

    msg = await channel.send(embed = embed)
    await msg.add_reaction('✈️')
    await msg.add_reaction('🎮')


async def spontaneous_embed(message):
    embed = discord.Embed(colour=0x2664D8, title='Spontaneous Training', url=site_url)
    embed.add_field(name='What is Spontaneous Training?',
                value='Spontaneous Training is a venue for both students and training staff to post impromptu training availability in this channel. Do note that this source of availability **DOES NOT** guarantee that you will receive training, but instead is offered as a courtesy on behalf of the training staff. You MUST follow the rules listed below to use this system.',
                inline=False)
    embed.add_field(name='What happens if I have a session scheduled already?',
                value='If you already have a session scheduled and you place interest for Spontaneous Training, your previous session will not be canceled and you may keep that session at your discretion. Do note that students that do not have a session scheduled may get priority over those that have a session scheduled on setmore.',
                inline=False)
    embed.add_field(name='How do I get notified?',
                value='To be notified of Spontaneous Training availability being posted by training staff, react to this message with a 📢.',
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
    if (message.channel.name == "spontaneous-training"):
        content = message.content.replace(prefix+command,"")
        limit = []
        if "l:" in message.content:
            decoded = content.split("l:")
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
    if (message.channel.name == "spontaneous-training"):
        content = message.content.replace(prefix+command,"")
        if "t:" in content:
            decoded = content.split("t:")
            time = decoded[1]
            embed = discord.Embed(
                color=0xFFCC00,
                title="Training Request",
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
            await message.channel.send(embed = embed, delete_after=432000.0) #auto delete after 12 hrs
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
                value='If you are a Student 1 (S1) rated controller or higher, it is required per 7210.3 to fulfill THREE hours on a live position each quarter.',
                inline=False)
    embed.add_field(name='Leave of Absence',
                value='If you are unable to meet the activity requirements you may request a Leave of Absence (LOA) per 7210.3 3.4. The minimum length for a LOA is 30 days and the maximum length is 90 days. Controllers in active duty military/armed forces will be permitted up to 24 months of LOA for miltary related deployment or duties but they must complete a checkout with the TA or Instructor upon their return.',
                inline=False)
    
    query = message.content.replace(prefix+'activity ',"")
    query = query.replace(" ",",")
    users = await webQuery_async(site_url + '/api/data/bot/search/?ois='+query,site_token)
    for usrid in users:
        if (usrid):
            user = await client.fetch_member(usrid)
            if (user):
                await user.send(embed = embed)
                count += 1
        else:
            print("User Not Found!"+str(usrid))
    
    await message.reply('Sent '+str(count)+ ' activity message(s).')
    return

async def removeroles(message,guild):
    count = 0
    query = message.content.replace(prefix+'removeroles ',"")
    query = query.replace(" ",",")
    users = await webQuery_async(site_url + '/api/data/bot/search/?ois='+query,site_token)
    for usrid in users:
        if (usrid):
            try:
                user = await guild.fetch_member(usrid)
                if (user):
                    await user.edit(roles=[])
                    role = discord.utils.get(guild.roles,name="Pilot")
                    await user.add_roles(role)
                    count += 1
            except Exception as e:
                print("error in removeroles():" + e)
        else:
            print("User Not Found!"+str(usrid))
    
    await message.reply('Removed '+str(count)+ ' role(s).')
    return

async def addEvent(message,guild):
    eventid = message.content.lower().replace(prefix+'addevent ',"")
    query = site_url+'/api/data/bot/event.php?event_id='+str(eventid)
    event = await webQuery_async(query,site_token)
    if (not event['id']=='None'):
        startTime = datetime.strptime(event['time_start'] + '+0000','%Y-%m-%dT%H:%M%z')
        endTime = datetime.strptime(event['time_end']+ '+0000','%Y-%m-%dT%H:%M%z')

        if(endTime == startTime):
            endTime += timedelta(hours=4)
            
        if(endTime<startTime):
            endTime += timedelta(days=1)

        #special charactors
        description_text = html.unescape(event['description']).replace('<br>','\n').replace('<strong>','**').replace('</strong>','**')
        
        # Maximum charactor for event description
        if(len(description_text)>1000):
            description_text = description_text[0:996]+'...'

        event_img = requests.get(event['banner_path']).content

        channel = discord.utils.get(guild.channels, name="Briefing Room") # breifing room

        await guild.create_scheduled_event(name=html.unescape(event['name']), 
                                           entity_type = discord.EntityType['voice'],
                                           channel = channel,
                                           start_time=startTime,
                                           privacy_level = discord.PrivacyLevel['guild_only'],
                                           end_time=endTime,
                                           description=description_text,
                                           image = bytearray(event_img),
                                           )
        await message.author.send("Event Added!")
    else:
        await message.author.send(f"**ERROR**\nEvent {eventid} Not Found")

async def debugMsg(message):
    embed = discord.Embed(colour=0x2664D8, title='Debug Message', url=site_url)
    embed.add_field(name='Debug Message',
                value=message.content.lower().replace(prefix+'debugmsg ',""),
                inline=False)
    await message.author.send(embed = embed)
    return

async def waitlist(guild):
        #channel = discord.utils.get(guild.channels, name="Senior Channel")
        channel = discord.utils.get(guild.channels, id=SNR_Channel_ID)

        # fetch count info
        query = site_url+'/api/data/bot/vis_loa.php?'
        counts = await webQuery_async(query,site_token)
        # create embed msg
        if (int(counts['visit']) and int(counts['loa'])):
            embed = discord.Embed(colour=0x2664D8, title='Daily Waitlist Information', url=site_url)
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
        if channel:
            await channel.send(embed = embed)

async def deleteTreq(L_TREQ):
    for req in L_TREQ:
        if (time()-req[1])>43200:
            try:
                await req[0].delete() #delete the message
            except Exception as e:
                print("Error in deleteTreq(): ")
                print(e)
            finally:
                L_TREQ.remove(req) # remove from queue

    return L_TREQ

async def closethread(message,guild):
    #check if it is a thread
    if isinstance(message.channel,discord.channel.Thread):
        channel = message.channel
        await message.delete()
        await channel.send("It looks like this thread is no longer needed, so I'm going to close the thread now. Thanks again for the suggestion. If you have further concerns or wish to reopen this suggestion, please create a new issue thread.")
        await channel.edit(archived=True, locked=True)

async def updateStatusBoard(guild):
    fileds = ["DTW","CLE","PIT","BUF"]
    IDS = [DTW_SB_ID,CLE_SB_ID,PIT_SB_ID,BUF_SB_ID]
    for i in range(len(fileds)):
        try:
            id = IDS[i]
            channel = guild.get_channel(id)

            query = await getPFieldStatus()

            #populate name
            name = fileds[i] + " -- Dep: " + str(int(query[fileds[i].lower()+"_d"])) + "  Arr: " +  str(int(query[fileds[i].lower()+"_a"]))
            await channel.edit(name = name, reason = "Status board update")
        
        except Exception as e:
            print("error in updateStatusBoard(): ") 
            print(e)
        

async def sendTrainingReminder(guild):

    # Get Sessions from Scheddy
    bookings = await schedulerQuery(
        "https://scheddy.clevelandcenter.org/api/allSessions",
        scheddy_token
    )

    now_utc = datetime.now(UTC)

    for booking in bookings or []:
        try:
            session = booking["session"]
            mentor = booking["mentor"]
            sessionType = booking["sessionType"]

            if session.get("cancelled"):
                continue

            # Parse ISO Zulu time
            start_str = session["start"]
            start_utc = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(UTC)

            # within next 24 hours
            if not (timedelta(0) < (start_utc - now_utc) < timedelta(days=1)):
                continue

            # Get discord info
            provider_id = await webQuery_async(
                f"{site_url}/api/data/bot/user.php?cid={session['mentor']}",
                key=site_token
            )
            customer_id = await webQuery_async(
                f"{site_url}/api/data/bot/user.php?cid={session['student']}",
                key=site_token
            )

            provider_dc = None
            if provider_id and provider_id.get("discord_id"):
                provider_dc = guild.get_member(int(provider_id["discord_id"]))

            customer_dc = None
            if customer_id and customer_id.get("discord_id"):
                customer_dc = guild.get_member(int(customer_id["discord_id"]))

            # Discord timestamp
            unix_ts = int(start_utc.timestamp())
            discord_time = f"<t:{unix_ts}:F>  •  <t:{unix_ts}:R>"
            zulu_time = start_utc.strftime("%Y-%m-%d %H:%MZ")

            # Mentor embed
            embedMentor = discord.Embed(colour=0x2664D8, title="Training Session Reminder")
            embedMentor.add_field(name="Session Name", value=str(sessionType.get("name","")), inline=False)
            embedMentor.add_field(name=f"Date/Time (Local Time)", value=discord_time, inline=False)
            embedMentor.add_field(name="Date/Time (Zulu)", value=zulu_time, inline=False)
            embedMentor.add_field(
                name="Instructor/Mentor",
                value=(provider_dc.mention if provider_dc else f"{mentor.get('firstName','')} {mentor.get('lastName','')}".strip()),
                inline=False
            )
            embedMentor.add_field(
                name="Student",
                value=(customer_dc.mention if customer_dc else str(session.get("student"))),
                inline=False
            )
            embedMentor.set_footer(text=f"Maintained by the v{FACILITY_ID} Web Services Team")

            if provider_dc:
                await provider_dc.send(embed=embedMentor)

            # Student embed
            embedStudent = discord.Embed(colour=0x2664D8, title="Training Session Reminder")
            embedStudent.add_field(name="Session Name", value=str(sessionType.get("name","")), inline=False)
            embedStudent.add_field(name=f"Date/Time (Local Time)", value=discord_time, inline=False)
            embedStudent.add_field(name="Date/Time (Zulu)", value=zulu_time, inline=False)
            embedStudent.add_field(
                name="Instructor/Mentor",
                value=(provider_dc.mention if provider_dc else f"{mentor.get('firstName','')} {mentor.get('lastName','')}".strip()),
                inline=False
            )
            embedStudent.add_field(
                name="Student",
                value=(customer_dc.mention if customer_dc else str(session.get("student"))),
                inline=False
            )
            embedStudent.set_footer(text=f"Maintained by the v{FACILITY_ID} Web Services Team")

            if customer_dc:
                await customer_dc.send(embed=embedStudent)

        except Exception as e:
            print("error in sendTrainingReminder():")
            print(e)

async def myAppointment(message,guild):
    hasSession = False
    try:
        user = await webQuery_async(site_url + '/api/data/bot/discordID2CID.php?discord_id='+str(message.author.id),key = site_token)
        
        if not user:
            await message.author.send(content = "I cannot find your information in the scheduling system")
            return
        
        bookings = await schedulerQuery(
            "https://scheddy.clevelandcenter.org/api/userSessions/" + str(user['cid']),
            scheddy_token
         )

        now_utc = datetime.now(UTC)

        for booking in bookings:

            session = booking["session"]
            mentor = booking["mentor"]
            sessionType = booking["sessionType"]

            # Parse ISO Zulu time
            start_str = session["start"]
            start_utc = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(UTC)

            # Ignore sessions in the past
            if start_utc <= now_utc:
                continue
            
            hasSession = True

            # Discord timestamp
            unix_ts = int(start_utc.timestamp())
            discord_time = f"<t:{unix_ts}:F>  •  <t:{unix_ts}:R>"
            zulu_time = start_utc.strftime("%Y-%m-%d %H:%MZ")

            # Get discord info
            provider_id = await webQuery_async(
                f"{site_url}/api/data/bot/user.php?cid={session['mentor']}",
                key=site_token
            )
            customer_id = await webQuery_async(
                f"{site_url}/api/data/bot/user.php?cid={session['student']}",
                key=site_token
            )

            provider_dc = None
            if provider_id and provider_id.get("discord_id"):
                provider_dc = guild.get_member(int(provider_id["discord_id"]))

            customer_dc = None
            if customer_id and customer_id.get("discord_id"):
                customer_dc = guild.get_member(int(customer_id["discord_id"]))

            # Build message
            embed = discord.Embed(colour=0x2664D8, title="Training Session Reminder")
            embed.add_field(name="Session Name", value=str(sessionType.get("name","")), inline=False)
            embed.add_field(name=f"Date/Time (Local Time)", value=discord_time, inline=False)
            embed.add_field(name="Date/Time (Zulu)", value=zulu_time, inline=False)
            embed.add_field(
                name="Instructor/Mentor",
                value=(provider_dc.mention if provider_dc else f"{mentor.get('firstName','')} {mentor.get('lastName','')}".strip()),
                inline=False
            )
            embed.add_field(
                name="Student",
                value=(customer_dc.mention if customer_dc else str(session.get("student"))),
                inline=False
            )
            embed.set_footer(text=f"Maintained by the v{FACILITY_ID} Web Services Team")

            # Send the message
            await message.author.send(embed = embed)

        # If no session found, inform the user
        if hasSession == False:
            embed = discord.Embed(colour=0xf70d1a, title='Your Upcoming Training Session')
            embed.add_field(name='Session Information',
                    value='You do not have a session scheduled currently.',
                    inline=False)
            await message.author.send(embed = embed)
        
    except Exception as e:
        print ("error 2 in myAppointment():")
        print(e)

        await message.author.send(content = "There is an error occurs when getting the data. Please try again later.")


async def reliefEmbed(guild):
    channel = discord.utils.get(guild.channels,name="relief")
    embed = discord.Embed(colour=0x2664D8, title='Relief Rules')
    embed.add_field(name='What is this?',
                value='This channel is designated for relief calls when you are closing or requesting underlying facility coverage due to high demand. Access to this function is currently limited to **S3 and above**.',
                inline=False)
    embed.add_field(name='How to use is?',
            value=("**!relief [time]** – Notify others when you are requesting relief\n"
                    "**!closing [time]** – Notify when you are closing your position\n"
                    "**!helpme [position]** – Request coverage for a specific underlying facility"),
            inline=False)
    embed.set_footer(text = 'Maintained by the v'+FACILITY_ID+' Web Services Team')

    msg = await channel.send(embed = embed)


async def requestRelief(message, command, guild, alert_type):
    try:
        try:
            user = await webQuery_async(site_url + '/api/data/bot/discordID2CID.php?discord_id='+str(message.author.id),key = site_token)
        except Exception as e:
            print("discordID2CID fetch failed:", e)
            return await message.author.send("**ERROR**\n Unable to look up your CID right now.")

        if not user:
            return await message.author.send(content = "I cannot find your information in the system. Please link your discord with the ZOB website.")
        
        if not has_rating_at_least(user or {}, "S3", require_full=False):
            return await message.author.send(content="You must be S3 or above to request relief.")

        Relief_Channel_ID = discord.utils.get(guild.channels,name = "relief") 
        Relief_Channel_ID = Relief_Channel_ID.id
        if message.channel.id != Relief_Channel_ID:
            await message.author.send(message.channel.id)
            await message.author.send(Relief_Channel_ID)
            return await message.author.send("**ERROR**\n Incorrect Channel")

        # Example message: "!relief 15 mins"
        # Remove the command token only once
        eta_text = message.content.replace(prefix + command, "", 1).strip()

        if not eta_text:
            return await message.author.send("**ERROR**\n Missing time or position. Example: `!relief 15 mins`")

        # 1) Get CID from Discord ID
        if not user or not user.get("cid"):
            return await message.author.send("**ERROR**\n I cannot find your CID (is your account linked?).")

        try:
            cid = int(user["cid"])
        except Exception:
            return await message.author.send("**ERROR**\n CID returned was invalid.")

        # 2) Pull workload API
        try:
            workload = await webQuery_async(
                site_url + "/api/data/ids/workload?json=1",
                key=site_token
            )
        except Exception as e:
            print("workload fetch failed:", e)
            return await message.author.send("**ERROR**\n Unable to read workload data right now.")

        buckets = (workload or {}).get("controllers", [])
        if not isinstance(buckets, list) or not buckets:
            return await message.author.send("**ERROR**\n Workload data was empty.")

        # 3) Match CID inside workload controllers
        match_bucket = None
        match_ctrl = None

        for b in buckets:
            for c in (b or {}).get("controllers", []) or []:
                try:
                    if int(c.get("cid", -1)) == cid:
                        match_bucket = b
                        match_ctrl = c
                        break
                except Exception:
                    continue
            if match_bucket:
                break

        if not match_bucket or not match_ctrl:
            return await message.author.send("**ERROR**\n I don’t see you on an active frequency right now.")

        callsign = match_ctrl.get("callsign") or match_ctrl.get("vnas_callsign") or "UNKNOWN"
        freq = (match_bucket.get("frequency") or "").strip()

        pilot_count = match_bucket.get("pilot_count")
        if pilot_count is None:
            pilot_count = len(match_bucket.get("pilots") or [])
        pilot_count = int(pilot_count)

        # Optional: don't rate-limit manual relief requests
        cooldown = 0

        sent = await send_relief_workload_alert(
            alert_type=alert_type,
            guild=guild,
            callsign=callsign,
            on_frequency=pilot_count,
            frequency=freq,
            cooldown_seconds=cooldown,
            eta=eta_text,
        )

        if not sent:
            return await message.author.send("**ERROR**\n Relief request was not sent (cooldown or channel issue).")
        
    except Exception as e:
            print("error in requestRelief():")
            print(e)

def required_rating_for_callsign(callsign: str) -> str:
    cs = (callsign or "").upper()
    if "CTR" in cs:
        return "C1"
    if "APP" in cs or "DEP" in cs:
        return "S3"
    if "TWR" in cs:
        return "S2"
    if "GND" in cs:
        return "S1"
    return "S1"

def _cert_value(payload: dict, code: str) -> str:
    key = FLAG_KEY.get(code)
    if not key:
        return ""
    return str(payload.get(key, "")).strip().lower()

def has_rating_at_least(payload: dict, required_code: str, require_full: bool) -> bool:
    """
    True if payload shows the controller has required_code or higher.
    If require_full=True, the matching level must be "full" (not "mine").
    Otherwise, "mine" OR "full" counts.
    """
    required_rank = RANK.get(required_code, 0)

    # check from highest down, so higher certs satisfy lower requirements
    for code, rank in sorted(RANK.items(), key=lambda kv: kv[1], reverse=True):
        if rank < required_rank:
            continue
        if code == "OBS":
            continue

        v = _cert_value(payload, code)
        if not v:
            continue

        if require_full:
            if v == "full":
                return True
        else:
            if v in ("mine", "full"):
                return True

    return False

def rating_from_user_payload(user: dict) -> str:
    if not user:
        return "OBS"

    # Highest-to-lowest
    flag_order = [("C3", "c3"), ("C1", "c1"), ("S3", "s3"), ("S2", "s2"), ("S1", "s1")]
    for code, key in flag_order:
        v = user.get(key)
        if v is None:
            continue
        if str(v).strip() not in (""):
            return code

    # Fallback if your endpoint ever includes a direct rating string
    r = (user.get("rating") or "").strip().upper()
    return r


async def get_subscribed_users_from_reaction(
    *,
    channel: discord.abc.Messageable,
    message_id: int,
    emoji: str,
) -> list[discord.User]:
    if not message_id:
        return []

    try:
        sub_msg = await channel.fetch_message(message_id)
    except Exception as e:
        print(f"Failed to fetch subscribe message {message_id}: {e}")
        return []

    target = None
    for r in sub_msg.reactions:
        if str(r.emoji) == str(emoji):
            target = r
            break

    if target is None:
        return []

    users: list[discord.User] = []
    try:
        async for u in target.users(limit=None):
            if not getattr(u, "bot", False):
                users.append(u)
    except Exception as e:
        print(f"Failed reading reaction users: {e}")

    return users


async def build_relief_ping_list(
    *,
    guild: discord.Guild,
    channel: discord.TextChannel,
    callsign: str,
) -> list[str]:
    required = required_rating_for_callsign(callsign)
    require_full = ("DTW" in (callsign or "").upper())

    reacted_users = await get_subscribed_users_from_reaction(
        channel=channel,
        message_id=Relief_Subscribe_Message_ID,
        emoji=Relief_Subscribe_Emoji,
    )
    if not reacted_users:
        return []

    sem = asyncio.Semaphore(10)

    async def check_one(u: discord.User) -> Optional[str]:
        async with sem:
            try:
                payload = await webQuery_async(
                    site_url + "/api/data/bot/discordID2CID.php?discord_id=" + str(u.id),
                    key=site_token
                )
            except Exception:
                return None

            if has_rating_at_least(payload or {}, required, require_full=require_full):
                m = guild.get_member(u.id)
                return (m.mention if m else f"<@{u.id}>")
            return None

    results = await asyncio.gather(*(check_one(u) for u in reacted_users), return_exceptions=True)
    return [r for r in results if isinstance(r, str) and r]



async def send_relief_workload_alert(
    *,
    alert_type: str,              # "workload" or "relief" or "closing"
    guild: discord.Guild,
    callsign: str,
    on_frequency: int,
    frequency: Optional[str] = None,
    cooldown_seconds: int = 20 * 60,
    eta: Optional[str] = None,
) -> bool:
    if not callsign:
        return False

    key = f"{alert_type}|{callsign}|{frequency or ''}"
    now = time()
    last = _last_workload_alert.get(key, 0.0)
    if (now - last) < cooldown_seconds:
        return False
    _last_workload_alert[key] = now

    channel = discord.utils.get(guild.channels, name="relief")
    if channel is None:
        print("Channel not found in send_relief_workload_alert()")
        return False

    title = "Controller Assistance Alert"
    if alert_type == "workload":
        title = "Controller Workload is High"
    elif alert_type == "relief":
        title = "Controller Relief Requested"
    elif alert_type == "closing":
        title = "Controller Needs to Close Soon"

    embed = discord.Embed(title=title, description="", color=0x2664D8)
    embed.add_field(name="Callsign", value=str(callsign), inline=False)

    if frequency:
        embed.add_field(name="Frequency", value=str(frequency), inline=True)

    embed.add_field(name="Active on Frequency", value=str(on_frequency), inline=True)

    if eta:
        if alert_type == "workload":
            embed.add_field(name="Requesting help on", value=str(eta), inline=False)
        else:
            embed.add_field(name="Relieve by (ETA)", value=str(eta), inline=False)

    embed.set_footer(text=f"Maintained by the v{FACILITY_ID} Web Services Team")

    content = None

    #mentions = await build_relief_ping_list(guild=guild, channel=channel, callsign=callsign)

    content = "@here"

    '''
    # If content is huge, split it (Discord 2000 char limit)
    if content and len(content) > 1900:
        chunks = []
        cur = ""
        for m in content.split():
            if len(cur) + len(m) + 1 > 1900:
                chunks.append(cur.strip())
                cur = ""
            cur += m + " "
        if cur.strip():
            chunks.append(cur.strip())

        # First chunk gets the embed
        await channel.send(
            content=chunks[0],
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True, everyone=True),
            delete_after=3600.0
        )
        # Remaining chunks mention only
        for ch in chunks[1:]:
            await channel.send(
                content=ch,
                allowed_mentions=discord.AllowedMentions(users=True, everyone=True),
                delete_after=3600.0
            )
        return True
    '''
    await channel.send(
        content=content,
        embed=embed,
        allowed_mentions=discord.AllowedMentions(users=True, everyone=True),
        delete_after=3600.0
    )
    return True

