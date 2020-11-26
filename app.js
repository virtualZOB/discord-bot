require('dotenv').config();
const   Discord     = require('discord.js'),
        fs          = require('fs'),
        client      = new Discord.Client(),
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

// Functions (START)
const func = require('./functions/all');
// Functions (END)

// Join Listener (START)
client.on('guildMemberAdd', (member) => {

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

    }

});
// Message Listener (END)

client.login(process.env.token);

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

    if (client.guilds.cache.get(process.env.guild_id).channels.cache.find(channel => channel.name === "ids4")) {
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

        client.guilds.cache.get(process.env.guild_id).channels.cache.find(channel => channel.name === "ids4").send(embed);

        res.sendStatus(200);

    } else {
        return res.json({
            status  :   'error',
            msg     :   'An error occured when finding a channel to post your payload in.'
        });
    }

});

// POST: postATIS
app.post('/postATIS', cors(cors_opt), (req, res) => {
    const   icao         = req.body.icao,
            atis_letter  = req.body.atis_letter,
            config_profile = req.body.config_profile,
            metar       = req.body.metar;

    if (client.guilds.cache.get(process.env.guild_id).channels.cache.find(channel => channel.name === "ids4")) {
        // SETTING: Embed Message Variable
        const embed = new Discord.MessageEmbed()
            .setColor('#4ae9ff')
            .setTitle('Updated ATIS Information')
            .addFields(
                {
                    name : 'Facility',
                    value : icao,
                    inline : true
                },
                {
                    name : 'ATIS Letter',
                    value : atis_letter,
                    inline : true
                },
                {
                    name : 'Config Profile',
                    value : '```' + config_profile + '```',
                    inline : false
                },
                {
                    name : 'Raw METAR',
                    value : '```' + metar + '```',
                    inline: false
                }
            )
            .setFooter('Maintained by the v' + FACILITY_ID + ' Web Services Team');        

        client.guilds.cache.get(process.env.guild_id).channels.cache.find(channel => channel.name === "ids4").send(embed);

        res.sendStatus(200);

    } else {
        return res.json({
            status  :   'error',
            msg     :   'An error occured when finding a channel to post your payload in.'
        });
    }

});