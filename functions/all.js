const Discord = require('discord.js');
const axios = require('axios');
const client = new Discord.Client();

// GETTING: Environment Variables
const site_token = process.env.site_token;
const site_url = process.env.site_url;
const guild_id = process.env.guild_id;
const FACILITY_ID = process.env.FACILITY_ID;
const FACILITY_NAME = process.env.FACILITY_NAME;

// ARRAY: Ratings
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
]

module.exports = {
    syncroles: async function (discord_id, message, live) {
        try {
            const response = await axios.get(site_url + '/api/data/bot/?discord_id=' + discord_id + '&key=' + site_token);
           
            const user = response.data;

            if (user.status !== "None") {
                // Setting Values
                if (user.discord_nick_pref > 0) {
                    var name = user.first_name;
                } else {
                    var name = user.first_name + ' ' + user.last_name;
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

                if (user.staff !== 'zzzz') {
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
                if (type === "loa") {
                    var prim_role = message.guild.roles.cache.find(role => role.name === "Mutual Visiting Controller");
                } else if (type === "vis") {
                    var prim_role = message.guild.roles.cache.find(role => role.name === "Visiting Controller");
                } else {
                    var prim_role = message.guild.roles.cache.find(role => role.name === FACILITY_ID + " Controller");
                }

                if (user.staff !== 'zzzz') {
                    if (user.staff == "ATM" || user.staff == "DATM" || user.staff == "TA" || user.staff == "ATA") {
                        var staff_role = message.guild.roles.cache.find(role => role.name === "Senior Staff");
                    } else {
                        var staff_role = message.guild.roles.cache.find(role => role.name === "Facility Staff");
                    }
                }
                // Roles (END)

                // Removing (START)
                ratings.forEach(rating_name => 
                    message.member.roles.remove(message.guild.roles.cache.find(role => role.name === rating_name)));

                message.member.roles.remove(message.guild.roles.cache.find(role => role.name === "Mutual Visiting Controller"));
                message.member.roles.remove(message.guild.roles.cache.find(role => role.name === "Visiting Controller"));
                message.member.roles.remove(message.guild.roles.cache.find(role => role.name === FACILITY_ID + " Controller"));
                message.member.roles.remove(message.guild.roles.cache.find(role => role.name === "Facility Staff"));
                message.member.roles.remove(message.guild.roles.cache.find(role => role.name === "Training Staff"));

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
                            value : 'Thank you for joining the Virtual ' + FACILITY_NAME + '. Your roles & nickname have been synced according to our ARTCC site.',
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
                                name : 'Un-Set Nickname',
                                value : 'Once you have finished your streaming, and all of your content is to prestine quality and your audience is contempt you may reset your nickname by re-sending this command (**!live**). Happy Controlling!',
                                inline : false
                            },
                        )
                        .setFooter('Maintained by the v' + FACILITY_ID + ' Data Services Team');
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
                .setFooter('Maintained by the v' + FACILITY_ID + ' Data Services Team');

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
            .setColor('#32cd32')
            .setTitle('Welcome to ' + FACILITY_ID)
            .setURL(site_url)
            .addFields(
                {
                    name : 'Introduction',
                    value : 'Welcome to the Virtual ' + FACILITY_NAME + ' Official Discord Server; the primary communication method for all means regarding the ARTCC. If you are new to the Discord please keep in mind that all means of communications either voice or text are covered under the VATSIM Code of Conduct, and all rules are applicable in thie Discord server. We want to ensure a safe community and a great experience for our controllers to properly communicate, coordinate, navigate, and educate.',
                    inline : false
                },
                {
                    name : 'Linking Your Site Account',
                    value : 'The Virtual ' + FACILITY_NAME + ' utilizes this Discord Bot, and our facility website (' + site_url + ') to seamlessy and efficiently link the two systems together and provide roles and information effectively to all controllers whether they are home, visiting, or mutual visiting. If you have not already linked your account please navigate to our site and login, and navigate to your "Profile" to link your Discord account to the site.',
                    inline : false
                },
                {
                    name : 'Linking To Discord',
                    value : 'Once you have properly linked your Discord account to our facility website you may now proceed to the most important step in initially syncing your roles via a command. To properly utilize the system type **!sync**, and let our robots tinker away and grant your roles.',
                    inline : false
                }
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Data Services Team');

        message.delete().then(() => {
            message.channel.send(embed);
        });

    }
}