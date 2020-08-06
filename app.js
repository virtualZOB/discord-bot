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

    }
});
// Message Listener (END)

client.login(process.env.token);