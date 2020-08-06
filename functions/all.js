const Discord = require('discord.js');
const axios = require('axios');
const client = new Discord.Client();

const site_token = process.env.site_token;
const site_url = process.env.site_url;
const FACILITY_ID = process.env.FACILITY_ID;

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
                const nickname = full_name + ' | ' + facility; 
            } else {
                const nickname = full_name;
            }

            if (user.staff !== 'zzzz') {
                const nickname = full_name + ' | ' + user.staff;
            }
            // Nickname (END)

            // Roles (START)
            if (type === "loa") {
                let prim_role = message.guild.roles.cache.find(role => role.name === "Mutual Visiting Controller");
            } else if (type === "vis") {
                let prim_role = message.guild.roles.cache.find(role => role.name === "Visiting Controller");
            } else {
                let prim_role = message.guild.roles.cache.find(role => role.name === FACILITY_ID + " Controller");
            }

            if (user.staff !== 'zzzz') {
                if (user.staff == "ATM" || user.staff == "DATM" || user.staff == "TA" || user.staff == "ATA") {
                    let staff_role = message.guild.roles.cache.find(role => role.name === "Senior Staff");
                } else {
                    let staff_role = message.guild.roles.cache.find(role => role.name === "Facility Staff");
                }
            }
            // Roles (END)

            // Assigning (START)
            message.member.addRole(message.guild.roles.cache.find(role => role.name === "VATSIM Controller"))
            message.member.addRole(prim_role);

            if (staff_role) {
                message.member.addRole(staff_role);
            }

            message.member.setNickname(message.content.replace('changeNick ', nickname));
            // Assigning (END)

            message.reply("**Success!**");

        } catch (error) {
            console.log(error);
            message.reply("**Oops...** an error occured.");
        }
    }
}