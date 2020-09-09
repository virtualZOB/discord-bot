const Discord = require('discord.js');
const fs = require('fs');
const client = new Discord.Client();

// Setting Values
const prefix = process.env.prefix;

client.on('ready', () => {
  console.log(`Credentials ${client.user.tag}: Sucessfully Logged On.`);
});

// Functions (START)
const func = require('./functions/all');
// Functions (END)

// Join Listener (START)
client.on('guildMemberAdd', member => {

    member.roles.add(member.guild.roles.cache.find(role => role.name === "VATSIM Controller"));

    // Message (START)
    const embed = new Discord.MessageEmbed()
    .setColor('#32cd32')
    .setTitle('Welcome to ' + FACILITY_ID)
    .setURL(site_url)
    .addFields(
        {
            name : 'Need Assistance?',
            value : 'Welcome to the Virtual ' + FACILITY_NAME + ' Official Discord Server; the primary communication method for all means regarding the ARTCC. If you are in need of assistance please message one of our @Facility Staff, and change your Discord "nickname" to your full name associated with your VATSIM account. If no assistance is required please follow the instructions in the "welcome" channel, and have a great rest of your day!',
            inline : false
        }
    )
    .setFooter('Maintained by the v' + FACILITY_ID + ' Data Services Team');
    // Message (END)

    member.send(embed);

});
// Join Listener (END)

// Message Listener (START)
client.on('message', message => {

    if (message.content.startsWith(prefix)) {

        const args = message.content.slice(prefix.length).split(/ +/);
        const command = args.shift().toLowerCase();

        if (command === "sync") {
            func.syncroles(message.author.id, message);
        }

        if (command === "welcomemessage") {
            if (message.member.roles.cache.some(role => role.name === 'Facility Staff') || message.member.roles.cache.some(role => role.name === 'Senior Staff')) {
                func.welcomeMessage(message);
            } else {
                message.reply("**Error:** Insufficient Permission.");
            }
        }

        // if (command === "r") {
        //     func.updateRatings();
        // }

    }

});
// Message Listener (END)

client.login(process.env.token);