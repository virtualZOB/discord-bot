const Discord = require('discord.js');
const fs = require('fs');
const client = new Discord.Client();

// Setting Values
const prefix = process.env.prefix;
const site_token = process.env.site_token;
const site_url = process.env.site_url;

client.on('ready', () => {
  console.log(`Credentials ${client.user.tag}: Sucessfully Logged On.`);
});

// Functions (START)
const functionFiles = fs.readdirSync('./functions').filter(file => file.endsWith('.js'));

for (const file of functionFiles) {
    const func = require('./functions/' + file);
}
// Functions (END)

// Message Listener (START)
client.on('message', message => {
    if (message.content.startsWith(prefix)) {
        const args = message.content.slice(prefix.length).split(/ +/);
        const command = args.shift().toLowerCase();

        if (command === "sync") {
            syncroles(message.author.id, site_token, site_url);
        }

    }
});
// Message Listener (END)

client.login(process.env.token);