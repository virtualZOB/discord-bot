const Discord = require('discord.js');
const axios = require('axios');
const client = new Discord.Client();

// GETTING: Environment Variables
const site_token = process.env.site_token;
const site_url = process.env.site_url;
const FACILITY_ID = process.env.FACILITY_ID;
const FACILITY_NAME = process.env.FACILITY_NAME;

module.exports = {
    syncroles: async function (discord_id, message) {
        try {
            const response = await axios.get(site_url + '/api/data/bot/?discord_id=' + discord_id + '&key=' + site_token);
            
            const user = response.data;

            // Setting Values
            const full_name = user.first_name + ' ' + user.last_name;
            const type = user.type;
            const facility = user.facility;

            // Nickname (START)
            if (type === "loa" || type === "vis") {
                var nickname = full_name + ' | ' + facility; 
            } else {
                var nickname = full_name;
            }

            if (user.staff !== 'zzzz') {
                var nickname = full_name + ' | ' + user.staff;
            }

            if (user.mentor != '') {
                var nickname = full_name + ' | MTR'; 
            }

            if (user.ins != '') {
                var nickname = full_name + ' | INS'; 
            }

            if (user.facility === 'ZHQ') {
                var nickname = full_name + ' | VATUSA#'; 
            }
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

            // Assigning (START)
            message.member.roles.add(message.guild.roles.cache.find(role => role.name === "VATSIM Controller"));
            message.member.roles.add(prim_role);

            if (staff_role) {
                message.member.roles.add(staff_role);
            }

            if (user.mentor != '' || user.ins != '') {
                message.member.roles.add(message.guild.roles.cache.find(role => role.name === "Training Staff"));
            }

            if (user.facility === 'ZHQ' || user.rating === 'ADM') {
                message.member.roles.add(message.guild.roles.cache.find(role => role.name === "VATSIM/VATUSA Staff"));
            }

            message.member.setNickname(nickname);
            // Assigning (END)

            message.delete();
            console.log("Success: " + user.discord_name + " Assigned Per System.");
            

        } catch (error) {
            console.log("Error: " + error);
            message.reply("**Oops...** an error occured.");
        }
    },
    welcomeMessage: function(message) {
        const embed = new Discord.MessageEmbed()
            .setColor('#32cd32')
            .setTitle('Welcome to ' + FACILITY_ID)
            .setURL(site_url + '/api/user/discord/link')
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