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

client.login(process.env.token);