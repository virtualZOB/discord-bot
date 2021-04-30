require('dotenv').config();
const   Discord     = require('discord.js'),
        client      = new Discord.Client(
        {ws: {
            intents: ['GUILD_MESSAGES', 'GUILDS', 'GUILD_MESSAGE_REACTIONS']
          },
          partials: ['USER', 'REACTION', 'MESSAGE']}),
        express     = require('express'),
        app         = express(),
        cors        = require('cors'),
        helmet      = require('helmet'),
        bodyParser  = require('body-parser'),
        prefix      = process.env.prefix;

const   site_token  = process.env.site_token,
        site_url    = process.env.site_url,
        guild_id    = process.env.guild_id,
        FACILITY_ID = process.env.FACILITY_ID,
        FACILITY_NAME = process.env.FACILITY_NAME,
        cors_opt = {
            origin  :   site_url,
            optionsSuccessStatus: 200
        };

let     port = process.env.PORT || 5000;

client.on('ready', () => {
  console.log(`Credentials ${client.user.tag}: Sucessfully Logged On.`);
});


// Reaction Listener (START)
client.on('messageReactionAdd', (reaction, u) => {
    if (reaction.emoji.name === '📢') {
        if (reaction.message.channel.name !== "spontaneous-training") return;
        if (u.bot) return;

        const role = client.guilds.cache.get(guild_id).roles.cache.find(r => r.name === "Spontaneous Training");
        const user = client.guilds.cache.get(guild_id).members.cache.get(u.id);
        user.roles.add(role);
    }
});

client.on('messageReactionRemove', (reaction, u) => {
    if (reaction.emoji.name === '📢') {
        if (reaction.message.channel.name !== "spontaneous-training") return;
        if (u.bot) return;

        const role = client.guilds.cache.get(guild_id).roles.cache.find(r => r.name === "Spontaneous Training");
        const user = client.guilds.cache.get(guild_id).members.cache.get(u.id);
        user.roles.remove(role);
    }
})
// Reaction Listener (END)

// Functions (START)
const func = require('./functions/all');
// Functions (END)

// Join Listener (START)
client.on('guildMemberAdd', (member) => {

    member.roles.add(member.guild.roles.cache.find(role => role.name === "VATSIM Controller"));

    // Message (START)`
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
            func.syncroles(message.author.id, message, false);
        }

        if (command === "live") {
            func.syncroles(message.author.id, message, true);
        }

        if (command === "welcomemessage") {
            if (message.member.roles.cache.some(role => role.name === 'Facility Staff') || message.member.roles.cache.some(role => role.name === 'Senior Staff')) {
                func.welcomeMessage(message);
            } else {
                message.reply("**Error:** Insufficient Permission.");
            }
        }

        if (command === "spontaneous_embed") {
            if (message.member.roles.cache.some(role => role.name === 'Facility Staff') || message.member.roles.cache.some(role => role.name === 'Senior Staff')) {
                func.spontaneous_embed(message);
            } else {
                message.reply("**Error:** Insufficient Permission.");
            }
        }

        if (command === "spontaneous") {
            if (message.member.roles.cache.some(role => role.name === "Training Staff")) {
                func.spontaneous(message, message.content.split(prefix + 'spontaneous'));
            } else {
                message.reply("**Error:** Insufficient Permission.")
            }
        }


    }

});

// Message Listener (END)

client.login(process.env.token);

// Express (START)
app.use(helmet()).options('*', cors(cors_opt));

app.use(bodyParser.json());
app.use(bodyParser.raw());
app.use(bodyParser.urlencoded({ extended: true }));

app.listen(port, () => {
    console.log(`Express: Listening on ${port}`);
});

// POST: /postIDS
app.post('/postIDS', cors(cors_opt), (req, res) => {
    const   message     = req.body.message,
            expiry_date = req.body.expiry_date,
            type        = req.body.type;

    if (client.guilds.cache.get(process.env.guild_id).channels.cache.find(channel => channel.name === "ids")) {
        // SETTING: Embed Message Variable
        const embed = new Discord.MessageEmbed()
            .setColor('#ffff33')
            .setTitle('New ' + type +' Posted')
            .addFields(
                {
                    name : 'Content',
                    value : '```' + message + '```',
                    inline : false
                },
                {
                    name : 'Expiry Date',
                    value : expiry_date,
                    inline : false
                },
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team');        

        client.guilds.cache.get(process.env.guild_id).channels.cache.find(channel => channel.name === "ids").send(embed);

        res.sendStatus(200);

    } else {
        return res.json({
            status  :   'error',
            msg     :   'An error occured when finding a channel to post your payload in.'
        });
    }

});
// Express (END)