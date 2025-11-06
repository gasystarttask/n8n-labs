import { Client, GatewayIntentBits, Events } from 'discord.js';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

// Create a new client instance
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.DirectMessages
    ]
});

// Configuration from environment variables
const config = {
    discordToken: process.env.DISCORD_TOKEN,
    n8nWebhookUrl: process.env.N8N_WEBHOOK_URL,
    channelId: process.env.DISCORD_CHANNEL_ID || null,
    guildId: process.env.DISCORD_GUILD_ID || null
};

// Function to send message data to n8n webhook
async function sendToN8nWebhook(messageData) {
    try {
        console.log('Sending message to n8n webhook:', config.n8nWebhookUrl);
        
        const response = await axios.post(config.n8nWebhookUrl, messageData, {
            headers: {
                'Content-Type': 'application/json'
            },
            timeout: 10000 // 10 second timeout
        });
        
        console.log('✅ Successfully sent to n8n:', response.status);
        return response.data;
    } catch (error) {
        console.error('❌ Error sending to n8n webhook:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }
        throw error;
    }
}

// Function to format message data for n8n
function formatMessageData(message) {
    return {
        messageId: message.id,
        content: message.content,
        author: {
            id: message.author.id,
            username: message.author.username,
            displayName: message.author.displayName || message.author.username,
            bot: message.author.bot,
            avatar: message.author.displayAvatarURL()
        },
        channel: {
            id: message.channel.id,
            name: message.channel.name || 'DM',
            type: message.channel.type
        },
        guild: message.guild ? {
            id: message.guild.id,
            name: message.guild.name
        } : null,
        timestamp: message.createdTimestamp,
        createdAt: message.createdAt.toISOString(),
        attachments: message.attachments.map(attachment => ({
            id: attachment.id,
            name: attachment.name,
            url: attachment.url,
            size: attachment.size,
            contentType: attachment.contentType
        })),
        embeds: message.embeds.length > 0 ? message.embeds : null,
        mentions: {
            users: message.mentions.users.map(user => ({
                id: user.id,
                username: user.username
            })),
            roles: message.mentions.roles.map(role => ({
                id: role.id,
                name: role.name
            })),
            channels: message.mentions.channels.map(channel => ({
                id: channel.id,
                name: channel.name
            }))
        }
    };
}

// Function to check if message should be processed
function shouldProcessMessage(message) {
    // Don't process bot messages (including our own)
    if (message.author.bot) {
        return false;
    }
    
    // If specific channel is configured, only process messages from that channel
    if (config.channelId && message.channel.id !== config.channelId) {
        return false;
    }
    
    // If specific guild is configured, only process messages from that guild
    if (config.guildId && (!message.guild || message.guild.id !== config.guildId)) {
        return false;
    }
    
    return true;
}

// Event listener for when the client is ready
client.once(Events.ClientReady, readyClient => {
    console.log(`🚀 Discord bot is ready! Logged in as ${readyClient.user.tag}`);
    console.log(`📡 Will forward messages to: ${config.n8nWebhookUrl}`);
    
    if (config.channelId) {
        console.log(`📢 Monitoring specific channel: ${config.channelId}`);
    } else {
        console.log(`📢 Monitoring all accessible channels`);
    }
    
    if (config.guildId) {
        console.log(`🏠 Restricted to guild: ${config.guildId}`);
    }
});

// Event listener for new messages
client.on(Events.MessageCreate, async (message) => {
    try {
        // Check if we should process this message
        if (!shouldProcessMessage(message)) {
            return;
        }
        
        console.log(`📨 New message from ${message.author.username} in ${message.guild?.name || 'DM'}: ${message.content}`);
        
        // Format the message data
        const messageData = formatMessageData(message);
        
        // Send to n8n webhook
        await sendToN8nWebhook(messageData);
        
    } catch (error) {
        console.error('❌ Error processing message:', error.message);
        
        // Optional: React to the message with an error emoji to indicate failure
        try {
            await message.react('❌');
        } catch (reactionError) {
            console.error('Could not add error reaction:', reactionError.message);
        }
    }
});

// Error handling
client.on(Events.Error, error => {
    console.error('❌ Discord client error:', error);
});

client.on(Events.Warn, warning => {
    console.warn('⚠️ Discord client warning:', warning);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Received SIGINT, shutting down gracefully...');
    client.destroy();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
    client.destroy();
    process.exit(0);
});

// Validation and startup
function validateConfig() {
    if (!config.discordToken) {
        console.error('❌ DISCORD_TOKEN is required in .env file');
        process.exit(1);
    }
    
    if (!config.n8nWebhookUrl) {
        console.error('❌ N8N_WEBHOOK_URL is required in .env file');
        process.exit(1);
    }
    
    console.log('✅ Configuration validated');
}

// Start the bot
try {
    validateConfig();
    
    console.log('🔄 Starting Discord bot...');
    await client.login(config.discordToken);
    
} catch (error) {
    console.error('❌ Failed to start bot:', error.message);
    process.exit(1);
}
