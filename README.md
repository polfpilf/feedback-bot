# Feedback Bot

Telegram feedback bot.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)


## Usage
Register a new bot using Telegram's [@BotFather](https://t.me/botfather). Copy the provided token to `telegram_bot_token` configuration option.

After deploying the bot, authenticate yourself as an Admin by sending the `auth` command to your new bot:
```
You: /auth <admin-token>
Bot: Auth token successfully verified
```

After that all messages from other users to the bot will be forwarded to the Admins. The Admins can send messages to users by replying to the forwarded messages.
Admin profiles will not be visible to the users and messages will look as if they were sent by the bot itself.

Bot can forward messages to and from group chats. For that an authenticated Admin has to add the bot to the target group.
**Note:** if bot has been added to a group by non-admin user, it has to be deleted from group and added again by an authenticated Admin.
To allow group members to reply to the forwarded messages [Privacy Mode](https://core.telegram.org/bots#privacy-mode) has to be disabled.
This can be done via [@BotFather](https://t.me/botfather).

## Configuration
Bot can be configured by editing the [settings.toml](settings.toml)
or by adding a `.secrets.toml` file into the project root directory (adviced for local setup).
Alternatively configuration can be specified using environment variables.

Configuration fields are described in the [settings.toml](settings.toml) file.
