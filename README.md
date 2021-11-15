# Feedback Bot

Telegram feedback bot.

*Read this in [Russian](README.ru.md).*

## Usage
Register a new bot using Telegram's [@BotFather](https://t.me/botfather).
Copy the provided token to `telegram_bot_token` configuration option
and start the bot.

After starting the bot, authenticate yourself as an Admin
by sending the `auth` command and the `admin_token` option value
to your new bot:
```
You: /auth <admin-token>
Bot: Auth token successfully verified
```

**Note:** it is recommended to remove the message with the token
after successful authentication.

After that all messages from other users to the bot will be forwarded
to the Admins. The Admins can send messages to users by replying
to the forwarded messages (press on the message and select "Reply").
Admin profiles will not be visible to the users and messages will look
as if they were sent by the bot itself.

Bot can forward messages to and from group chats.
For that an authenticated Admin has to add the bot to the target group.
**Note:** if bot has been added to a group by non-admin user,
it has to be deleted from group and added again by an authenticated Admin.
To allow group members to reply to the forwarded messages
[Privacy Mode](https://core.telegram.org/bots#privacy-mode) has to be disabled.
This can be done via [@BotFather](https://t.me/botfather).

## Dependencies:
* Python 3.9+;
* Poetry;
* PostgreSQL 13.

## Configuration
Bot can be configured by editing the [settings.toml](settings.toml)
or by adding a `.secrets.toml` file into the project root directory
(advised for local setup). Alternatively configuration can be specified
using environment variables.

### Options:
* `host` - host for incoming connections (default `127.0.0.1`);
* `port` - port number for incoming connections (default `3000`);
* `telegram_bot_token` - required, bot token provided by
  [@BotFather](https://t.me/botfather);
* `telegram_webhook_host` - required,
  host of the URL for Telegram-sent updates;
* `telegram_webhook_path` - required,
  path of the URL for Telegram-sent updates;
* `database_url` - URL of the database (details about the format can be found
  [here](https://www.postgresql.org/docs/13/libpq-connect.html#id-1.7.3.8.3.6));
* `admin_token` - bot Administrator token (password).

Environment variable names for options can be uppercase.

## Deploying to Heroku
Use the button below to deploy the bot in one click:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

**Warning:** Hobby Dev plan for
[Heroku Postgres addon](https://elements.heroku.com/addons/heroku-postgresql)
is used by default. This plan has limited storage capacity.
If the storage limits have been encountered, either the addon plan can be upgraded
or old forwarded messages can be removed by running the following query
(use [heroku-cli](https://devcenter.heroku.com/articles/heroku-postgresql#pg-psql)
to connect to the database):

```sql
-- remove forwarded messages received before 2021-01-01
DELETE FROM forwarded_message WHERE created_at < '2021-01-01';
```

### Applying updates
1. Install [git](https://git-scm.com/downloads) and configure
[heroku-cli](https://devcenter.heroku.com/articles/heroku-cli).
2. Clone the repository:
    ```
    git clone https://github.com/polfpilf/feedback-bot.git
    ```
    If the repository was cloned previously,
    execute the following command in the local repository folder:
    ```
    git pull origin
    ```
3. Add heroku remote to your local repository
([instructions](https://devcenter.heroku.com/articles/git#for-an-existing-heroku-app)).
4. Push the updated bot version to heroku repository:
    ```
    git push heroku master
    ```
