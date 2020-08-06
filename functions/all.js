module.exports = {
    syncroles: function (discord_id, site_token, site_url) {
        const Discord = require('discord.js');
        const axios = require('axios');
        const client = new Discord.Client();
    
        try {
            const response = axios.get(site_url + '/api/data/discord/?discord_id=' + discord_id + '&key=' + site_token);
            console.log(response);
        } catch (err) {
            console.log(err);
            message.reply("**Oops...** an error occured.");
        }
    }
}