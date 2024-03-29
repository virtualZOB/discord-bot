require('dotenv').config({path: '../'});
const   Discord     = require('discord.js'),
        axios       = require('axios'),
        client      = new Discord.Client();

// GETTING: Environment Variables
const   site_token  = process.env.site_token,
        site_url    = process.env.site_url,
        guild_id    = process.env.guild_id,
        FACILITY_ID = process.env.FACILITY_ID,
        FACILITY_NAME = process.env.FACILITY_NAME;

// SETTING: Arrays
const ratings = [
    'ADM',
    'SUP',
    'I3',
    'I1',
    'C3',
    'C1',
    'S3',
    'S2',
    'S1',
    'OBS'
];

const roles = [
    'Visiting Controller',
    FACILITY_ID + ' Controller',
    'Pilot'
];

const DELAYINMILLISEC = 43200000; //24 hrs

module.exports = {
    syncroles: async function (discord_id, message, live) {
        try {
            const response = await axios.get(site_url + '/api/data/bot/?discord_id=' + discord_id + '&key=' + site_token);

            const user = response.data;

            if (user.status !== "None") {
                if (user.type !== 'lim') {
                    // HOME or VISITING controller

                    if (user.pref_name == '') {
                        if (user.discord_nick_pref > 0) {
                            var name = user.first_name;
                        } else {
                            var name = user.first_name + ' ' + user.last_name;
                        }
                    } else {
                        var pref_split = user.pref_name.split(' ');

                        if (user.discord_nick_pref > 0) {
                            var name = pref_split[0];
                        } else {
                            var name = pref_split[0] + ' ' + pref_split[1];
                        }
                    }

                    const type = user.type;
                    const facility = user.facility;

                    // Nickname (START)
                    if (type === "loa") {
                        var nickname = name + ' | ' + facility; 
                    } else {
                        var nickname = name + ' | ' + user.initials;
                    }

                    if (user.facility === 'ZHQ') {
                        var nickname = name + ' | VATUSA#'; 
                    }

                    if (user.rating === 'ADM') {
                        var nickname = name + ' | VAT???#'; 
                    }
                    
                    if (user.mentor == 'Yes') {
                        var nickname = name + ' | MTR'; 
                    }

                    if (user.ins == 'Yes') {
                        var nickname = name + ' | INS'; 
                    }

                    if (user.staff !== '') {
                        var nickname = name + ' | ' + user.staff;
                    }

                    // LIVE Functionality (S)
                    if (live === true) {
                        if (message.member.displayName.includes('LIVE') == true) {
                            // Do Nothing
                        } else {
                            var nickname = name + ' | LIVE';
                        }
                    }
                    // LF (E)

                    // Nickname (END)

                    // Roles (START)
                    if (type === "vis") {
                        var prim_role = message.guild.roles.cache.find(role => role.name === "Visiting Controller");
                    } else {
                        var prim_role = message.guild.roles.cache.find(role => role.name === FACILITY_ID + " Controller");
                    }

                    if (user.staff === "EC" || user.staff === "WM" || user.staff === "FE" || user.staff === "AEC" || user.staff === "AWM" || user.staff === "AFE") {
                        var staff_role = message.guild.roles.cache.find(role => role.name === "Facility Staff");
                    }

                    if (user.staff === "WT" || user.staff === "ET" || user.staff === "FET") {
                        var staff_role = message.guild.roles.cache.find(role => role.name === "Facility Team Member");
                    }
                    // Roles (END)

                    // Removing (START)
                    ratings.forEach(rating_name => {
                        message.member.roles.remove(message.guild.roles.cache.find(role => role.name === rating_name));
                    });

                    roles.forEach(role_name => {
                        message.member.roles.remove(message.guild.roles.cache.find(role => role.name === role_name));
                    });
                    // Removing (END)

                    // Assigning (START)
                    message.member.roles.add(message.guild.roles.cache.find(role => role.name === "VATSIM Controller"));
                    message.member.roles.add(message.guild.roles.cache.find(role => role.name === user.rating));
                    message.member.roles.add(prim_role);

                    if (staff_role) {
                        message.member.roles.add(staff_role);
                    }

                    if (user.mentor == 'Yes' || user.ins == 'Yes') {
                        message.member.roles.add(message.guild.roles.cache.find(role => role.name === "Training Staff"));
                    }

                    if (user.facility === 'ZHQ' || user.rating === 'ADM') {
                        message.member.roles.add(message.guild.roles.cache.find(role => role.name === "VATSIM/VATUSA Staff"));
                    }
                    message.member.setNickname(nickname);
                    // Assigning (END)
                } else {
                    // LIMITED controller
                    if (user.pref_name == '') {
                        var name = user.first_name + ' ' + user.last_name;
                    } else {
                        var name = user.pref_name;
                    }

                    // LIVE Functionality (S)
                    if (live === true) {
                        if (message.member.displayName.includes('LIVE') == true) {
                            // Do Nothing
                        } else {
                            var nickname = name + ' | LIVE';
                        }
                    } else {
                        var nickname = name;
                    }
                    // LF (E)

                    // Removing (START)
                    ratings.forEach(rating_name => {
                        message.member.roles.remove(message.guild.roles.cache.find(role => role.name === rating_name));
                    });

                    roles.forEach(role_name => {
                        message.member.roles.remove(message.guild.roles.cache.find(role => role.name === role_name));
                    });
                    // Removing (END)

                    message.member.roles.add(message.guild.roles.cache.find(role => role.name === "Pilot"));
                    message.member.setNickname(nickname);
                }

                message.delete();

                if (live === false) {
                    // Message (START)
                    var embed = new Discord.MessageEmbed()
                    .setColor('#32cd32')
                    .setTitle('Roles Synced')
                    .setURL(site_url)
                    .addFields(
                        {
                            name : 'Successfully Synced Roles',
                            value : 'Thank you for joining the Virtual ' + FACILITY_NAME + ' Discord. Your roles & nickname have been synced according to our ARTCC site.',
                            inline : false
                        },
                    )
                    .setFooter('Maintained by the v' + FACILITY_ID + ' Data Services Team');
                    // Message (END)
                } else {
                    if (message.member.displayName.includes("LIVE") == true) {
                        var embed = "We have reset your nickname to it's original state. Thank you for abiding by all of the policies and we hope your stream went well. Happy Controlling!"
                    } else {
                        // Message (START)
                        var embed = new Discord.MessageEmbed()
                        .setColor('#600080')
                        .setTitle('Live Status Set')
                        .setURL(site_url)
                        .addFields(
                            {
                                name : 'Follow The Policies',
                                value : 'Please remember that your stream is subject to the Facility Operations Policy (https://vats.im/' + FACILITY_ID + '/fop) and VATSIM Code of Conduct (https://vats.im/coc) and to abide by all rules enforcing streams on the Discord and live network respectively.',
                                inline : false
                            },
                            {
                                name : 'Reset Nickname',
                                value : 'Once you have finished your streaming, and all of your content is to prestine quality and your audience is contempt you may reset your nickname by re-sending this command (**!live**). Happy Controlling!',
                                inline : false
                            },
                        )
                        .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team');
                        // Message (END)
                    }
                }

                message.author.send(embed);

                console.log("Success: " + user.discord_name + " Assigned Per System.");

            } else {

                message.delete();

                // Message (START)
                const embed = new Discord.MessageEmbed()
                .setColor('#f70d1a')
                .setTitle('Account Not Linked')
                .setURL(site_url)
                .addFields(
                    {
                        name : 'Please Link Account',
                        value : 'If you have not already done so please link your Discord account to our ARTCC site (' + site_url + '), and re-execute the command.',
                        inline : false
                    },
                )
                .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team');

                message.author.send(embed);
                // Message (END)
            }
            

        } catch (error) {
            console.log("Error: " + error);
            message.reply("**Oops...** an error occured.");
        }
    },
    welcomeMessage: function(message) {
        const embed = new Discord.MessageEmbed()
            .setColor('#ADD8E6')
            .setTitle('Welcome to ' + FACILITY_ID)
            .setURL(site_url)
            .addFields(
                {
                    name : 'Introduction',
                    value : 'Welcome to the Virtual ' + FACILITY_NAME + ' Official Discord Server; the primary communication method for all means regarding the ARTCC. If you are new to the Discord please keep in mind that all means of communications either voice or text are covered under the VATSIM Code of Conduct and the VATSIM Cleveland ARTCC Discord Policy. We want to ensure a safe community and a great experience for our pilots, controllers, and staff to properly communicate, coordinate, navigate, and educate.',
                    inline : false
                },
                {
                    name : 'Linking Your Site Account',
                    value : 'The Virtual ' + FACILITY_NAME + ' utilizes this Discord Bot, and our facility website (' + site_url + ') to seamlessy and efficiently link the two systems together and provide roles and information effectively to all pilots and home/visiting controllers. If you have not already linked your account please navigate to our site and login, navigating to your "Profile" to link your Discord account to the site; or if not a rostered controller (i.e. pilot): the "Discord" button under your name in the navigation bar.',
                    inline : false
                },
                {
                    name : 'Linking To Discord',
                    value : 'Once you have properly linked your Discord account to our facility website you may now proceed to the most important step in initially syncing your roles via a command. To properly utilize the system type **!sync**, and let our robots tinker away and grant your roles.',
                    inline : false
                }
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team');

        message.delete().then(() => {
            message.channel.send(embed);
        });

    }, spontaneous_embed: function(message) {
        const embed = new Discord.MessageEmbed()
            .setColor('#2664D8')
            .setTitle('Spontaneous Training')
            .setURL(site_url)
            .addFields(
                {
                    name : 'What is Spontaneous Training?',
                    value : 'Spontaneous Training is a venue for both students and training staff to post impromptu training availability in this channel. Do note that this source of availability **DOES NOT** guarantee that you will receive training, but instead is offered as a courtesy on behalf of the training staff. You MUST follow the rules listed below to use this system.',
                    inline : false
                },
                {
                    name : 'What happens if I have a session scheduled already?',
                    value : 'If you already have a session scheduled and you place interest for Spontaneous Training, your previous session will not be canceled and you may keep that session at your discretion. Do note that students that do not have a session scheduled may get priority over those that have a session scheduled on setmore.',
                    inline : false
                },
                {
                    name : 'How do I get notified?',
                    value : 'To be notified of Spontaneous Training availability being posted by training staff, react to this message with a 📢.',
                    inline : false
                },
                {
                    name : 'Note',
                    value : 'This is not a venue to encourage soliciting, and we recommend being respectful when coordinating times with training staff for Spontaneous Training or sessions outside of the normal training schedule available on Setmore. If you have any questions or concerns regarding training, reach out to the Training Administrator (TA) or an appropriate member of the training staff.',
                    inline : false
                },
				{
					name : 'Rules',
					value : '1.You must be prepared for your session. If you come to a spontaneous training session unprepared, it may result in the loss of privileges to use this system.\n2.**You must be prepared for an immediate start within the availability window that you provide. If you are not ready to start when contacted by a training staff member, your request will be deleted.**\n3.Your availability window must be within 6 hours of your posting and you may not post future availability. Availability must only be posted when you are free.\n4.Do not direct message or tag training staff members unless they reach out to you or have posted their own availability in this channel.\n5.Requests should be made in **Eastern** time.\n6.Messages will be deleted at the end of the day.\n7.There is **NO GUARANTEE** that your request will be picked up. Training staff are all volunteers and will get to your request if they can.',
					inline : false
				},
				{
					name : 'Command for Training Requests',
					value : '!treq [Type of Session] t: [Availability Window]\n\nExample: !treq ITG-1 t: 3pm Eastern to 9pm Eastern',
					inline : false
				},
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team and Training Department');

        message.delete().then(() => {
            message.channel.send(embed).then(message => {
                message.react('📢').catch(err => console.log(err));
            });
        });   
    }, spontaneous: function(message, content) {
        if (message.content.includes("l:")) {
            var decoded = content[1].split('l:');
            var limit = decoded[1];
        }

        if (limit) {
            var embed = new Discord.MessageEmbed()
            .setColor('#FFCC00')
            .setTitle('Spontaneous Training Available')
            .setURL(site_url)
            .addFields(
                {
                    name : 'Training Staff',
                    value : message.author,
                    inline : false
                },
                {
                    name : 'Date/Time',
                    value : decoded[0],
                    inline : false
                },
                {
                    name : 'Session Type(s) Unavailable',
                    value : limit,
                    inline : false
                }
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team and Training Department');
        } else {
            var embed = new Discord.MessageEmbed()
            .setColor('#FFCC00')
            .setTitle('Spontaneous Training Available')
            .setURL(site_url)
            .addFields(
                {
                    name : 'Training Staff',
                    value : message.author,
                    inline : false
                },
                {
                    name : 'Date/Time',
                    value : content[1],
                    inline : false
                }
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team and Training Department');            
        }

        message.delete().then(() => {
            message.channel.send(`${message.guild.roles.cache.find(role => role.name === "Spontaneous Training")}`).then(() => {
                message.channel.send(embed);
            });
        });

    }, trainingresquest: function(message, content){
        if (message.content.includes("t:")) {
            var decoded = content[1].split('t:');
            var time = decoded[1];
        }
        var embed = new Discord.MessageEmbed()
        .setColor('#FFCC00')
        .setTitle('Spontaneous Training Request')
        .setURL(site_url)
        .addFields(
            {
                name : 'Student',
                value : message.author,
                inline : false
            },
            {
                name : 'Session Type',
                value : decoded[0],
                inline : false
            },
            {
                name : 'Date/Time',
                value : time,
                inline : false
            }
        )
        .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team and Training Department');            

        message.delete().then(() => {
            //message.channel.send(`${message.guild.roles.cache.find(role => role.name === "Training Staff")}`).then(() => {
                message.channel.send(embed).then((msg) => {
                    setTimeout(() => {
                        msg.delete();
                    },DELAYINMILLISEC);
            });
        //});
        },DELAYINMILLISEC);

    },activity: async function(message, client) {
        var count = 0;
        var embed = new Discord.MessageEmbed()
        .setColor('#FF2E2E')
        .setTitle('Activity Notification')
        .setURL(site_url)
        .addFields(
            {
                name : 'Reminder of Activity',
                value : 'Hello! You are receiving this notification as you have yet to fulfill your activity requirements for v' + FACILITY_ID + ' this month! We encourage you to get on position or schedule a training session at the next available time prior to the end of calendar month in order to fulfill your activity requirements. A reminder that we have, on a standard month, at least one host or support events that you are able to look forward to this next upcoming month alongside various days of training slot times that you can take advantage of to further your virtual air traffic career. We would hate to lose you as a controller within our facility as each and every member is a vital part of both the air traffic operations and also the community within!',
                inline : false
            },
            {
                name : 'Minimum Activity Requirement (OBS)',
                value : 'If you are an Observer (OBS), it is required per 7210.3 to fulfill at least one complete training session each calendar month.',
                inline : false
            },
            {
                name : 'Minimum Activity Requirement (S1+)',
                value : 'If you are a Student 1 (S1) rated controller or higher, it is required per 7210.3 to fulfill two hours on a live position each calendar month.',
                inline : false
            },
            {
                name : 'Leave of Absence',
                value : 'If you are unable to meet the activity requirements you may request a Leave of Absence (LOA) per 7210.3 3.4. The minimum length for a LOA is 30 days and the maximum length is 90 days. Controllers in active duty military/armed forces will be permitted up to 24 months of LOA for miltary related deployment or duties but they must complete a checkout with the TA or Instructor upon their return.',
                inline : false
            }
        )
        .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team and Senior Staff'); 


        var formatted = message.content.replace(/ /g, ",");

        const response = await axios.get(site_url + '/api/data/bot/search/?ois=' + formatted.replace("!activity,", "") + '&key=' + site_token);
           
        response.data.forEach(data => {
            if (data !== '') {
                client.users.fetch(data, false).then((user) => {
                    user.send(embed);
                })

                count++;
            }
        });

        message.reply(`sent ${count} activity message(s).`)
    }, removeroles: async function(message, client) {
        var count = 0;
        var formatted = message.content.replace(/ /g, ",");

        const response = await axios.get(site_url + '/api/data/bot/search/?ois=' + formatted.replace("!removeroles,", "") + '&key=' + site_token);

        let guild = client.guilds.cache.get(guild_id);
           
        response.data.forEach(data => {
            if (data !== '') {
                guild.members.fetch(data, false).then((user) => {
                    user.roles.remove(guild.roles.cache.find(role => role.name === "ZOB Controller"))
                    user.roles.remove(guild.roles.cache.find(role => role.name === "Visiting Controller"))
                    user.roles.remove(guild.roles.cache.find(role => role.name === "Spontaneous Training"))
                })

                count++;
            }
        });

        message.reply(`removed ${count} role(s).`)
    }, addevent: async function(user, content){
        const event_id = content[1]
        //fetch event info from website
        const response = await axios.get(site_url + '/api/data/bot/event.php?event_id=' + event_id + '&key=' + site_token);
        const event = response.data;
        
        if(event.status != 'None'){
            // create event
            
        }
        else{
            // event id not found, return error
            message.delete();

            // Message (START)
            const embed = new Discord.MessageEmbed()
            .setColor('#f70d1a')
            .setTitle('Unexpected Error')
            .setURL(site_url)
            .addFields(
                {
                    name : 'Error',
                    value : 'Could not find the event. Please check the event ID is correct',
                    inline : false
                },
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team');

            user.send(embed);
            // Message (END)
        }

    }, updateevent: async function(user, message){
        // TODO
    }, debugMSG: async function(user, message) {
        const embed = new Discord.MessageEmbed()
        .setColor('#f70d1a')
        .setTitle('DEBUG Message')
        .setURL(site_url)
        .addFields(
            {
                name : 'Message',
                value : message,
                inline : false
            },
        )
        user.send(embed);
    
    }
}