# Discord to n8n Webhook Bot

A Discord bot that forwards messages from Discord channels to n8n webhooks for automation and integration purposes.

## Features

- ✅ Forwards Discord messages to n8n webhooks
- ✅ Configurable channel and server filtering
- ✅ Rich message data including attachments, embeds, and mentions
- ✅ Comprehensive error handling and logging
- ✅ Graceful shutdown handling
- ✅ Bot message filtering (ignores other bots)

## Setup Instructions

### 1. Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token and save it for later
6. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (if needed)

### 2. Bot Permissions

In the "OAuth2" > "URL Generator" section:
- Select scope: `bot`
- Select permissions:
  - Send Messages
  - Read Message History
  - View Channels
  - Add Reactions (for error feedback)

Copy the generated URL and use it to invite the bot to your Discord server.

### 3. n8n Webhook Setup

1. In your n8n workflow, add a "Webhook" trigger node
2. Set the method to "POST"
3. Copy the webhook URL (should be something like `http://localhost:5678/webhook/discord`)

### 4. Environment Configuration

1. Copy the `.env` file and update the values:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here

# n8n Webhook Configuration
N8N_WEBHOOK_URL=http://localhost:5678/webhook/discord

# Optional: Channel ID to monitor (leave empty to monitor all channels)
DISCORD_CHANNEL_ID=

# Optional: Guild ID to restrict bot to specific server
DISCORD_GUILD_ID=
```

**To get Channel/Guild IDs:**
1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on a channel/server and select "Copy ID"

### 5. Installation and Running

```bash
# Install dependencies
npm install

# Start the bot
npm start
```

Or add a start script to package.json:
```json
{
  "scripts": {
    "start": "node index.js"
  }
}
```

## Message Data Format

The bot sends the following data structure to your n8n webhook:

```json
{
  "messageId": "string",
  "content": "string",
  "author": {
    "id": "string",
    "username": "string",
    "displayName": "string",
    "bot": false,
    "avatar": "string (URL)"
  },
  "channel": {
    "id": "string",
    "name": "string",
    "type": "number"
  },
  "guild": {
    "id": "string",
    "name": "string"
  },
  "timestamp": "number",
  "createdAt": "string (ISO)",
  "attachments": [
    {
      "id": "string",
      "name": "string",
      "url": "string",
      "size": "number",
      "contentType": "string"
    }
  ],
  "embeds": "array or null",
  "mentions": {
    "users": [],
    "roles": [],
    "channels": []
  }
}
```

## Configuration Options

- `DISCORD_TOKEN`: Your Discord bot token (required)
- `N8N_WEBHOOK_URL`: Your n8n webhook URL (required)
- `DISCORD_CHANNEL_ID`: Specific channel to monitor (optional)
- `DISCORD_GUILD_ID`: Specific server to monitor (optional)

## Logging

The bot provides comprehensive logging:
- ✅ Successful webhook deliveries
- ❌ Error messages and details
- 📨 Message processing information
- 🚀 Startup and configuration details

## Error Handling

- Network timeouts (10 second timeout)
- Invalid webhook URLs
- Discord API errors
- Graceful shutdown on SIGINT/SIGTERM
- Error reactions on failed message processing

## Troubleshooting

1. **Bot doesn't respond**: Check the bot token and permissions
2. **Webhook failures**: Verify the n8n webhook URL and that n8n is running
3. **Missing messages**: Check if the bot has permission to read the channel
4. **Rate limiting**: Discord has rate limits; the bot will handle this automatically

## Development

To run in development mode with auto-restart:
```bash
npm install -g nodemon
nodemon index.js
```