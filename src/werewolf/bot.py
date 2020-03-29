import discord
import asyncio
import aiohttp
import os
import random
import traceback
import sys
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from config import *
from settings import *
import json
import urllib.request
from collections import OrderedDict
from itertools import chain

# NOTE: I wonder if I should first encapsulate the entire thing into a class, where this init block
# is my __init__ method, and so on. If I start failing to make progress or losing some fidelity along
# the way I should come back and think about that PLAN
################## START INIT #####################
# TODO: This is an emulation of Global Variables, I really don't think that's a good idea but I need to figure out how to architect it away.
# My general plan starting off is to basically pull all of these into the class describing the game logic... Or at least... Well The parts that make sense for the game logic.
# It seems like the 'session' data is mostly game data and the rest of it might be discord specific


client = discord.Client()
PLAYERS_ROLE = None
ADMINS_ROLE = None
WEREWOLF_NOTIFY_ROLE = None
ratelimit_dict = {}
pingif_dict = {}
notify_me = []
stasis = {}
commands = {}

wait_bucket = WAIT_BUCKET_INIT
wait_timer = datetime.now()
day_warning = DEFAULT_DAY_WARNING
day_timeout = DEFAULT_DAY_TIMEOUT
night_warning = DEFAULT_NIGHT_WARNING
night_timeout = DEFAULT_NIGHT_TIMEOUT

# TODO: I don't know what these files are open for or what is going on here
faftergame = None
starttime = None
with open(NOTIFY_FILE, 'a+') as notify_file:
    notify_file.seek(0)
    notify_me = notify_file.read().split(',')

if os.path.isfile(STASIS_FILE):
    with open(STASIS_FILE, 'r') as stasis_file:
        stasis = json.load(stasis_file)
else:
    with open(STASIS_FILE, 'a+') as stasis_file:
        stasis_file.write('{}')

random.seed(datetime.now())

################### END INIT ######################

@client.event
async def on_ready():
    global starttime
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    # NOTE: Shouldn't OnReady only ever trigger once?
    # I thought I should trust that this lifecycle method works just fine rather than
    # writing some code to protect against it running twice. TODO: See if I can figure out why.
    if starttime:
        await log(1, 'on_ready triggered again!')
        return
    await log(1, 'on_ready triggered!')
    # [
    #   playing : True | False, 
    #   players : {
    #       player id : [alive, role, action, template, other]
    #   }, day?, 
    #   [datetime night, datetime day],
    #   [elapsed night, elapsed day],
    #   first join time,
    #   gamemode]
    # NOTE: These role-names are defined in the context of the config.py.example file.
    # TODO: Extract Discord Logic from Game logic
    # Does this game actually require discord roles to function?
    # - The functionality that prevents players from talking at night is actually nice.
    # So lets say yes it does require at least, player and werewolf roles.
    # If that's true it should support configuring those roles, not only before the server is up
    # But after it's already running, via some command which sets that up.
    # TODO: Store this information in a file and if it doesn't exist. Create it.
    # When OnReady Runs, inform the user that this information isn't set or available in the file
    # And what they need to do to make it ready.
    # TODO: There's some library for using environment files that might me more suitable which I should import.
    for role in client.get_server(WEREWOLF_SERVER).role_hierarchy:
        if role.name == PLAYERS_ROLE_NAME:
            global PLAYERS_ROLE
            PLAYERS_ROLE = role
        if role.name == ADMINS_ROLE_NAME:
            global ADMINS_ROLE
            ADMINS_ROLE = role
        if role.name == WEREWOLF_NOTIFY_ROLE_NAME:
            global WEREWOLF_NOTIFY_ROLE
            WEREWOLF_NOTIFY_ROLE = role
    if PLAYERS_ROLE:
        await log(0, "Players role id: " + PLAYERS_ROLE.id)
    else:
        await log(3, "Could not find players role " + PLAYERS_ROLE_NAME)
    if ADMINS_ROLE:
        await log(0, "Admins role id: " + ADMINS_ROLE.id)
    else:
        await log(3, "Could not find admins role " + ADMINS_ROLE_NAME)
    if WEREWOLF_NOTIFY_ROLE:
        await log(0, "Werewolf Notify role id: " + WEREWOLF_NOTIFY_ROLE.id)
    else:
        await log(2, "Could not find Werewolf Notify role " + WEREWOLF_NOTIFY_ROLE_NAME)
    if PLAYING_MESSAGE:
        await client.change_presence(status=discord.Status.online, game=discord.Game(name=PLAYING_MESSAGE))
    starttime = datetime.now()


@client.event
async def on_resume():
    # TODO: Why does OnResume Matter if it doesn't actually contain any resume code...?
    print("RESUMED")
    await log(1, "on_resume triggered!")


# NOTE: All of the logic here is coming through an on_message event
# The rules are divided by PM or Public Channel and
# Bot Prefix or Not BotPrefix
# Commmands are in a non_private message and start with the command prefix.
# They are sent to the command dispatcher.
# Do Cogs have a mechanism by which you can specify a cog-specific prefix?
# Bots which load cogs to have a mechanism to specify a botwide prefix.
# TODO: Break this logic out into individual commands (except perhaps for PM's with user commands)
@client.event
async def on_message(message):
    if not starttime:
        return
    if message.author.id in [client.user.id] + IGNORE_LIST or not client.get_server(WEREWOLF_SERVER).get_member(message.author.id):
        if not (message.author.id in ADMINS or message.author.id == OWNER_ID):
            return
    if await rate_limit(message):
        return

    if message.channel.is_private:
        await log(0, 'pm from ' + message.author.name + ' (' + message.author.id + '): ' + message.content)
        if session[0] and message.author.id in session[1]:
            if session[1][message.author.id][1] in WOLFCHAT_ROLES and session[1][message.author.id][0]:
                if not message.content.strip().startswith(BOT_PREFIX):
                    await wolfchat(message)

    if message.content.strip().startswith(BOT_PREFIX):
        # command
        command = message.content.strip()[len(BOT_PREFIX):].lower().split(' ')[0]
        parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
        if has_privileges(1, message) or message.channel.id == GAME_CHANNEL or message.channel.is_private:
            await parse_command(command, message, parameters)
    elif message.channel.is_private:
        command = message.content.strip().lower().split(' ')[0]
        parameters = ' '.join(message.content.strip().lower().split(' ')[1:])
        await parse_command(command, message, parameters)


############# COMMANDS #############
# NOTE: I've pulled out the command section. This is surely entirely broken right now.
######### END COMMANDS #############

def misdirect(player, alive_players=None):
    if not alive_players:
        alive_players = [x for x in session[1] if session[1][x][0]]
    return random.choice([alive_players[len(alive_players)-1] if alive_players.index(player) == 0 else alive_players[alive_players.index(player)-1], alive_players[0] if alive_players.index(player) == len(alive_players)-1 else alive_players[alive_players.index(player)+1]])


def has_privileges(level, message):
    if message.author.id == OWNER_ID:
        return True
    elif level == 1 and message.author.id in ADMINS:
        return True
    elif level == 0:
        return True
    else:
        return False


async def reply(message, text, cleanmessage=True):
    if cleanmessage:
        text = text.replace('@', '@\u200b')
    await client.send_message(message.channel, message.author.mention + ', ' + str(text))


async def send_lobby(text):
    for i in range(3):
        try:
            msg = await client.send_message(client.get_channel(GAME_CHANNEL), text)
            return msg
            break
        except:
            await log(3, "Error in sending message `{}` to lobby: ```py\n{}\n```".format(
                text, traceback.format_exc()))
            await asyncio.sleep(5)
    else:
        await log(3, "Unable to send message `{}` to lobby: ```py\n{}\n```".format(
            text, traceback.format_exc()))


async def parse_command(commandname, message, parameters):
    await log(0, 'Parsing command ' + commandname + ' with parameters `' + parameters + '` from ' + message.author.name + ' (' + message.author.id + ')')
    if commandname in commands:
        pm = 0
        if message.channel.is_private:
            pm = 1
        if has_privileges(commands[commandname][1][pm], message):
            try:
                await commands[commandname][0](message, parameters)
            except Exception:
                traceback.print_exc()
                print(session)
                msg = '```py\n{}\n```\n**session:**```py\n{}\n```'.format(traceback.format_exc(), session)
                await log(3, msg)
                await client.send_message(message.channel, "An error has occurred and has been logged.")
        elif has_privileges(commands[commandname][1][0], message):
            if session[0] and message.author.id in session[1] and session[1][message.author.id][0]:
                if commandname in COMMANDS_FOR_ROLE and (get_role(message.author.id, 'role') in COMMANDS_FOR_ROLE[commandname]\
                or not set(get_role(message.author.id, 'templates')).isdisjoint(set(COMMANDS_FOR_ROLE[commandname]))):
                    await reply(message, "Please use command " + commandname + " in channel.")
        elif has_privileges(commands[commandname][1][1], message):
            if session[0] and message.author.id in session[1] and session[1][message.author.id][0]:
                if commandname in COMMANDS_FOR_ROLE and get_role(message.author.id, 'role') in COMMANDS_FOR_ROLE[commandname]:
                    try:
                        await client.send_message(message.author, "Please use command " + commandname + " in private message.")
                    except discord.Forbidden:
                        pass
            elif message.author.id in ADMINS:
                await reply(message, "Please use command " + commandname + " in private message.")
        else:
            await log(2, 'User ' + message.author.name + ' (' + message.author.id + ') tried to use command ' + commandname + ' with parameters `' + parameters + '` without permissions!')


async def log(loglevel, text):
    # TODO: Turn this into a real LogHandler, and Configure File, Console Stdout and Owner PM Logging.
    # TODO: Enable Changing the Log Level at Runtime.
    # loglevels
    # 0 = DEBUG
    # 1 = INFO
    # 2 = WARNING
    # 3 = ERROR
    levelmsg = {0 : '[DEBUG] ',
                1 : '[INFO] ',
                2 : '**[WARNING]** ',
                3 : '**[ERROR]** <@' + OWNER_ID + '> '
                }
    logmsg = levelmsg[loglevel] + str(text)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write("[{}] {}\n".format(datetime.now(), logmsg))
    if loglevel >= MIN_LOG_LEVEL:
        await client.send_message(client.get_channel(DEBUG_CHANNEL), logmsg)


def balance_roles(massive_role_list, default_role='villager', num_players=-1):
    if num_players == -1:
        num_players = len(session[1])
    extra_players = num_players - len(massive_role_list)
    if extra_players > 0:
        massive_role_list += [default_role] * extra_players
        return (massive_role_list, "Not enough roles; added {} {} to role list".format(extra_players, default_role))
    elif extra_players < 0:
        random.shuffle(massive_role_list)
        removed_roles = []
        team_roles = [0, 0, 0]
        for role in massive_role_list:
            if role in WOLF_ROLES_ORDERED:
                team_roles[0] += 1
            elif role in VILLAGE_ROLES_ORDERED:
                team_roles[1] += 1
            elif role in NEUTRAL_ROLES_ORDERED:
                team_roles[2] += 1
        for i in range(-1 * extra_players):
            team_fractions = list(x / len(massive_role_list) for x in team_roles)
            roles_to_remove = set()
            if team_fractions[0] > 0.35:
                roles_to_remove |= set(WOLF_ROLES_ORDERED)
            if team_fractions[1] > 0.7:
                roles_to_remove |= set(VILLAGE_ROLES_ORDERED)
            if team_fractions[2] > 0.15:
                roles_to_remove |= set(NEUTRAL_ROLES_ORDERED)
            if len(roles_to_remove) == 0:
                roles_to_remove = set(roles)
                if team_fractions[0] < 0.25:
                    roles_to_remove -= set(WOLF_ROLES_ORDERED)
                if team_fractions[1] < 0.5:
                    roles_to_remove -= set(VILLAGE_ROLES_ORDERED)
                if team_fractions[2] < 0.05:
                    roles_to_remove -= set(NEUTRAL_ROLES_ORDERED)
                if len(roles_to_remove) == 0:
                    roles_to_remove = set(roles)
            for role in massive_role_list[:]:
                if role in roles_to_remove:
                    massive_role_list.remove(role)
                    removed_roles.append(role)
                    break
        return (massive_role_list, "Too many roles; removed {} from the role list".format(', '.join(sort_roles(removed_roles))))
    return (massive_role_list, '')


async def assign_roles(gamemode):
    massive_role_list = []
    gamemode_roles = get_roles(gamemode, len(session[1]))

    if not gamemode_roles:
        # Second fallback just in case
        gamemode_roles = get_roles('default', len(session[1]))
        session[6] = 'default'

    # Generate list of roles

    for role in gamemode_roles:
        if role in roles and role not in TEMPLATES_ORDERED:
            massive_role_list += [role] * gamemode_roles[role]

    massive_role_list, debugmessage = balance_roles(massive_role_list)
    if debugmessage != '':
        await log(2, debugmessage)

    if session[6].startswith('roles'):
        session[7] = dict((x, massive_role_list.count(x)) for x in roles if x in massive_role_list)
    else:
        session[7] = dict(gamemode_roles)

    random.shuffle(massive_role_list)
    for player in session[1]:
        role = massive_role_list.pop()
        session[1][player][1] = role
        if role == 'hunter':
            session[1][player][4].append('hunterbullet')
        elif role == 'matchmaker':
            session[1][player][4].append('match')
        elif role == 'amnesiac':
            session[1][player][4].append('role:{}'.format(random.choice(list(set(roles) - set(["minion", "matchmaker", "villager", "cultist", "amnesiac", "clone", "monster", "demoniac", "piper", "dullahan", "wild child"] + TEMPLATES_ORDERED)))))
            if 'role:hunter' in session[1][player][4]:
                session[1][player][4].append('hunterbullet')
            if 'role:priest' in session[1][player][4]:
                session[1][player][4].append('bless')
        elif role == 'priest':
            session[1][player][4].append('bless')
        elif role == 'clone':
            session[1][player][4].append('clone')

    for i in range(gamemode_roles['cursed villager'] if 'cursed villager' in gamemode_roles else 0):
        cursed_choices = [x for x in session[1] if get_role(x, 'role') not in\
        ACTUAL_WOLVES + ROLES_SEEN_WOLF + ['seer', 'priest', 'oracle', 'jester', 'fool'] and 'cursed' not in session[1][x][3]]
        if cursed_choices:
            cursed = random.choice(cursed_choices)
            session[1][cursed][3].append('cursed')
    for i in range(gamemode_roles['mayor'] if 'mayor' in gamemode_roles else 0):
        if gamemode == 'random':
            mayor_choices = [x for x in session[1] if 'mayor' not in session[1][x][3]]
        else:
            mayor_choices = [x for x in session[1] if get_role(x, 'role') not in\
        ['monster', 'jester', 'fool'] and 'mayor' not in session[1][x][3]]
        if mayor_choices:
            mayor = random.choice(mayor_choices)
            session[1][mayor][3].append('mayor')
            session[1][mayor][4].append('unrevealed')
    for i in range(gamemode_roles['gunner'] if 'gunner' in gamemode_roles else 0):
        if gamemode in ['chaos', 'random']:
            gunner_choices = [x for x in session[1] if ('gunner' not in session[1][x][3] and 'sharpshooter' not in session[1][x][3])]
        else:
            gunner_choices = [x for x in session[1] if get_role(x, 'role') not in \
            WOLF_ROLES_ORDERED + NEUTRAL_ROLES_ORDERED + ['priest'] and ('gunner' not in session[1][x][3] and 'sharpshooter' not in session[1][x][3])]
        if gunner_choices:
            pewpew = random.choice(gunner_choices)
            if get_role(pewpew, 'role') == 'village drunk':
                session[1][pewpew][3].append('gunner')
                if session[6] == 'mad':
                    session[1][pewpew][4] += ['bullet']
                else:
                    session[1][pewpew][4] += ['bullet'] * int(GUNNER_MULTIPLIER * len(session[1]) + 1) * DRUNK_MULTIPLIER
            elif random.random() > 0.2 or session[6] == 'aleatoire':
                session[1][pewpew][3].append('gunner')
                if session[6] == 'mad':
                    session[1][pewpew][4] += ['bullet']
                else:
                    session[1][pewpew][4] += ['bullet'] * int(GUNNER_MULTIPLIER * len(session[1]) + 1)
            else:
                session[1][pewpew][3].append('sharpshooter')
                if session[6] == 'mad':
                    session[1][pewpew][4] += ['bullet']
                else:
                    session[1][pewpew][4] += ['bullet'] * int(SHARPSHOOTER_MULTIPLIER * len(session[1]) + 1)
    gunners = [x for x in session[1] if 'gunner' in session[1][x][3]]
    for i in range(gamemode_roles['sharpshooter'] if 'sharpshooter' in gamemode_roles else 0):
        sharpshooter_choices = [x for x in gunners if 'sharpshooter' not in session[1][x][3]]
        if sharpshooter_choices:
            pewpew = random.choice(sharpshooter_choices)
            session[1][pewpew][3].remove('gunner')
            session[1][pewpew][4] = [x for x in session[1][pewpew][4] if x != 'bullet']
            session[1][pewpew][3].append('sharpshooter')
            session[1][pewpew][4] += ['bullet'] * int(SHARPSHOOTER_MULTIPLIER * len(session[1]) + 1)
    for i in range(gamemode_roles['assassin'] if 'assassin' in gamemode_roles else 0):
        if gamemode == 'random':
            assassin_choices = [x for x in session[1] if 'assassin' not in session[1][x][3]]
        else:
            assassin_choices = [x for x in session[1] if get_role(x, 'role') not in\
        ACTUAL_WOLVES + NEUTRAL_ROLES_ORDERED + ["traitor", "seer", "augur", "oracle", "harlot", "detective", "guardian angel"] and 'assassin' not in session[1][x][3]]
        if assassin_choices:
            assassin = random.choice(assassin_choices)
            session[1][assassin][3].append('assassin')
            if get_role(assassin, 'role') == 'village drunk':
                session[1][assassin][4].append('assassinate:{}'.format(random.choice([x for x in session[1] if x != assassin])))
    for i in range(gamemode_roles['blessed villager'] if 'blessed villager' in gamemode_roles else 0):
        if gamemode == 'random':
            blessed_choices = [x for x in session[1] if 'blessed' not in session[1][x][3]]
        else:
            blessed_choices = [x for x in session[1] if get_role(x, 'role') == 'villager' and not session[1][x][3]]
        if blessed_choices:
            blessed = random.choice(blessed_choices)
            session[1][blessed][3].append('blessed')
    if gamemode == 'belunga':
        for player in session[1]:
            session[1][player][4].append('belunga_totem')


async def end_game(reason, winners=None):
    global faftergame
    await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.online)
    if not session[0]:
        return
    session[0] = False
    if session[2]:
        if session[3][1]:
            session[4][1] += datetime.now() - session[3][1]
    else:
        if session[3][0]:
            session[4][0] += datetime.now() - session[3][0]
    msg = "<@{}> Game over! Night lasted **{:02d}:{:02d}**. Day lasted **{:02d}:{:02d}**. Game lasted **{:02d}:{:02d}**. \
          \n{}\n\n".format('> <@'.join(sort_players(session[1])), session[4][0].seconds // 60, session[4][0].seconds % 60,
          session[4][1].seconds // 60, session[4][1].seconds % 60, (session[4][0].seconds + session[4][1].seconds) // 60,
          (session[4][0].seconds + session[4][1].seconds) % 60, reason)
    if winners or session[6] == 'crazy':
        for player in session[1]:
            # ALTERNATE WIN CONDITIONS
            if session[1][player][0] and get_role(player, 'role') == 'crazed shaman':
                winners.append(player)
        winners = sort_players(set(winners)) # set ensures winners are unique
        if len(winners) == 0:
            msg += "No one wins!"
        elif len(winners) == 1:
            msg += "The winner is **{}**!".format(get_name(winners[0]))
        elif len(winners) == 2:
            msg += "The winners are **{}** and **{}**!".format(get_name(winners[0]), get_name(winners[1]))
        else:
            msg += "The winners are **{}**, and **{}**!".format('**, **'.join(map(get_name, winners[:-1])), get_name(winners[-1]))
    await send_lobby(msg)
    await log(1, "WINNERS: {}".format(winners))

    players = list(session[1])
    session[3] = [datetime.now(), datetime.now()]
    session[4] = [timedelta(0), timedelta(0)]
    session[6] = ''
    session[7] = {}
    
    global day_warning
    global day_timeout
    global night_warning
    global night_timeout
    day_warning = DEFAULT_DAY_WARNING
    day_timeout = DEFAULT_DAY_TIMEOUT
    night_warning = DEFAULT_NIGHT_WARNING
    night_timeout = DEFAULT_NIGHT_TIMEOUT

    perms = client.get_channel(GAME_CHANNEL).overwrites_for(client.get_server(WEREWOLF_SERVER).default_role)
    perms.send_messages = True
    await client.edit_channel_permissions(client.get_channel(GAME_CHANNEL), client.get_server(WEREWOLF_SERVER).default_role, perms)
    player_dict = {}
    for player in players:
        player_dict[player] = ('game end', "bot")
    await player_deaths(player_dict)

    if faftergame:
        # !faftergame <command> [<parameters>]
        # faftergame.content.split(' ')[0] is !faftergame
        command = faftergame.content.split(' ')[1]
        parameters = ' '.join(faftergame.content.split(' ')[2:])
        await commands[command][0](faftergame, parameters)
        faftergame = None


def win_condition():
    teams = {'village' : 0, 'wolf' : 0, 'neutral' : 0}
    injured_wolves = 0
    for player in session[1]:
        if session[1][player][0]:
            if 'injured' in session[1][player][4]:
                if get_role(player, 'actualteam') == 'wolf' and session[1][player][1] not in ['cultist', 'minion'] and 'entranced' not in session[1][player][4]:
                    injured_wolves += 1
            else:
                if session[1][player][1] in ['cultist', 'minion'] and session[6] != 'evilvillage':
                    teams['village'] += 1
                else:
                    teams[roles[session[1][player][1]][0]] += 1
    winners = []
    win_team = ''
    win_lore = ''
    win_msg = ''
    lovers = []
    players = session[1]
    for plr in players:
        for o in players[plr][4]:
            if o.startswith("lover:"):
                lvr = o.split(':')[1]
                if lvr in players:
                    if plr not in lovers and session[1][plr][0]:
                        lovers.append(plr)
                    if lvr not in lovers and session[1][lvr][0]:
                        lovers.append(lvr)
    if len([x for x in session[1] if session[1][x][0]]) == 0:
        win_lore = 'Everyone died. The town sits abandoned, collecting dust.'
        win_team = 'no win'
    elif len(lovers) == len([x for x in session[1] if session[1][x][0]]):
        win_team = 'lovers'
        win_lore = "Game over! The remaining villagers through their inseparable love for each other have agreed to stop all of this senseless violence and coexist in peace forever more. All remaining players win."
    elif len([x for x in session[1] if session[1][x][0] and (get_role(x, 'role') == 'succubus' or 'entranced' in session[1][x][4])]) == len([x for x in session[1] if session[1][x][0]]):
        win_team = 'succubi'
        win_lore = "Game over! The succub{} completely enthralled the village, making them officers in an ever-growing army set on spreading their control and influence throughout the entire world.".format('i' if len([x for x in session[1] if get_role(x, 'role') == 'succubus']) > 1 else 'us')
    elif len([x for x in session[1] if session[1][x][0] and (get_role(x, 'role') == 'piper' or 'charmed' in session[1][x][4])]) == len([x for x in session[1] if session[1][x][0]]):
        win_team = 'pipers'
        win_lore = "Game over! Everyone has fallen victim to the charms of the piper{0}. The piper{0} lead{1} the villagers away from the village, never to return...".format('' if len([x for x in session[1] if get_role(x, 'role') == 'piper']) < 2 else 's', 's' if len([x for x in session[1] if get_role(x, 'role') == 'piper']) < 2 else '')
    elif teams['village'] + teams['neutral'] <= teams['wolf'] and not (session[6] == 'evilvillage' and teams['village']):
        if session[6] == 'evilvillage':
            if not teams['village']:
                if [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']:
                    win_team = 'monster'
                    win_lore = "Game over! All the villagers are dead! As The cultists rejoice, they get destroyed by the monster{0}, causing the monster{0} to win.".format('s' if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']) > 1 else '')
                elif not [x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in ['cultist', 'minion']]:
                    win_team = 'no win'
                    win_lore = "Game over! All the villagers are dead, but the cult needed to sacrifice the wolves to accomplish that. The cult disperses shortly thereafter, and nobody wins."
                else:
                    win_team = 'wolf'
                    win_lore = "Game over! All the villagers are dead! The cultists rejoice with their wolf buddies and start plotting to take over the next village."
        elif [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']:
            win_team = 'monster'
            win_lore = "Game over! The number of uninjured villagers is equal or less than the number of living wolves! The wolves overpower the villagers but then get destroyed by the monster{0}, causing the monster{0} to win.".format('s' if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']) > 1 else '')
        else:
            win_team = 'wolf'
            win_lore = 'The number of uninjured villagers is equal or less than the number of living wolves! The wolves overpower the remaining villagers and devour them whole.'
    elif len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') in ACTUAL_WOLVES + ['traitor']]) == 0:
        # old version: teams['wolf'] == 0 and injured_wolves == 0:
        if [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']:
            win_team = 'monster'
            win_lore = "Game over! All the wolves are dead! As the villagers start preparing the BBQ, the monster{0} quickly kill{1} the remaining villagers, causing the monster{0} to win.".format('s' if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']) > 1 else '', '' if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']) > 1 else 's')
        else:
            if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') in ['cultist', 'minion']]) == teams['wolf'] and session[6] == 'evilvillage':
                win_team = 'village'
                win_lore = "Game over! All the wolves are dead! The villagers round up the remaining cultists, hang them, and live happily ever after."
            else:
                win_team = 'village'
                win_lore = 'All the wolves are dead! The surviving villagers gather the bodies of the dead wolves, roast them, and have a BBQ in celebration.'
    elif teams['village'] >= teams['wolf'] and session[6] == 'evilvillage':
        if [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']:
            win_team = 'monster'
            win_lore = "Game over! The number of uninjured cultists is equal or less than the number of living villagers! as the villagers regain control over the village, the monster{0} quickly kill{1} the remaining villagers, causing the monster{0} to win.".format('s' if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']) > 1 else '', '' if len([x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'monster']) > 1 else 's')
        elif not [x for x in session[1] if session[1][x][0] and get_role(x, 'role') in ['cultist', 'minion']]:
            win_team = 'village'
            win_lore = "Game over! All the cultists are dead! The now-exposed wolves are captured and killed by the remaining villagers. A BBQ party commences shortly thereafter."
        else:
            win_team = 'village'
            win_lore = "Game over! The number of uninjured cultists is equal or less than the number of living villagers! They manage to regain control of the village and dispose of the remaining cultists."
    else:
        return None
        
        
    for player in session[1]:
        lovers = []
        for n in session[1][player][4]:
            if n.startswith('lover:'):
                lovers.append(n.split(':')[1])
        role = get_role(player, 'role')
        templates = get_role(player, 'templates')
        if get_role(player, 'role') == 'piper' and win_team == 'pipers':
            winners.append(player)
        if (get_role(player, 'role') == 'succubus' or 'entranced' in session[1][player][4]) and win_team == 'succubi':
            winners.append(player)
        if get_role(player, 'actualteam') == win_team:
            winners.append(player)
        if [x for x in lovers if (session[1][x][0] and session[1][player][0])]:
            winners.append(player)
        if get_role(player, 'role') == 'vengeful ghost' and not session[1][player][0] and [x.split(':')[1] for x in session[1][player][4] if x.startswith("vengeance:")] and [x.split(':')[1] for x in session[1][player][4] if x.startswith("vengeance:")].pop() != win_team:
            winners.append(player)
        if (get_role(player, 'role') == 'amnesiac' or (get_role(player, 'role') == 'vengeful ghost' and session[1][player][0]) and win_team == 'village'):
            winners.append(player)
        if get_role(player, 'role') == 'jester' and 'lynched' in session[1][player][4]:
            winners.append(player)
        if get_role(player, 'role') == 'monster' and session[1][player][0] and win_team == 'monster':
            winners.append(player)
        if get_role(player, 'role') == 'clone' and session[1][player][0]:
            winners.append(player)
        if get_role(player, 'role') == 'lycan' and win_team == 'village':
            winners.append(player)
        if (get_role(player, 'role') == 'turncoat') and (('side:villagers' in session[1][player][4] and win_team == 'village') or ('side:wolves' in session[1][player][4] and win_team == 'wolf')):
            winners.append(player)
        if ((win_team != 'succubi' and 'entranced' in session[1][player][4]) or 'charmed' in session[1][player][4]) and player in winners:
            winners.remove(player)
    return [win_team, win_lore + '\n\n' + end_game_stats(), winners]


def end_game_stats():
    role_msg = ""
    role_dict = {}
    for role in roles:
        role_dict[role] = []
    for player in session[1]:
        if 'traitor' in session[1][player][4]:
            session[1][player][1] = 'traitor'
            session[1][player][4].remove('traitor')
        if 'wolf_cub' in session[1][player][4]:
            session[1][player][1] = 'wolf cub'
            session[1][player][4].remove('wolf_cub')
        role_dict[session[1][player][1]].append(player)
        if 'cursed' in session[1][player][3]:
            role_dict['cursed villager'].append(player)
        if 'gunner' in session[1][player][3]:
            role_dict['gunner'].append(player)
        if 'assassin' in session[1][player][3]:
            role_dict['assassin'].append(player)
        if 'mayor' in session[1][player][3]:
            role_dict['mayor'].append(player)
        if 'sharpshooter' in session[1][player][3]:
            role_dict['sharpshooter'].append(player)

    for key in sort_roles(role_dict):
        value = sort_players(role_dict[key])
        if len(value) == 0:
            pass
        elif len(value) == 1:
            role_msg += "The **{}** was **{}**. ".format(key, get_name(value[0]))
        elif len(value) == 2:
            role_msg += "The **{}** were **{}** and **{}**. ".format(roles[key][1], get_name(value[0]), get_name(value[1]))
        else:
            role_msg += "The **{}** were **{}**, and **{}**. ".format(roles[key][1], '**, **'.join(map(get_name, value[:-1])), get_name(value[-1]))

    lovers = []

    for player in session[1]:
        for o in session[1][player][4]:
            if o.startswith("lover:"):
                lover = o.split(':')[1]
                lovers.append(tuple(sort_players([player, lover])))
    lovers = list(set(lovers))
    # create a list of unique lover pairs
    sorted_second_lover = sort_players(x[1] for x in lovers)
    sorted_first_lover = sort_players(x[0] for x in lovers)
    # sort by second lover then first lover in the pair
    lovers_temp = []
    for l in sorted_second_lover:
        for pair in list(lovers):
            if pair[1] == l:
                lovers_temp.append(pair)
                lovers.remove(pair)
    lovers = list(lovers_temp)
    lovers_temp = []
    for l in sorted_first_lover:
        for pair in list(lovers):
            if pair[0] == l:
                lovers_temp.append(pair)
                lovers.remove(pair)
    lovers = list(lovers_temp)
    if len(lovers) == 0:
        pass
    elif len(lovers) == 1:
        # *map(get_name, lovers[0]) just applies get_name to each lover then unpacks the result into format
        role_msg += "The **lovers** were **{}/{}**. ".format(*map(get_name, lovers[0]))
    elif len(lovers) == 2:
        role_msg += "The **lovers** were **{}/{}** and **{}/{}**. ".format(*map(get_name, lovers[0] + lovers[1]))
    else:
        role_msg += "The **lovers** were {}, and **{}/{}**. ".format(
            ', '.join('**{}/{}**'.format(*map(get_name, x)) for x in lovers[:-1]), *map(get_name, lovers[-1]))
    return role_msg


def get_name(player):
    member = client.get_server(WEREWOLF_SERVER).get_member(player)
    if member:
        return str(member.display_name)
    else:
        return str(player)


def get_player(string):
    string = string.lower()
    users = []
    discriminators = []
    nicks = []
    users_contains = []
    nicks_contains = []
    for player in session[1]:
        if string == player.lower() or string.strip('<@!>') == player:
            return player
        member = client.get_server(WEREWOLF_SERVER).get_member(player)
        if member:
            if member.name.lower().startswith(string):
                users.append(player)
            if string.strip('#') == member.discriminator:
                discriminators.append(player)
            if member.display_name.lower().startswith(string):
                nicks.append(player)
            if string in member.name.lower():
                users_contains.append(player)
            if string in member.display_name.lower():
                nicks_contains.append(player)
        elif get_player(player).lower().startswith(string):
            users.append(player)
    if len(users) == 1:
        return users[0]
    if len(discriminators) == 1:
        return discriminators[0]
    if len(nicks) == 1:
        return nicks[0]
    if len(users_contains) == 1:
        return users_contains[0]
    if len(nicks_contains) == 1:
        return nicks_contains[0]
    return None


def sort_players(players):
    fake = []
    real = []
    for player in players:
        if client.get_server(WEREWOLF_SERVER).get_member(player):
            real.append(player)
        else:
            fake.append(player)
    return sorted(real, key=get_name) + sorted(fake, key=int)


def get_role(player, level):
    # level: {team: reveal team only; actualteam: actual team; seen: what the player is seen as; death: role taking into account cursed and cultist and traitor; actual: actual role}
    # (terminology: role = what you are, template = additional things that can be applied on top of your role)
    # cursed, gunner, blessed, mayor, assassin are all templates
    # so you always have exactly 1 role, but can have 0 or more templates on top of that
    # revealing totem (and similar powers, like detective id) only reveal roles
    if player in session[1]:
        role = session[1][player][1]
        templates = session[1][player][3]
        if level == 'team':
            if roles[role][0] == 'wolf':
                if not role in ROLES_SEEN_VILLAGER:
                    return "wolf"
            return "village"
        elif level == 'actualteam':
            return roles[role][0]
        elif level == 'seen':
            seen_role = None
            if role in ROLES_SEEN_WOLF:
                seen_role = 'wolf'
            elif session[1][player][1] in ROLES_SEEN_VILLAGER:
                seen_role = 'villager'
            else:
                seen_role = role
            for template in templates:
                if template in ROLES_SEEN_WOLF:
                    seen_role = 'wolf'
                    break
                if template in ROLES_SEEN_VILLAGER:
                    seen_role = 'villager'
            return seen_role
        elif level == 'seenoracle':
            seen_role = get_role(player, 'seen')
            if seen_role != 'wolf':
                seen_role = 'villager'
            return seen_role
        elif level == 'death':
            returnstring = ''
            if role == 'traitor':
                returnstring += 'villager'
            else:
                returnstring += role
            return returnstring
        elif level == 'deathstats':
            returnstring = ''
            if role == 'traitor':
                returnstring += 'villager'
            else:
                returnstring += role
            return returnstring
        elif level == 'role':
            return role
        elif level == 'templates':
            return templates
        elif level == 'actual':
            return ' '.join(templates + [role])
    return None


def get_roles(gamemode, players):
    if gamemode.startswith('roles'):
        role_string = ' '.join(gamemode.split(' ')[1:])
        if role_string != '':
            gamemode_roles = {}
            separator = ','
            if ';' in role_string:
                separator = ';'
            for role_piece in role_string.split(separator):
                piece = role_piece.strip()
                if '=' in piece:
                    role, amount = piece.split('=')
                elif ':' in piece:
                    role, amount = piece.split(':')
                else:
                    return None
                amount = amount.strip()
                if amount.isdigit():
                    gamemode_roles[role.strip()] = int(amount)
            return gamemode_roles
    elif gamemode in gamemodes:
        if players in range(gamemodes[gamemode]['min_players'], gamemodes[gamemode]['max_players'] + 1):
            if gamemode == 'random':
                exit = False
                while not exit:
                    exit = True
                    available_roles = [x for x in roles if x not in TEMPLATES_ORDERED\
                                        and x not in ('villager', 'cultist')]
                    gamemode_roles = dict((x, 0) for x in available_roles)
                    gamemode_roles[random.choice([x for x in ACTUAL_WOLVES if x != 'wolf cub'])] += 1 # ensure at least 1 wolf that can kill
                    for i in range(players - 1):
                        gamemode_roles[random.choice(available_roles)] += 1
                    gamemode_roles['gunner'] = random.randrange(int(players ** 1.2 / 4))
                    gamemode_roles['cursed villager'] = random.randrange(int(players ** 1.2 / 3))
                    teams = {'village' : 0, 'wolf' : 0, 'neutral' : 0}
                    for role in gamemode_roles:
                        if role not in TEMPLATES_ORDERED:
                            teams[roles[role][0]] += gamemode_roles[role]
                    if teams['wolf'] >= teams['village'] + teams['neutral']:
                        exit = False
                for role in dict(gamemode_roles):
                    if gamemode_roles[role] == 0:
                        del gamemode_roles[role]
                return gamemode_roles
            else:
                gamemode_roles = {}
                for role in roles:
                    if role in gamemodes[gamemode]['roles'] and gamemodes[gamemode]['roles'][role][\
                    players - MIN_PLAYERS] > 0:
                        gamemode_roles[role] = gamemodes[gamemode]['roles'][role][players - MIN_PLAYERS]
                return gamemode_roles
    return None


def get_votes(totem_dict):
    voteable_players = [x for x in session[1] if session[1][x][0]]
    able_players = [x for x in voteable_players if 'injured' not in session[1][x][4]]
    vote_dict = {'abstain' : 0}
    for player in voteable_players:
        vote_dict[player] = 0
    able_voters = [x for x in able_players if totem_dict[x] == 0]
    for player in able_voters:
        if session[1][player][2] in vote_dict:
            vote_dict[session[1][player][2]] += 1
        if 'influence_totem' in session[1][player][4] and session[1][player][2] in vote_dict:
            vote_dict[session[1][player][2]] += 1
    for player in [x for x in able_players if totem_dict[x] != 0]:
        if totem_dict[player] < 0:
            vote_dict['abstain'] += 1
        else:
            for p in [x for x in voteable_players if x != player]:
                vote_dict[p] += 1
    return vote_dict


def _autocomplete(string, lst):
    if string in lst:
        return (string, 1)
    else:
        choices = []
        for item in lst:
            if item.startswith(string):
                choices.append(item)
        if len(choices) == 1:
            return (choices[0], 1)
        else:
            return (choices, len(choices))


def verify_gamemode(gamemode, verbose=True):
    msg = ''
    good = True
    for i in range(gamemodes[gamemode]['max_players'] - gamemodes[gamemode]['min_players'] + 1):
        total = sum(gamemodes[gamemode]['roles'][role][i + gamemodes[gamemode]['min_players'] - MIN_PLAYERS] for role in gamemodes[gamemode]['roles']\
        if role not in TEMPLATES_ORDERED)
        msg += str(total)
        if total != i + gamemodes[gamemode]['min_players'] and total != 0:
            good = False
            msg += ' - should be ' + str(i + gamemodes[gamemode]['min_players'])
        msg += '\n'
    msg = msg[:-1]
    if verbose:
        return msg
    else:
        return good


def verify_gamemodes(verbose=True):
    msg = ''
    good = True
    for gamemode in sorted(gamemodes):
        msg += gamemode + '\n'
        result = verify_gamemode(gamemode)
        resultlist = result.split('\n')
        for i in range(len(resultlist)):
            if resultlist[i] != str(i + gamemodes[gamemode]['min_players']) and resultlist[i] != '0':
                msg += result
                good = False
                break
        else:
            msg += 'good'
        msg += '\n\n'
    if verbose:
        return msg
    else:
        return good


async def wolfchat(message, author=''):
    if isinstance(message, discord.Message):
        author = message.author.id
        msg = message.content
    else:
        msg = str(message)

    member = client.get_server(WEREWOLF_SERVER).get_member(author)
    if member:
        athr = member.display_name
    else:
        athr = author
    for wolf in [x for x in session[1] if x != author and session[1][x][0] and session[1][x][1] in WOLFCHAT_ROLES and client.get_server(WEREWOLF_SERVER).get_member(x)]:
        try:
            pfx = "**[Wolfchat]**"
            if athr != '':
                pfx += " message from **{}**".format(athr)
            await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(wolf), "{}: {}".format(pfx, msg))
        except discord.Forbidden:
            pass


async def player_idle(message):
    while message.author.id in session[1] and not session[0]:
        await asyncio.sleep(1)
    while message.author.id in session[1] and session[0] and session[1][message.author.id][0]:
        def check(msg):
            if not message.author.id in session[1] or not session[1][message.author.id][0] or not session[0]:
                return True
            if msg.author.id == message.author.id and msg.channel.id == client.get_channel(GAME_CHANNEL).id:
                return True
            return False
        msg = await client.wait_for_message(author=message.author, channel=client.get_channel(GAME_CHANNEL), timeout=PLAYER_TIMEOUT, check=check)
        if msg == None and message.author.id in session[1] and session[0] and session[1][message.author.id][0]:
            await send_lobby(message.author.mention + "**, you have been idling for a while. Please say something soon or you might be declared dead.**")
            try:
                await client.send_message(message.author, "**You have been idling in #" + client.get_channel(GAME_CHANNEL).name + " for a while. Please say something soon or you might be declared dead.**")
            except discord.Forbidden:
                pass
            msg = await client.wait_for_message(author=message.author, channel=client.get_channel(GAME_CHANNEL), timeout=PLAYER_TIMEOUT2, check=check)
            if msg == None and message.author.id in session[1] and session[0] and session[1][message.author.id][0]:
                if session[6] == 'noreveal':
                    await send_lobby("**" + get_name(message.author.id) + "** didn't get out of bed for a very long time and has been found dead.")
                else:
                    await send_lobby("**" + get_name(message.author.id) + "** didn't get out of bed for a very long time and has been found dead. "
                                          "The survivors bury the **" + get_role(message.author.id, 'death') + '**.')
                if message.author.id in stasis:
                    stasis[message.author.id] += QUIT_GAME_STASIS
                else:
                    stasis[message.author.id] = QUIT_GAME_STASIS
                await player_deaths({message.author.id : ('idle', "bot")})
                await check_traitor()
                await log(1, "{} ({}) IDLE OUT".format(message.author.display_name, message.author.id))


def is_online(user_id):
    member = client.get_server(WEREWOLF_SERVER).get_member(user_id)
    if member:
        if member.status in [discord.Status.online, discord.Status.idle]:
            return True
    return False


async def player_deaths(players_dict): # players_dict = {dead : (reason, kill_team), ...}
    for player in players_dict:
        reason = players_dict[player][0]
        kill_team = players_dict[player][1]
        if player not in session[1]:
            return
        ingame = 'IN GAME'
        if session[0] and reason != 'game cancel':
            session[1][player][0] = False
            lovers = []
            for o in session[1][player][4]:
                if o.startswith('lover:'):
                    lovers.append(o.split(":")[1])
            assassin_target = ""
            for o in session[1][player][4]:
                if o.startswith('assassinate:') and "assassin" in get_role(player, "templates") and kill_team != "bot":
                    assassin_target = o.split(":")[1]
                    break
                    
            if session[0]:
                if assassin_target:
                    if session[1][assassin_target][0] and assassin_target not in players_dict and not ("protection_totem2" in session[1][assassin_target][4] or "guarded" in session[1][assassin_target][4]) and not 'blessed' in get_role(assassin_target, 'templates') and not [x for x in session[1][assassin_target][4] if x.startswith('bodyguard:')]:
                        await send_lobby("Before dying, **{0}** quickly slits **{1}**'s throat. The village mourns the loss of a{2} **{3}**.".format(get_name(player), get_name(assassin_target), "n" if get_role(assassin_target, "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(assassin_target, "death")))
                        await player_deaths({assassin_target : ("assassination", get_role(player, 'actualteam'))})
                    elif 'blessed' in get_role(assassin_target, 'templates'):
                        try:
                            await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(player), "**{0}** seems to be blessed, causing your assassination attempt to fail.".format(get_name(assassin_target)))
                        except discord.Forbidden:
                            pass
                    elif "protection_totem2" in session[1][assassin_target][4]:
                        await send_lobby("Before dying, **{0}** quickly attempts to slit **{1}**'s throat; however, {1}'s totem emits a brilliant flash of light, causing the attempt to miss.".format(get_name(player), get_name(assassin_target)))
                    elif "guarded" in session[1][assassin_target][4]:
                        await send_lobby("Before dying, **{0}** quickly attempts to slit **{1}**'s throat; however, a guardian angel was on duty and able to foil the attempt.".format(get_name(player), get_name(assassin_target)))
                    elif [x for x in session[1][assassin_target][4] if x.startswith('bodyguard:')]:
                        await send_lobby("Sensing danger, **{2}** shoves **{1}** aside to save them from **{0}**.".format(get_name(player), get_name(assassin_target), get_name([x for x in session[1][assassin_target][4] if x.startswith('bodyguard:')].pop().split(':')[1])))
                for lover in lovers:
                    if session[1][lover][0] and kill_team != "bot" and lover not in players_dict:
                        await send_lobby("Saddened by the loss of their lover, **{0}**, a{1} **{2}**, commits suicide.".format(get_name(lover), "n" if get_role(lover, "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(lover, "death")))
                        await player_deaths({lover : ("lover suicide", kill_team)})
                        
                #mad scientist target choosing
                mad_kills = []
                if get_role(player, 'role') == 'mad scientist' and kill_team != "bot":
                    players = [x for x in session[1]]
                    #mad scientist skips dead players if over 16p, random mode, rapidfire mode (or maelstrom)
                    skip_dead = False
                    if len(players) > 15 or session[6] in ['random', 'rapidfire']:
                        skip_dead = True
                    first = players.index(player)
                    #look for the first players not dead (or break after one loop)
                    while not session[1][players[first]][0]:
                        if first == 0:
                            first = len(players) - 1
                        else:
                            first -= 1
                        if not skip_dead:
                            break
                    if session[1][players[first]][0]:
                        mad_kills.append(players[first])
                    #the same on the other side
                    second = players.index(player)
                    while not session[1][players[second]][0]:
                        if second == len(players) - 1:
                            second = 0
                        else:
                            second += 1
                        if not skip_dead:
                            break
                    if session[1][players[second]][0]:
                        mad_kills.append(players[second])
                        
                #kill those next to the mad scientist if they aren't protected
                if mad_kills:
                    for mad_target in mad_kills:
                        if "blessed" in session[1][mad_target][4]:
                            mad_kills.remove(mad_target)
                        elif "protection_totem2" in session[1][mad_target][4]:
                            await send_lobby("Before the chemical can harm **{1}**, their totem flashes and they are teleported away from **{0}**.".format(get_name(player), get_name(mad_target)))
                            mad_kills.remove(mad_target)
                        elif "guarded" in session[1][mad_target][4]:
                            await send_lobby("Sensing danger, a guardian angel whisks **{1}** away from **{0}**.".format(get_name(player), get_name(mad_target)))
                            mad_kills.remove(mad_target)
                        for bodyguard in [x for x in session[1] if get_role(x, 'role') == "bodyguard" and session[1][x][2] == mad_target]:
                            if bodyguard and mad_target in mad_kills:
                                await send_lobby("Sensing danger, **{2}** shoves **{1}** aside to save them from **{0}**.".format(get_name(player), get_name(mad_target), get_name(bodyguard)))
                                mad_kills.remove(mad_target)
                                if bodyguard not in mad_kills:
                                    mad_kills.append(bodyguard)
                    if len(mad_kills) == 2:
                        await send_lobby("**{0}** throws a potent chemical into the crowd. **{1}**, a{2} **{3}**, and **{4}**, a{5} **{6}**, are hit and die.".format(get_name(player), get_name(mad_kills[0]), "n" if get_role(mad_kills[0], "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(mad_kills[0], "death"), get_name(mad_kills[1]), "n" if get_role(mad_kills[1], "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(mad_kills[1], "death")))
                        await player_deaths({mad_kills[0] : ("mad scientist", 'village'), mad_kills[1] : ("mad scientist", 'village')})
                    elif len(mad_kills) == 1:
                        await send_lobby("**{0}** throws a potent chemical into the crowd. **{1}**, a{2} **{3}**, is hit and dies.".format(get_name(player), get_name(mad_kills[0]), "n" if get_role(mad_kills[0], "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(mad_kills[0], "death")))
                        await player_deaths({mad_kills[0] : ("mad scientist", 'village')})
                        
                if 'desperation_totem' in session[1][player][4] and reason == "lynch":
                    end_voter = ""
                    for x in session[1]:
                        if max(list(chain.from_iterable([[i for i in session[1][x][4] if i.startswith("vote:")] for x in session[1] if session[1][x][0]]))) in session[1][x][4] and session[1][x][2] == player:
                            end_voter = x
                    if end_voter and end_voter not in players_dict and get_role(player, 'role') != 'fool':
                        await send_lobby("As the noose is being fitted, **{0}**'s totem emits a brilliant flash of light. When the villagers are able to see again, they discover that **{1}**, a{2} **{3}**, has fallen over dead.".format(get_name(player), get_name(end_voter), "n" if get_role(end_voter, "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(end_voter, "death")))
                        await player_deaths({end_voter : ("desperation", get_role(player, 'actualteam'))})
                
                #clone taking the dead's role
                for clone in [x for x in session[1] if (session[1][x][0] and get_role(x, 'role') == "clone" and "clone:{}".format(player) in session[1][x][4])]:
                    member = client.get_server(WEREWOLF_SERVER).get_member(clone)
                    role = get_role(player, 'role')
                    cloning = player
                    #finding final target from who the clones were cloning
                    if role == "clone":
                        while role == 'clone' and not session[1][cloning][0]:
                            for new_target in [x for x in session[1][player][4] if x.startswith('clone:')]:
                                session[1][clone][4].append(new_target)
                                session[1][clone][4].remove("clone:{}".format(cloning))
                                cloning = (new_target.split(':')[1])
                                role == get_role(cloning, 'role')
                        if member:
                            try:
                                await client.send_message(member, "Your target was a clone and you are now cloning their target, **{0}**.".format(get_name(cloning)))
                            except discord.Forbidden:
                                pass
                                
                    #if the clone target is dead (in case we cloned a clone but their target is alive)
                    if not session[1][cloning][0]:
                        if role == "amnesiac":
                            role = [x.split(':')[1].replace("_", " ") for x in session[1][player][4] if x.startswith("role:")].pop()
                        if role == "priest" and bless in session[1][player][4]:
                            session[1][clone][4].append("bless")
                        elif role == "hunter" and "hunterbullet" in session[1][player][4]:
                            session[1][clone][4].append("hunterbullet")
                        elif role == "piper"  and "charmed" in session[1][clone][4]:
                            session[1][clone][4].remove("charmed")
                        elif role == "succubus"  and "entranced" in session[1][clone][4]:
                            session[1][clone][4].remove("entranced")
                        session[1][clone][1] = role
                        if member:
                            try:
                                await client.send_message(member, "You have cloned your target and are now a **{0}**.".format(role))
                            except discord.Forbidden:
                                pass
                        if role in WOLFCHAT_ROLES:
                            await wolfchat("{0} is now a **{1}**!".format(get_name(clone), role))
                        elif role == "minion":
                           await _send_role_info(clone)
                       
                if get_role(player, 'role') ==  'succubus' and not [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'succubus']:
                    if kill_team != 'bot':
                        foul_dict = {}
                        foul_message = ''
                        for entranced in [x for x in session[1] if session[1][x][0] and 'entranced' in session[1][x][4] and x not in players_dict]:
                            foul_message += "As the last remaining succubus dies, a foul curse causes **{0}**, a{1} **{2}** to wither away and die in front of the astonished village.\n".format(get_name(entranced), "n" if get_role(entranced, "death").lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", get_role(entranced, "death"))
                            foul_dict[entranced] = ('foul curse', kill_team)
                        if foul_message:
                            await send_lobby(foul_message)
                            await player_deaths(foul_dict)
                    else:
                        for entranced in [x for x in session[1] if session[1][x][0] and 'entranced' in session[1][x][4] and x not in players_dict]:
                            session[1][entranced][4].remove('entranced')
                            member = client.get_server(WEREWOLF_SERVER).get_member(entranced)
                            if member:
                                try:
                                    await client.send_message(member, "You are no longer entranced. **Your win conditions have reset to normal.**")
                                except discord.Forbidden:
                                    pass
                if get_role(player, 'role') == "vengeful ghost" and (kill_team != "bot" and not reason == 'gunner suicide'):
                    session[1][player][4].append("vengeance:{}".format(kill_team))
                    member = client.get_server(WEREWOLF_SERVER).get_member(player)
                    if member:
                        try:
                            await client.send_message(member, "OOOooooOOOOooo! You are the **vengeful ghost**. It is now your job to exact your revenge on the **{0}** that killed you.".format('villagers' if kill_team == 'village' else 'wolves'))
                        except discord.Forbidden:
                            pass
                if get_role(player, 'role') == 'piper' and not [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'piper']:
                    for player_ in session[1]:
                        session[1][player_][4] = [x for x in session[1][player_][4] if not x in ['charmed', 'tocharm']]
                        
                #timelord stuff
                global day_warning
                global day_timeout
                global night_warning
                global night_timeout
                if get_role(player, 'role') == 'time lord' and (kill_team != 'bot') and day_warning != 45:
                    day_warning = 45
                    day_timeout = 60
                    night_warning = 20
                    night_timeout = 30
                    await send_lobby("The time lord has died. Night will now only last **{0}** seconds, and day **{1}** seconds. Better be speedy!".format(night_timeout, day_timeout))
                    #reset day timer?                
        else:
            ingame = 'NOT IN GAME'
            del session[1][player]
        member = client.get_server(WEREWOLF_SERVER).get_member(player)
        if member:
            await client.remove_roles(member, PLAYERS_ROLE)
        if session[0] and kill_team != "bot":
            if get_role(player, 'role') == 'wolf cub':
                for p in session[1]:
                    if session[1][p][0] and get_role(p, 'role') in ACTUAL_WOLVES + ['traitor']:
                        session[1][p][4].append('angry')
        for p in [x for x in session[1] if "assassin" in get_role(x, "templates") and "assassinate:{}".format(player) in session[1][x][4]]:
            session[1][p][4] = [x for x in session[1][p][4] if x != "assassinate:{}".format(player)]
            if get_role(p, 'role') == 'village drunk':
                session[1][p][4].append('assassinate:{}'.format(random.choice([x for x in session[1] if x != p])))
                
        await log(0, "{} ({}) PLAYER DEATH {} FOR {}".format(get_name(player), player, ingame, reason))


async def check_traitor():
    if not session[0] and win_condition() == None:
        return
    wolf_cub_turned = False
    for other in [session[1][x][4] for x in session[1]]:
        if 'traitor' in other:
            # traitor already turned
            return
    wolf_team_alive = [x for x in session[1] if session[1][x][0] and get_role(x, 'role') in [
        'traitor'] + ACTUAL_WOLVES]
    if len(wolf_team_alive) == 0:
        # no wolves alive; don't play traitor turn message
        return
    wolf_team_no_traitors = [x for x in wolf_team_alive if get_role(x, 'role') != 'traitor']
    wolf_team_no_cubs = [x for x in wolf_team_no_traitors if get_role(x, 'role') != 'wolf cub']
    if len(wolf_team_no_cubs) == 0:
        cubs = [x for x in wolf_team_alive if get_role(x, 'role') == 'wolf cub']
        if cubs:
            await log(1, ', '.join(cubs) + " grew up into wolf")
            for cub in cubs:
                session[1][cub][4].append('wolf_cub')
                session[1][cub][1] = 'wolf'
                member = client.get_server(WEREWOLF_SERVER).get_member(cub)
                if member:
                    try:
                        await client.send_message(member, "You have grown up into a wolf and vowed to take revenge for your dead parents!")
                    except discord.Forbidden:
                        pass
                    await send_lobby("**The villagers listen horrified as they hear growling deepen in pitch. The wolf will do whatever it takes to avenge their parents!**")
    if len(wolf_team_no_traitors) == 0:
        traitors = [x for x in wolf_team_alive if get_role(x, 'role') == 'traitor']
        await log(1, ', '.join(traitors) + " turned into wolf")
        for traitor in traitors:
            session[1][traitor][4].append('traitor')
            session[1][traitor][1] = 'wolf'
            member = client.get_server(WEREWOLF_SERVER).get_member(traitor)
            if member:
                try:
                    await client.send_message(member, "HOOOOOOOOOWL. You have become... a wolf!\nIt is up to you to avenge your fallen leaders!")
                except discord.Forbidden:
                    pass
        if session[6] != 'noreveal':
            await send_lobby("**The villagers, during their celebrations, are frightened as they hear a loud howl. The wolves are not gone!**")


def sort_roles(role_list):
    role_list = list(role_list)
    result = []
    for role in WOLF_ROLES_ORDERED + VILLAGE_ROLES_ORDERED + NEUTRAL_ROLES_ORDERED + TEMPLATES_ORDERED:
        result += [role] * role_list.count(role)
    return result


async def run_game():
    # NOTE: Migrated to another file while updating
    # TODO:  this functionality needs to be added back in order to work.


async def game_loop(ses=None):
    # NOTE: Migrated to another file while updating
    # TODO:  this functionality needs to be added back in order to work.


async def start_votes(player):
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < 60:
        votes_needed = max(2, min(len(session[1]) // 4 + 1, 4))
        votes = len([x for x in session[1] if session[1][x][1] == 'start'])
        if votes >= votes_needed or session[0] or votes == 0:
            break
        await asyncio.sleep(0.1)
    else:
        for player in session[1]:
            session[1][player][1] = ''
        await send_lobby("Not enough votes to start, resetting start votes.")

async def rate_limit(message):
    if not (message.channel.is_private or message.content.startswith(BOT_PREFIX)) or message.author.id in ADMINS or message.author.id == OWNER_ID:
        return False
    global ratelimit_dict
    global IGNORE_LIST
    if message.author.id not in ratelimit_dict:
        ratelimit_dict[message.author.id] = 1
    else:
        ratelimit_dict[message.author.id] += 1
    if ratelimit_dict[message.author.id] > IGNORE_THRESHOLD:
        if not message.author.id in IGNORE_LIST:
            IGNORE_LIST.append(message.author.id)
            await log(2, message.author.name + " (" + message.author.id + ") was added to the ignore list for rate limiting.")
        try:
            await reply(message, "You've used {0} commands in the last {1} seconds; I will ignore you from now on.".format(IGNORE_THRESHOLD, TOKEN_RESET))
        except discord.Forbidden:
            await send_lobby(message.author.mention +
                                      " used {0} commands in the last {1} seconds and will be ignored from now on.".format(IGNORE_THRESHOLD, TOKEN_RESET))
        finally:
            return True
    if message.author.id in IGNORE_LIST or ratelimit_dict[message.author.id] > TOKENS_GIVEN:
        if ratelimit_dict[message.author.id] > TOKENS_GIVEN:
            await log(2, "Ignoring message from " + message.author.name + " (" + message.author.id + "): `" + message.content + "` since no tokens remaining")
        return True
    return False

async def do_rate_limit_loop():
    await client.wait_until_ready()
    global ratelimit_dict
    while not client.is_closed:
        for user in ratelimit_dict:
            ratelimit_dict[user] = 0
        await asyncio.sleep(TOKEN_RESET)

async def game_start_timeout_loop():
    session[5] = datetime.now()
    while not session[0] and len(session[1]) > 0 and datetime.now() - session[5] < timedelta(seconds=GAME_START_TIMEOUT):
        await asyncio.sleep(0.1)
    if not session[0] and len(session[1]) > 0:
        session[0] = True
        await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.online)
        await send_lobby("{0}, the game has taken too long to start and has been cancelled. "
                          "If you are still here and would like to start a new game, please do `!join` again.".format(PLAYERS_ROLE.mention))
        perms = client.get_channel(GAME_CHANNEL).overwrites_for(client.get_server(WEREWOLF_SERVER).default_role)
        perms.send_messages = True
        await client.edit_channel_permissions(client.get_channel(GAME_CHANNEL), client.get_server(WEREWOLF_SERVER).default_role, perms)
        player_dict = {}
        for player in list(session[1]):
            player_dict[player] = ('game cancel', "bot")
        await player_deaths(player_dict)
        session[0] = False
        session[3] = [datetime.now(), datetime.now()]
        session[4] = [timedelta(0), timedelta(0)]
        session[6] = ''
        session[7] = {}

async def wait_timer_loop():
    global wait_bucket
    timer = datetime.now()
    while not session[0] and len(session[1]) > 0:
        if datetime.now() - timer > timedelta(seconds=WAIT_BUCKET_DELAY):
            timer = datetime.now()
            wait_bucket = min(wait_bucket + 1, WAIT_BUCKET_MAX)
        await asyncio.sleep(0.5)

async def backup_settings_loop():
    while not client.is_closed:
        print("BACKING UP SETTINGS")
        with open(NOTIFY_FILE, 'w') as notify_file:
            notify_file.write(','.join([x for x in notify_me if x != '']))
        with open(STASIS_FILE, 'w') as stasis_file:
            json.dump(stasis, stasis_file)
        await asyncio.sleep(BACKUP_INTERVAL)

############## POST-DECLARATION STUFF ###############
COMMANDS_FOR_ROLE = {'see' : ['seer', 'oracle', 'augur', 'doomsayer'],
                     'kill' : ['wolf', 'werecrow', 'werekitten', 'wolf shaman', 'hunter', 'vengeful ghost', 'doomsayer', 'wolf mystic'],
                     'give' : ['shaman', 'wolf shaman'],
                     'visit' : ['harlot', 'succubus'],
                     'shoot' : ['gunner', 'sharpshooter'],
                     'observe' : ['werecrow', 'sorcerer'],
                     'pass' : ['harlot', 'hunter', 'guardian angel', 'succubus', 'warlock', 'bodyguard', 'piper', 'turncoat'],
                     'id' : ['detective'],
                     'choose' : ['matchmaker'],
                     'guard' : ['guardian angel', 'bodyguard'],
                     'target' : ['assassin'],
                     'bless' : ['priest'],
                     'consecrate' : ['priest'],
                     'entrance' : ['succubus'],
                     'hex' : ['hag'],
                     'curse' : ['warlock'],
                     'charm' : ['piper'],
                     'clone' : ['clone'],
                     'side' : ['turncoat']}
GAMEPLAY_COMMANDS = ['join', 'j', 'start', 'vote', 'lynch', 'v', 'abstain', 'abs', 'nl', 'stats', 'leave', 'q', 'role', 'roles']
GAMEPLAY_COMMANDS += list(COMMANDS_FOR_ROLE)

# {role name : [team, plural, description]}
roles = {'wolf' : ['wolf', 'wolves', "Your job is to kill all of the villagers. Type `kill <player>` in private message to kill them."],
         'werecrow' : ['wolf', 'werecrows', "You are part of the wolfteam. Use `observe <player>` during the night to see if they were in bed or not. "
                                            "You may also use `kill <player>` to kill them."],
         'wolf cub' : ['wolf', 'wolf cubs', "You are part of the wolfteam. While you cannot kill anyone, the other wolves will "
                                            "become enraged if you die and will get two kills the following night."],
         'werekitten' : ['wolf', 'werekittens', "You are like a normal wolf, except due to your cuteness, you are seen as a villager "
                                                "and gunners will always miss when they shoot you. Use `kill <player>` in private message "
                                                "to vote to kill <player>."],
         'wolf shaman' : ['wolf', 'wolf shamans', "You are part of the wolfteam. You may use `kill <player>` to kill a villager. You can also select "
                                                  "a player to receive a totem each night by using `give <player>.` You may give yourself a totem, "
                                                  "but you may not give the same player a totem two nights in a row. If you do not give the totem "
                                                  "to anyone, it will be given to a random player."],
         'traitor' : ['wolf', 'traitors', "You are exactly like a villager, but you are part of the wolf team. Only the detective can reveal your true "
                                          "identity. Once all other wolves die, you will turn into a wolf."],
         'sorcerer' : ['wolf', 'sorcerers', "You may use `observe <player>` in pm during the night to observe someone and determine if they "
                                            "are the seer, oracle, or augur. You are seen as a villager; only detectives can reveal your true identity."],
         'cultist' : ['wolf', 'cultists', "Your job is to help the wolves kill all of the villagers. But you do not know who the wolves are."],
         'seer' : ['village', 'seers', "Your job is to detect the wolves; you may have a vision once per night. Type `see <player>` in private message to see their role."],
         'oracle' : ['village', 'oracles', "Your job is to detect the wolves; you may have a vision once per night. Type `see <player>` in private message to see whether or not they are a wolf."],
         'shaman' : ['village', 'shamans', "You select a player to receive a totem each night by using `give <player>`. You may give a totem to yourself, but you may not give the same"
                                           " person a totem two nights in a row. If you do not give the totem to anyone, it will be given to a random player. "
                                           "To see your current totem, use the command `myrole`."],
         'harlot' : ['village', 'harlots', "You may spend the night with one player each night by using `visit <player>`. If you visit a victim of a wolf, or visit a wolf, "
                                           "you will die. You may visit yourself to stay home."],
         'hunter' : ['village', 'hunters', "Your job is to help kill the wolves. Once per game, you may kill another player using `kill <player>`. "
                                           "If you do not wish to kill anyone tonight, use `pass` instead."],
         'augur' : ['village', 'augurs', "Your job is to detect the wolves; you may have a vision once per night. Type `see <player>` in private message to see the aura they exude."
                                         " Blue is villager, grey is neutral, and red is wolf."],
         'detective' : ['village', 'detectives', "Your job is to determine all of the wolves and traitors. During the day, you may use `id <player>` in private message "
                                                 "to determine their true identity. However you risk a {}% chance of revealing your role to the wolves every time you use your ability.".format(int(DETECTIVE_REVEAL_CHANCE * 100))],
         'villager' : ['village', 'villagers', "Your job is to lynch all of the wolves."],
         'crazed shaman' : ['neutral', 'crazed shamans', "You select a player to receive a random totem each night by using `give <player>`. You may give a totem to yourself, "
                                                         "but you may not give the same person a totem two nights in a row. If you do not give the totem to anyone, "
                                                         "it will be given to a random player. You win if you are alive by the end of the game."],
         'fool' : ['neutral', 'fools', "You become the sole winner if you are lynched during the day. You cannot win otherwise."],
         'cursed villager' : ['template', 'cursed villagers', "This template is hidden and is seen as a wolf by the seer. Roles normally seen as wolf, the seer, and the fool cannot be cursed."],
         'gunner' : ['template', 'gunners', ("This template gives the player a gun. Type `{0}shoot <player>` in channel during the day to shoot <player>."
                                            "If you are a villager and shoot a wolf, they will die. Otherwise, there is a chance of killing them, injuring "
                                            "them, or the gun exploding. If you are a wolf and shoot at a wolf, you will intentionally miss.".format(BOT_PREFIX))],
         'assassin' : ['template', 'assassins', "Choose a target with `target <player>`. If you die you will take out your target with you. If your target dies you may choose another one. "
                                                "Wolves and info-obtaining roles (such as seer and oracle) may not be assassin."],
         'matchmaker' : ['village', 'matchmakers', "You can select two players to be lovers with `choose <player1> and <player2>`."
                                                   " If one lover dies, the other will as well. You may select yourself as one of the lovers."
                                                   " You may only select lovers during the first night."
                                                   " If you do not select lovers, they will be randomly selected and you will not be told who they are (unless you are one of them)."],
         'guardian angel' : ['village', 'guardian angels', "Your job is to protect the villagers. Use `guard <player>` in private message during night to protect "
                                                           "them from dying. You may protect yourself, however you may not guard the same player two nights in a row."],
         'jester' : ['neutral', 'jesters', "You will win alongside the normal winners if you are lynched during the day. You cannot otherwise win this game."],
         'minion' : ['wolf', 'minions', "It is your job to help the wolves kill all of the villagers. You are told who your leaders are on the first night, though they do not know you and you must tell them. Otherwise you have no powers, like a cultist"],
         'amnesiac' : ['neutral', 'amnesiacs', "You have forgotten your original role and need to wait a few nights to let the fog clear. You will win with the default role, until you remember your original role."],
         'blessed villager' : ['template', 'blessed villagers', "You feel incredibly safe. You won't be able to die as a normal villager, unless two players target you, or you are lynched at day."],
         'vengeful ghost' : ['neutral', 'vengeful ghosts', "Your soul will never be at rest. If you are killed during the game, you will swear eternal revenge upon team that killed you."
                                                           " Use `kill <player>` once per night after dying to kill an alive player. You only win if the team you swore revenge upon loses."],
         'priest' : ['village', 'priests', "Once per game during the day, you may bless someone with `bless <player>` to prevent them from being killed. Furthermore, you may consecrate the dead during the day with `consecrate <player>` to settle down restless spirits and prevent the corpse from rising as undead; doing so removes your ability to participate in the vote that day."],
         'doomsayer' : ['wolf', 'doomsayers', "You can see how bad luck will befall someone at night by using `see <player>` on them. You may also use `kill <player>` to kill a villager."],
         'succubus' : ['neutral', 'succubi', "You may entrance someone and make them follow you by visiting them at night. If all alive players are entranced, you win. Use `visit <player>` to visit a player or `pass` to stay home. If you visit the victim of the wolves, you will die."],
         'mayor' : ['template', 'mayors', "If the mayor would by lynched during the day, they reveal that they are the mayor and nobody is lynched that day. A mayor that has previously been revealed will be lynched as normal."],
         'monster' : ['neutral', 'monsters', "You cannot be killed by the wolves. If you survive until the end of the game, you win instead of the normal winners."],
         'sharpshooter' : ['template', 'sharpshooters', "This template is like the gunner template but due to it's holder's skills, they may never miss their target."],
         'village drunk': ['village', 'village drunks', "You have been drinking too much!"],
         'hag' : ['wolf', 'hags', "You can hex someone to prevent them from using any special powers they may have during the next day and night. Use `hex <player>` to hex them. Only detectives can reveal your true identity, seers will see you as a regular villager."],
         'bodyguard' : ['village', 'bodyguards', "It is your job to protect the villagers. If you guard a victim, you will sacrifice yourself to save them. Use `guard <player>` to guard a player or `pass` to not guard anyone tonight."],
         'piper' : ['neutral', 'pipers', "You can select up to two players to charm each night. The charmed players will know each other, but not who charmed them. You win when all other players are charmed. Use `charm <player1> and <player2>` to select the players to charm, or `charm <player>` to charm just one player."],
         'warlock' : ['wolf', 'warlocks', "Each night you can curse someone with `curse <player>` to turn them into a cursed villager, so the seer sees them as wolf. Act quickly, as your curse applies as soon as you cast it! Only detectives can reveal your true identity, seers will see you as a regular villager."],
         'mystic' : ['village', 'mystics', "Each night you will sense the number of evil villagers there are."],
         'wolf mystic' : ['wolf', 'wolf mystics', "Each night you will sense the number of villagers with a power that oppose you. You can also use `kill <player>` to kill a villager."],
         'mad scientist' : ['village', 'mad scientists', "You win with the villagers, and should you die, you will let loose a potent chemical concoction that will kill the players next to you if they are still alive."],
         'clone' : ['neutral', 'clones', "You can select someone to clone with `clone <player>`. If that player dies, you become their role. You may only clone someone during the first night."],
         'lycan' : ['neutral', 'lycans', "You are currently on the side of the villagers, but will turn into a wolf instead of dying if you are targeted by the wolves during the night."],
         'time lord' : ['village', 'time lords', "You are a master of time .. but you do not know it. If you are killed, day and night will speed up considerably."],
         'turncoat' : ['neutral', 'turncoats', "You can change the team you side with every other night. Use `side villagers` or `side wolves` to choose your team."]}

# NOTE: This was my temporary idea, I'm not entirely sure this is a good idea anymore.
# I sorta think we need a werewolf.Gamemode and then Implementers of Gamemodes.
# i.e. `from werewolf.gamemodes import default`
# Gamemodes are specifiers of the roles available?
from werewolf.gamemodes import gamemodes 
gamemodes['belunga']['roles'] = dict(gamemodes['default']['roles'])

# NOTE: Why are these roles ordered? What are the ordered by?
# It's not the alphabet, perhaps its the order in which they take their turns?
# If that's true and I create each of these roles as an object, how would I distinguish which one went first?
# Basically they'd have to be orderable by turn number. I think that's fine.
VILLAGE_ROLES_ORDERED = ['seer', 'oracle', 'shaman', 'harlot', 'hunter', 'augur', 'detective', 'matchmaker', 'guardian angel', 'bodyguard', 'priest', 'village drunk', 'mystic', 'mad scientist', 'time lord', 'villager']
WOLF_ROLES_ORDERED = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic', 'traitor', 'hag', 'sorcerer', 'warlock', 'minion', 'cultist']
NEUTRAL_ROLES_ORDERED = ['jester', 'crazed shaman', 'monster', 'piper', 'amnesiac', 'fool', 'vengeful ghost', 'succubus', 'clone', 'lycan', 'turncoat']
TEMPLATES_ORDERED = ['cursed villager', 'blessed villager', 'gunner', 'sharpshooter', 'mayor', 'assassin']
totems = {'death_totem' : 'The player who is given this totem will die tonight.',
          'protection_totem': 'The player who is given this totem is protected from dying tonight.',
          'revealing_totem': 'If the player who is given this totem is lynched, their role is revealed to everyone instead of them dying.',
          'influence_totem': 'Votes by the player who is given this totem count twice.',
          'impatience_totem' : 'The player who is given this totem is counted as voting for everyone except themselves, even if they do not lynch.',
          'pacifism_totem' : 'The player who is given this totem is always counted as abstaining, regardless of their vote.',
          'cursed_totem' : 'The player who is given this totem will gain the cursed template if they do not have it.',
          'lycanthropy_totem' : 'If the player who is given this totem is targeted by wolves the following night, they turn into a wolf instead of dying.',
          'retribution_totem' : 'If the player who is given this totem is targeted by wolves during the night, they kill a random wolf in turn.',
          'blinding_totem' : 'The player who is given this totem will be injured and unable to vote the following day.',
          'deceit_totem' : 'If the player who is given this totem is seen by the seer/oracle the following night, the '
                           'vision will return the opposite of what they are. If a seer/oracle is given this totem, '
                           'all of their visions will return the opposite.',
          'misdirection_totem' : 'If the player who is given this totem attempts to use a power the following day or night'
                                 ', they will target a player adjacent to their intended target instead of the player they targeted.',
          'luck_totem' : 'If the player who is given this totem is targeted tomorrow night, one of the players adjacent '
                         'to them will be targeted instead.',
          'silence_totem' : 'The player who is given this totem will be unable to use any special powers during the'
                            ' day tomorrow and the night after.',
          'pestilence_totem': 'If the player who is given this totem is killed by wolves tomorrow night,'
                              ' the wolves will not be able to kill the night after.',
          'desperation_totem': 'If the player who is given this totem is lynched, the last player to vote '
                               'them will also die.'}
SHAMAN_TOTEMS = ['death_totem', 'protection_totem', 'revealing_totem', 'influence_totem', 'impatience_totem', 'pacifism_totem', 'silence_totem', 'desperation_totem']
WOLF_SHAMAN_TOTEMS = ['protection_totem', 'impatience_totem', 'pacifism_totem', 'deceit_totem', 'lycanthropy_totem', 'luck_totem', 'misdirection_totem', 'silence_totem']
ROLES_SEEN_VILLAGER = ['werekitten', 'traitor', 'sorcerer', 'warlock', 'minion', 'cultist', 'villager', 'jester', 'fool', 'amnesiac', 'vengeful ghost', 'hag', 'piper', 'clone', 'lycan', 'time lord', 'turncoat']
ROLES_SEEN_WOLF = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'wolf shaman', 'wolf mystic', 'cursed', 'monster', 'succubus', 'mad scientist']
ACTUAL_WOLVES = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic']
WOLFCHAT_ROLES = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic', 'traitor', 'sorcerer', 'warlock', 'hag']

########### END POST-DECLARATION STUFF #############

# NOTE: I really dont understand what's going on here.
# We loop the rate limit? - Isn't rate limiting built into discord.py
# We loop the backup_settings - Shouldn't we backup settings when we set them?
# Then we run until complete the client.start(TOKEN) or in other words the bot.
# And finally once that's done, we try to do some kind of insane cleanup mechanism.
# TODO: Compare this to the startup system I have written for other discord bots and simplify it.
def main():
    client.loop.create_task(do_rate_limit_loop())
    client.loop.create_task(backup_settings_loop())
    try:
        client.loop.run_until_complete(client.start(TOKEN))
    finally:
        try:
            try:
                client.loop.run_until_complete(client.logout())
            except:
                pass
            pending = asyncio.Task.all_tasks()
            gathered = asyncio.gather(*pending)

            try:
                gathered.cancel()
                client.loop.run_until_complete(gathered)
                gathered.exception()
            except:
                pass
        except:
            print("Error in cleanup:\n" + traceback.format_exc())
        client.loop.close()

if __name__ == "__main__":
    main()