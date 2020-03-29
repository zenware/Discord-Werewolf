"""
This cog integrates the werewolf game engine /w the Discord.py bot functionality.
"""
import discord
from discord.ext import commands
from werewolf.game import WerewolfGameEngine

# TODO: Basically I'm extracting each of these commands into a GameEngine Class.
class Werewolf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # NOTE: Spawn a new game engine
        # Should I also start the random seed here?
        self.game_engine = WerewolfGameEngine()
        # TODO: Should I build in these links or provide configuration options for them?
        self.thumb = None
        self.author_thumb = None

    @commands.command('myrole', [0, 0], "```\n{0}myrole takes no arguments\n\nTells you your role in pm.```")
    async def cmd_myrole(self, ctx, message, parameters):
        await _send_role_info(message.author.id)


    @commands.command('stats', [0, 0], "```\n{0}stats takes no arguments\n\nLists current players in the lobby during the join phase, and lists game information in-game.```")
    async def cmd_stats(self, ctx, message, parameters):
        """Provide stats on the game before and after starting.

        Before starting this should provide a list of the players waiting.
        After the game is running this should provide game information.
        """
        await client.send_message(message.channel, self.game_engine.pretty_game_stats())
        if session[0]:
            reply_msg = "It is now **" + ("day" if session[2] else "night") + "time**. Using the **{}** gamemode.".format(
                'roles' if session[6].startswith('roles') else session[6])
            reply_msg += "\n**" + str(len(session[1])) + "** players playing: **" + str(len([x for x in session[1] if session[1][x][0]])) + "** alive, "
            reply_msg += "**" + str(len([x for x in session[1] if not session[1][x][0]])) + "** dead\n"
            reply_msg += "```basic\nLiving players:\n" + "\n".join(get_name(x) + ' (' + x + ')' for x in session[1] if session[1][x][0]) + '\n'
            reply_msg += "Dead players:\n" + "\n".join(get_name(x) + ' (' + x + ')' for x in session[1] if not session[1][x][0]) + '\n'

            if session[6] in ('random',):
                reply_msg += '\n!stats is disabled for the {} gamemode.```'.format(session[6])
                await reply(message, reply_msg)
                return
            orig_roles = dict(session[7])
            # make a copy
            role_dict = {}
            traitorvill = 0
            traitor_turned = False
            for other in [session[1][x][4] for x in session[1]]:
                if 'traitor' in other:
                    traitor_turned = True
                    break
            for role in roles: # Fixes !stats crashing with !frole of roles not in game
                role_dict[role] = [0, 0]
                # [min, max] for traitor and similar roles
            for player in session[1]:
                # Get maximum numbers for all roles
                role_dict[get_role(player, 'role') if not [x for x in session[1][player][4] if x.startswith('turned:')] else [x for x in session[1][player][4] if x.startswith('turned:')].pop().split(':')[1]][0] += 1
                role_dict[get_role(player, 'role') if not [x for x in session[1][player][4] if x.startswith('turned:')] else [x for x in session[1][player][4] if x.startswith('turned:')].pop().split(':')[1]][1] += 1
                if get_role(player, 'role') in ['villager', 'traitor'] or 'turned:villager' in session[1][player][4]:
                    traitorvill += 1
                    

            #reply_msg += "Total roles: " + ", ".join(sorted([x + ": " + str(roles[x][3][len(session[1]) - MIN_PLAYERS]) for x in roles if roles[x][3][len(session[1]) - MIN_PLAYERS] > 0])).rstrip(", ") + '\n'
            # ^ saved this beast for posterity

            reply_msg += "Total roles: "
            total_roles = dict(orig_roles)
            reply_msg += ', '.join("{}: {}".format(x, total_roles[x]) for x in sort_roles(total_roles))
            
            if session[6] == 'noreveal':
                reply_msg += "```"
                await reply(message, reply_msg)
                return

            for role in list(role_dict):
                # list is used to make a copy
                if role in TEMPLATES_ORDERED:
                    del role_dict[role]

            if traitor_turned:
                role_dict['wolf'][0] += role_dict['traitor'][0]
                role_dict['wolf'][1] += role_dict['traitor'][1]
                role_dict['traitor'] = [0, 0]

            for player in session[1]:
                role = get_role(player, 'role')
                # Subtract dead players
                if not session[1][player][0]:
                    reveal = get_role(player, 'deathstats')

                    if role == 'traitor' and traitor_turned:
                        # player died as traitor but traitor turn message played, so subtract from wolves
                        reveal = 'wolf'

                    if reveal == 'villager':
                        traitorvill -= 1
                        # could be traitor or villager
                        if 'traitor' in role_dict:
                            role_dict['traitor'][0] = max(0, role_dict['traitor'][0] - 1)
                            if role_dict['traitor'][1] > traitorvill:
                                role_dict['traitor'][1] = traitorvill

                        role_dict['villager'][0] = max(0, role_dict['villager'][0] - 1)
                        if role_dict['villager'][1] > traitorvill:
                            role_dict['villager'][1] = traitorvill
                    else:
                        # player died is definitely that role
                        role_dict[reveal][0] = max(0, role_dict[reveal][0] - 1)
                        role_dict[reveal][1] = max(0, role_dict[reveal][1] - 1)
                
            for clone in session[1]:
                if [x for x in session[1][clone][4] if x.startswith('clone:')]:
                    role = get_role(clone, 'role')
                    if (not session[1][clone][0] and role != 'clone' and orig_roles[role] > 1 and role_dict[role] != 0) or (session[1][clone][0] and role != 'clone'):
                        #first part - if the clone's dead but whether or not the corpse is them or a real their role, call them alive
                        #and the second part is if they are alive and have cloned, call them a clone instead
                        role_dict['clone'][0] += 1
                        role_dict['clone'][1] += 1
                        if role != 'traitor':
                            role_dict[role][0] -= 1
                            role_dict[role][1] -= 1
            
            #amnesiacs show amnesiac even after turning
            for player in session[1]:
                role = get_role(player, 'role')
                if session[1][player][0] and "amnesiac" in session[1][player][4]:
                    role_dict["amnesiac"][0] += 1
                    role_dict["amnesiac"][1] += 1
                    role_dict[role][0] -= 1
                    role_dict[role][1] -= 1

            reply_msg += "\nCurrent roles: "
            for template in TEMPLATES_ORDERED:
                if template in orig_roles:
                    del orig_roles[template]
            print(role_dict)
            for role in sort_roles(list(set(roles) - set(TEMPLATES_ORDERED))):
                if role in orig_roles or role_dict[role][0]:
                    if role_dict[role][0] == role_dict[role][1]:
                        if role_dict[role][0] == 1:
                            reply_msg += role
                        else:
                            reply_msg += roles[role][1]
                        reply_msg += ": " + str(role_dict[role][0])
                    else:
                        reply_msg += roles[role][1] + ": {}-{}".format(role_dict[role][0], role_dict[role][1])
                    reply_msg += ", "
            reply_msg = reply_msg.rstrip(", ") + "```"
            await reply(message, reply_msg)
        # TODO: MAKE IT TO HERE.

    @commands.command('revealroles', [1, 1], "```\n{0}revealroles takes no arguments\n\nDisplays what each user's roles are and sends it in pm.```", 'rr')
    async def cmd_revealroles(self, ctx, message, parameters):
        msg = ["**Gamemode**: {}```diff".format(session[6])]
        for player in session[1]:
            msg.append("{} {} ({}): {}; action: {}; other: {}".format(
                '+' if session[1][player][0] else '-', get_name(player), player, get_role(player, 'actual'),
                session[1][player][2], ' '.join(session[1][player][4])))
        msg.append("```")
        await client.send_message(message.channel, '\n'.join(msg))
        await log(2, "{0} ({1}) REVEALROLES".format(message.author.name, message.author.id))


    @commands.command('see', [2, 0], "```\n{0}see <player>\n\nIf you are a seer, uses your power to detect <player>'s role. If you are a doomsayer, dooms <player> with either sickness, lycanthropy or death.```")
    async def cmd_see(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or not session[1][message.author.id][0]:
            return
        role = get_role(message.author.id, 'role')
        if role not in COMMANDS_FOR_ROLE['see']:
            return
        if session[2]:
            await reply(message, "You may only see during the night.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        if (session[1][message.author.id][2] and role != 'doomsayer') or (role == 'doomsayer' and not [x for x in session[1][message.author.id][4] if x.startswith('doom:')]):
            await reply(message, "You have already used your power.")
            return
        else:
            if parameters == "":
                await reply(message, roles[role][2])
            else:
                player = get_player(parameters)
                if player:
                    if role != 'doomsayer':
                        if player == message.author.id:
                            await reply(message, "Using your power on yourself would be a waste.")
                        elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                            await reply(message, "You may not see a succubus.")
                        elif not session[1][player][0]:
                            await reply(message, "Player **" + get_name(player) + "** is dead!")
                        else:
                            session[1][message.author.id][2] = player
                            if 'misdirection_totem2' in session[1][message.author.id][4]:
                                player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                            elif 'luck_totem2' in session[1][player][4]:
                                player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                            if role == 'seer':
                                seen_role = get_role(player, 'seen')
                                if (session[1][player][4].count('deceit_totem2') +\
                                    session[1][message.author.id][4].count('deceit_totem2')) % 2 == 1:
                                    if seen_role == 'wolf':
                                        seen_role = 'villager'
                                    else:
                                        seen_role = 'wolf'
                                reply_msg = "is a **{}**".format(seen_role)
                            elif role == 'oracle':
                                seen_role = get_role(player, 'seenoracle')
                                if (session[1][player][4].count('deceit_totem2') +\
                                    session[1][message.author.id][4].count('deceit_totem2')) % 2 == 1:
                                    # getting team will return either village or wolf team
                                    if seen_role == 'wolf':
                                        seen_role = 'villager'
                                    else:
                                        seen_role = 'wolf'
                                reply_msg = "is {}a **wolf**".format('**not** ' if seen_role == 'villager' else '')
                            elif role == 'augur':
                                seen_role = get_role(player, 'actualteam')
                                if get_role(player, 'role') == 'amnesiac':
                                    seen_role = roles[[x.split(':')[1].replace("_", " ") for x in session[1][player][4] if x.startswith("role:")].pop()][1]
                                reply_msg = "exudes a **{}** aura".format(
                                    'red' if seen_role == 'wolf' else 'blue' if seen_role == 'village' else 'grey')
                            await reply(message, "You have a vision... in your vision you see that **{}** {}!".format(
                                get_name(player), reply_msg))
                            await log(1, "{0} ({1}) SEE {2} ({3}) AS {4}".format(get_name(message.author.id), message.author.id, get_name(player), player, seen_role))
                    else:
                        if player == message.author.id:
                            await reply(message, "Seeing yourself would be a waste.")
                            return
                        elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                            await reply(message, "You may not see a succubus.")
                            return
                        elif not session[1][player][0]:
                            await reply(message, "Player **" + get_name(player) + "** is dead!")
                            return
                        elif get_role(player, 'role') in WOLFCHAT_ROLES:
                            await reply(message, "Seeing another wolf would be a waste.")
                            return
                        else:
                            if 'misdirection_totem2' in session[1][message.author.id][4]:
                                player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                            elif 'luck_totem2' in session[1][player][4]:
                                player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        doom = 'lycan'
                        if [x for x in session[1][message.author.id][4] if x.startswith('doom:')]:
                            doom = [x.split(':')[1] for x in session[1][message.author.id][4] if x.startswith('doom:')].pop()
                        if doom == 'lycan':
                            await reply(message, "You have a vision that **{0}** is transforming into a savage beast tomorrow night.".format(get_name(player)))
                            session[1][player][4].append('lycanthropy')
                        elif doom == 'death':
                            await reply(message, "You have a vision that **{0}** will meet an untimely end tonight.".format(get_name(player)))
                            session[1][message.author.id][4].append('doomdeath:{}'.format(player))
                        elif doom == 'sick':
                            await reply(message, "You have a vision that **{0}** will become incredibly ill tomorrow and unable to do anything.".format(get_name(player)))
                            session[1][player][4].append('sick')
                        try:
                            session[1][message.author.id][4].remove('doom:{}'.format(doom))
                        except ValueError as e:
                            await log(2, "```py\n{}\n```".format(traceback.format_exc()))
                        await log(1, "{} ({}) {} DOOM {} ({})".format(get_name(message.author.id), message.author.id, doom,
                            get_name(player), player))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('bless', [2, 0], "```\n{0}bless <player>\n\nIf you are a priest, gives a blessing to <player>```")
    async def cmd_bless(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or not session[1][message.author.id][0]:
            return
        role = get_role(message.author.id, 'role')
        if role not in COMMANDS_FOR_ROLE['bless']:
            return
        if not session[2]:
            await reply(message, "You may only bless during the day.")
            return
        if 'bless' not in session[1][message.author.id][4]:
            await reply(message, "You have already blessed someone this game.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[role][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "You may not bless yourself.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        session[1][message.author.id][4].remove('bless')
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        await reply(message, "You have given a blessing to **{0}**.".format(get_name(player)))
                        session[1][player][3].append('blessed')
                        member = client.get_server(WEREWOLF_SERVER).get_member(player)
                        if member:
                            try:
                                await client.send_message(member, "You suddenly feel very safe.")
                            except discord.Forbidden:
                                pass
                        await log(1, "{} ({}) BLESS {} ({})".format(get_name(message.author.id), message.author.id,
                            get_name(player), player))


    @commands.command('consecrate', [2, 0], "```\n{0}consecrate <player>\n\nIf you are a priest, prevents <player> if they are a vengeful ghost from killing the following night, doing so removes your ability to participate in the vote that day```")
    async def cmd_consecrate(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or not session[1][message.author.id][0]:
            return
        role = get_role(message.author.id, 'role')
        if role not in COMMANDS_FOR_ROLE['consecrate']:
            return
        if not session[2]:
            return
        if 'consecrated' in session[1][message.author.id][4]:
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[role][2])
            else:
                player = get_player(parameters)
                if player:
                    if session[1][player][0]:
                        await reply(message, "**{0}** is not dead.".format(get_name(player)))
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if not session[1][x][0]])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if not session[1][x][0]])
                        await reply(message, "You have consecrated the body of **{0}**.".format(get_name(player)))
                        session[1][player][4].append('consecrated')
                        session[1][message.author.id][4].append('consecrated')
                        session[1][message.author.id][4].append('injured')
                        session[1][message.author.id][2] = ''
                        await log(1, "{} ({}) CONSECRATE {} ({})".format(get_name(message.author.id), message.author.id,
                            get_name(player), player))


    @commands.command('hex', [2, 0], "```\n{0}hex <player>\n\nIf you are a hag, hexes <player>```")
    async def cmd_hex(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or not session[1][message.author.id][0]:
            return
        if get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['hex']:
            return
        if session[2]:
            return
        if session[1][message.author.id][2]:
            await reply(message, "You have already hexed someone tonight.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[role][2])
            else:
                player = get_player(parameters)
                if player:
                    if not session[1][player][0]:
                        await reply(message, "**{0}** is dead.".format(get_name(player)))
                    elif 'lasttarget:{}'.format(player) in session[1][message.author.id][4]:
                        await reply(message, "You hexed **{0}** last night. You cannot hex the same person two nights in a row.".format(get_name(player)))
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not hex a succubus.")
                    elif get_role(player, 'role') in WOLFCHAT_ROLES:
                        await reply(message, "Hexing a wolf would be a waste.")
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        await reply(message, "You have cast a hex on **{0}**.".format(get_name(player)))
                        await wolfchat("**{0}** has cast a hex on **{1}**.".format(get_name(message.author.id), get_name(player)))
                        session[1][message.author.id][2] = player
                        session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if not x.startswith('lasttarget:')] + ['lasttarget:{}'.format(player)]
                        await log(1, "{} ({}) HEX {} ({})".format(get_name(message.author.id), message.author.id,
                            get_name(player), player))


    @commands.command('choose', [2, 0], "```\n{0}choose <player1> and <player2>\n\nIf you are a matchmaker, Selects two players to fall in love. You may select yourself as one of the lovers.```", 'match')
    async def cmd_choose(self, ctx, message, parameters):
        if not session[0] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['choose'] or not session[1][message.author.id][0] or not message.channel.is_private:
            return
        if parameters == "":
            await reply(message, roles[session[1][message.author.id][1]][2].format(BOT_PREFIX))
        else:
            if get_role(message.author.id, 'role') == 'matchmaker':
                if 'match' not in session[1][message.author.id][4]:
                    await reply(message, "You have already chosen lovers.")
                    return
                targets = parameters.split(' and ')
                if len(targets) == 2:
                    actual_targets = []
                    for target in targets:
                        player = get_player(target)
                        if not player:
                            await reply(message, "Could not find player " + target)
                            return
                        actual_targets.append(player)
                    actual_targets = set(actual_targets)
                    valid_targets = []
                    if len(actual_targets) != 2:
                        await reply(message, "You may only choose **2** unique players to match.")
                        return
                    for player in actual_targets:
                        if not session[1][player][0]:
                            await reply(message, "Player **" + get_name(player) + "** is dead!")
                            return
                        else:
                            valid_targets.append(player)
                    redirected_targets = []
                    for player in valid_targets:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            new_target = misdirect(message.author.id)
                            while new_target in redirected_targets:
                                new_target = misdirect(message.author.id)
                            redirected_targets.append(new_target)
                        elif 'luck_totem2' in session[1][player][4]:
                            new_target = misdirect(player)
                            while new_target in redirected_targets:
                                new_target = misdirect(message.author.id)
                            redirected_targets.append(new_target)
                        else:
                            redirected_targets.append(player)
                    await reply(message, "You have selected **{}** and **{}** to be lovers.".format(*map(get_name, redirected_targets)))
                    session[1][message.author.id][4].remove('match')
                    player1 = redirected_targets[0]
                    player2 = redirected_targets[1]
                    if "lover:" + player2 not in session[1][player1][4]:
                        session[1][player1][4].append("lover:" + player2)
                    if "lover:" + player1 not in session[1][player2][4]:
                        session[1][player2][4].append("lover:" + player1)
                    await log(1, "{} ({}) CHOOSE {} ({}) AND {} ({})".format(get_name(message.author.id), message.author.id,
                        get_name(player1), player1, get_name(player2), player2))
                    love_msg = "You are in love with **{}**. If that player dies for any reason, the pain will be too much for you to bear and you will commit suicide."
                    member1 = client.get_server(WEREWOLF_SERVER).get_member(player1)
                    member2 = client.get_server(WEREWOLF_SERVER).get_member(player2)
                    if member1:
                        try:
                            await client.send_message(member1, love_msg.format(get_name(player2)))
                        except discord.Forbidden:
                            pass
                    if member2:
                        try:
                            await client.send_message(member2, love_msg.format(get_name(player1)))
                        except discord.Forbidden:
                            pass
                else:
                    await reply(message, "You must choose two different players.")


    @commands.command('kill', [2, 0], "```\n{0}kill <player>\n\nIf you are a wolf, casts your vote to target <player>. If you are a "
                        "hunter or a vengeful ghost, <player> will die the following night.```")
    async def cmd_kill(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['kill']:
            return
        if get_role(message.author.id, 'role') == "vengeful ghost":
            if session[1][message.author.id][0] or not [x for x in session[1][message.author.id][4] if x.startswith("vengeance:")]:
                return
        if session[2]:
            await reply(message, "You may only kill someone during the night.")
            return
        if parameters == "":
            await reply(message, roles[session[1][message.author.id][1]][2])
        else:
            if get_role(message.author.id, 'role') == 'hunter':
                if 'hunterbullet' not in session[1][message.author.id][4]:
                    await reply(message, "You have already killed someone this game.")
                    return
                elif session[1][message.author.id][2]:
                    if session[1][message.author.id][2] == message.author.id:
                        await reply(message, "You have already chosen to not kill tonight".format(get_name(session[1][message.author.id][2])))
                    else:
                        await reply(message, "You have already chosen to kill **{}**.".format(get_name(session[1][message.author.id][2])))
                    return
                if "silence_totem2" in session[1][message.author.id][4]:
                    await reply(message, "You have been silenced, and are unable to use any special powers.")
                    return
                player = get_player(parameters)
                if 'misdirection_totem2' in session[1][message.author.id][4]:
                    player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                elif 'luck_totem2' in session[1][player][4]:
                    player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                if player:
                    if player == message.author.id:
                        await reply(message, "Suicide is bad for you.")
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not kill a succubus.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        session[1][message.author.id][2] = player
                        await reply(message, "You have chosen to kill **" + get_name(player) + "** tonight.")
                        await log(1, "{0} ({1}) HUNTERKILL {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                else:
                    await reply(message, "Could not find player " + parameters)
            elif roles[get_role(message.author.id, 'role')][0] == 'wolf':
                num_kills = session[1][message.author.id][4].count('angry') + 1
                targets = parameters.split(' and ')
                actual_targets = []
                for target in targets:
                    player = get_player(target)
                    if not player:
                        await reply(message, "Could not find player " + target)
                        return
                    actual_targets.append(player)
                actual_targets = set(actual_targets)
                valid_targets = []
                if len(actual_targets) > num_kills:
                    await reply(message, "You may only kill **{}** targets.".format(num_kills))
                    return
                for player in actual_targets:
                    if player == message.author.id:
                        await reply(message, "Suicide is bad for you.")
                        return
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not kill a succubus.")
                        return
                    elif get_role(message.author.id, 'actualteam') == 'wolf' and \
                    get_role(player, 'actualteam') == 'wolf' and get_role(player, 'role') not in ['minion', 'cultist']:
                        await reply(message, "You can't kill another wolf.")
                        return
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                        return
                    else:
                        if "silence_totem2" in session[1][message.author.id][4]:
                            await reply(message, "You have been silenced, and are unable to use any special powers.")
                            return
                        elif "ill_wolf" in session[1][message.author.id][4]:
                            await reply(message, "You are feeling ill tonight, and are unable to kill anyone.")
                            return
                        valid_targets.append(player)
                redirected_targets = []
                for player in valid_targets:
                    if 'misdirection_totem2' in session[1][message.author.id][4]:
                        new_target = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, "role") not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        while new_target in redirected_targets:
                            new_target = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, "role") not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        redirected_targets.append(new_target)
                    elif 'luck_totem2' in session[1][player][4]:
                        new_target = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, "role") not in WOLFCHAT_ROLES])
                        while new_target in redirected_targets:
                            new_target = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, "role") not in WOLFCHAT_ROLES])
                        redirected_targets.append(new_target)
                    else:
                        redirected_targets.append(player)
                session[1][message.author.id][2] = ','.join(redirected_targets)
                await reply(message, "You have voted to kill **{}**.".format('** and **'.join(
                    map(get_name, valid_targets))))
                await wolfchat("**{}** has voted to kill **{}**.".format(get_name(message.author.id), '** and **'.join(
                    map(get_name, valid_targets))))
                await log(1, "{0} ({1}) KILL {2} ({3})".format(get_name(message.author.id), message.author.id,
                ' and '.join(map(get_name, valid_targets)), ','.join(valid_targets)))
            elif get_role(message.author.id, 'role') == 'vengeful ghost' and 'consecrated' not in session[1][message.author.id][4] and 'driven' not in session[1][message.author.id][4]:
                if session[1][message.author.id][2] != '':
                    await reply(message, "You have already chosen to kill **{}**.".format(get_name(session[1][message.author.id][2])))
                    return
                player = get_player(parameters)
                against = 'wolf'
                if [x for x in session[1][message.author.id][4] if x.startswith("vengeance:")]:
                    against = [x.split(":")[1] for x in session[1][message.author.id][4] if x.startswith("vengeance:")].pop()
                if player:
                    if player == message.author.id:
                        return
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    elif get_role(player, 'actualteam') != against:
                        await reply(message, "You must target a {}.".format('villager' if against == 'village' else 'wolf'))
                    else:
                        session[1][message.author.id][2] = player
                        await reply(message, "You have chosen to kill **" + get_name(player) + "** tonight.")
                        await log(1, "{0} ({1}) VENGEFUL KILL {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))


    @commands.command('vote', [0, 0], "```\n{0}vote [<gamemode | player>]\n\nVotes for <gamemode> during the join phase or votes to lynch <player> during the day. If no arguments "
                        "are given, replies with a list of current votes.```", 'v')
    async def cmd_vote(self, ctx, message, parameters):
        if session[0]:
            await cmd_lynch(message, parameters)
        else:
            if message.channel.is_private:
                await reply(message, "Please use vote in channel.")
                return
            if parameters == "":
                await cmd_votes(message, parameters)
            else:
                if session[6]:
                    await reply(message, "An admin has already set a gamemode.")
                    return
                if message.author.id in session[1]:
                    choice, num = _autocomplete(parameters, gamemodes)
                    if num == 0:
                        await reply(message, "Could not find gamemode {}".format(parameters))
                    elif num == 1:
                        session[1][message.author.id][2] = choice
                        await reply(message, "You have voted for the **{}** gamemode.".format(choice))
                    else:
                        await reply(message, "Multiple options: {}".format(', '.join(sorted(choice))))
                else:
                    await reply(message, "You cannot vote for a gamemode if you are not playing!")


    @commands.command('lynch', [0, 0], "```\n{0}lynch [<player>]\n\nVotes to lynch [<player>] during the day. If no arguments are given, replies with a list of current votes.```")
    async def cmd_lynch(self, ctx, message, parameters):
        if not session[0] or not session[2]:
            return
        if parameters == "":
            await cmd_votes(message, parameters)
        else:
            if message.author.id not in session[1]:
                return
            if message.channel.is_private:
                await reply(message, "Please use lynch in channel.")
                return
            if 'illness' in session[1][message.author.id][4]:
                try:
                    await client.send_message(message.author, "You are staying home due to your illness and cannot participate in the vote.")
                except discord.Forbidden:
                    pass
                return
            if 'injured' in session[1][message.author.id][4]:
                await reply(message, "You are injured and unable to vote.")
                return
            to_lynch = get_player(parameters.split(' ')[0])
            if not to_lynch:
                to_lynch = get_player(parameters)
            if to_lynch:
                if not session[1][to_lynch][0]:
                    await reply(message, "Player **" + get_name(to_lynch) + "** is dead!")
                else:
                    session[1][message.author.id][2] = to_lynch
                    await reply(message, "You have voted to lynch **" + get_name(to_lynch) + "**.")
                    vote_list = list(chain.from_iterable([[int(i.split(':')[1]) for i in session[1][x][4] if i.startswith("vote:")] for x in session[1]]))
                    if len(vote_list) == 0:
                        session[1][message.author.id][4].append("vote:1")
                    else:
                        session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if not x.startswith('vote:')]
                        session[1][message.author.id][4].append("vote:{}".format(max(vote_list) + 1))
                    await log(1, "{0} ({1}) LYNCH {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(to_lynch), to_lynch))
            else:
                await reply(message, "Could not find player " + parameters)


    @commands.command('votes', [0, 0], "```\n{0}votes takes no arguments\n\nDisplays votes for gamemodes during the join phase or current votes to lynch during the day.```")
    async def cmd_votes(self, ctx, message, parameters):
        if not session[0]:
            vote_dict = {'start' : []}
            for player in session[1]:
                if session[1][player][2] in vote_dict:
                    vote_dict[session[1][player][2]].append(player)
                elif session[1][player][2] != '':
                    vote_dict[session[1][player][2]] = [player]
                if session[1][player][1] == 'start':
                    vote_dict['start'].append(player)
            reply_msg = "**{}** player{} in the lobby, **{}** vote{} required to choose a gamemode, **{}** votes needed to start.```\n".format(
                len(session[1]), '' if len(session[1]) == 1 else 's', len(session[1]) // 2 + 1, '' if len(session[1]) // 2 + 1 == 1 else 's',
                max(2, min(len(session[1]) // 4 + 1, 4)))
            for gamemode in vote_dict:
                if gamemode == 'start':
                    continue
                reply_msg += "{} ({} vote{}): {}\n".format(gamemode, len(vote_dict[gamemode]), '' if len(vote_dict[gamemode]) == 1 else 's',
                                                        ', '.join(map(get_name, vote_dict[gamemode])))
            reply_msg += "{} vote{} to start: {}\n```".format(len(vote_dict['start']), '' if len(vote_dict['start']) == 1 else 's',
                                                        ', '.join(map(get_name, vote_dict['start'])))
            await reply(message, reply_msg)
        elif session[0] and session[2]:
            vote_dict = {'abstain': []}
            alive_players = [x for x in session[1] if session[1][x][0]]
            able_voters = [x for x in alive_players if 'injured' not in session[1][x][4]]
            for player in able_voters:
                if session[1][player][2] in vote_dict:
                    vote_dict[session[1][player][2]].append(player)
                elif session[1][player][2] != '':
                    vote_dict[session[1][player][2]] = [player]
            abstainers = vote_dict['abstain']
            reply_msg = "**{}** living players, **{}** votes required to lynch, **{}** players available to vote, **{}** player{} refrained from voting.\n".format(
                len(alive_players), len(able_voters) // 2 + 1, len(able_voters), len(abstainers), '' if len(abstainers) == 1 else 's')

            if len(vote_dict) == 1 and vote_dict['abstain'] == []:
                reply_msg += "No one has cast a vote yet. Do `{}lynch <player>` in #{} to lynch <player>. ".format(BOT_PREFIX, client.get_channel(GAME_CHANNEL).name)
            else:
                reply_msg += "Current votes: ```\n"
                for voted in [x for x in vote_dict if x != 'abstain']:
                    reply_msg += "{} ({}) ({} vote{}): {}\n".format(
                        get_name(voted), voted, len(vote_dict[voted]), '' if len(vote_dict[voted]) == 1 else 's', ', '.join(['{} ({})'.format(get_name(x), x) for x in vote_dict[voted]]))
                reply_msg += "{} vote{} to abstain: {}\n".format(
                    len(vote_dict['abstain']), '' if len(vote_dict['abstain']) == 1 else 's', ', '.join(['{} ({})'.format(get_name(x), x) for x in vote_dict['abstain']]))
                reply_msg += "```"
            await reply(message, reply_msg)


    @commands.command('retract', [0, 0], "```\n{0}retract takes no arguments\n\nRetracts your gamemode and vote to start during the join phase, "
                            "or retracts your vote to lynch or kill during the game.```", 'r')
    async def cmd_retract(self, ctx, message, parameters):
        if message.author.id not in session[1]:
            # not playing
            return
        if not session[0] and session[1][message.author.id][2] == '' and session[1][message.author.id][1] == '':
            # no vote to start nor vote for gamemode
            return
        if session[0] and session[1][message.author.id][2] == '':
            # no target
            return
        if not session[0]:
            if message.channel.is_private:
                await reply(message, "Please use retract in channel.")
                return
            session[1][message.author.id][2] = ''
            session[1][message.author.id][1] = ''
            await reply(message, "You retracted your vote.")
            session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if not x.startswith("vote:")]
        elif session[0] and session[1][message.author.id][0]:
            if session[2]:
                if message.channel.is_private:
                    await reply(message, "Please use retract in channel.")
                    return
                session[1][message.author.id][2] = ''
                await reply(message, "You retracted your vote.")
                await log(1, "{0} ({1}) RETRACT VOTE".format(get_name(message.author.id), message.author.id))
            else:
                if session[1][message.author.id][1] in COMMANDS_FOR_ROLE['kill']:
                    if session[1][message.author.id][1] == ('hunter' or 'vengeful ghost'):
                        return
                    if not message.channel.is_private:
                        try:
                            await client.send_message(message.author, "Please use retract in pm.")
                        except discord.Forbidden:
                            pass
                        return
                    session[1][message.author.id][2] = ''
                    await reply(message, "You retracted your kill.")
                    await wolfchat("**{}** has retracted their kill.".format(get_name(message.author.id)))
                    await log(1, "{0} ({1}) RETRACT KILL".format(get_name(message.author.id), message.author.id))


    @commands.command('abstain', [0, 2], "```\n{0}abstain takes no arguments\n\nRefrain from voting someone today.```", 'abs', 'nl')
    async def cmd_abstain(self, ctx, message, parameters):
        if not session[0] or not session[2] or not message.author.id in session[1] or not session[1][message.author.id][0]:
            return
        if session[6] == 'evilvillage':
            await send_lobby("The evilvillage cannot abstain.")
            return
        if session[4][1] == timedelta(0):
            await send_lobby("The village may not abstain on the first day.")
            return
        if 'injured' in session[1][message.author.id][4]:
            await reply(message, "You are injured and unable to vote.")
            return
        session[1][message.author.id][2] = 'abstain'
        await log(1, "{0} ({1}) ABSTAIN".format(get_name(message.author.id), message.author.id))
        await send_lobby("**{}** votes to not lynch anyone today.".format(get_name(message.author.id)))


    @commands.command('coin', [0, 0], "```\n{0}coin takes no arguments\n\nFlips a coin. Don't use this for decision-making, especially not for life or death situations.```")
    async def cmd_coin(self, ctx, message, parameters):
        value = random.randint(1,100)
        reply_msg = ''
        if value == 1:
            reply_msg = 'its side'
        elif value == 100:
            reply_msg = client.user.name
        elif value < 50:
            reply_msg = 'heads'
        else:
            reply_msg = 'tails'
        await reply(message, 'The coin landed on **' + reply_msg + '**!')


    @commands.command('admins', [0, 0], "```\n{0}admins takes no arguments\n\nLists online/idle admins if used in pm, and **alerts** online/idle admins if used in channel (**USE ONLY WHEN NEEDED**).```")
    async def cmd_admins(self, ctx, message, parameters):
        await reply(message, 'Available admins: ' + ', '.join('<@{}>'.format(x) for x in ADMINS if is_online(x)), cleanmessage=False)


    @commands.command('fday', [1, 2], "```\n{0}fday takes no arguments\n\nForces night to end.```")
    async def cmd_fday(self, ctx, message, parameters):
        if session[0] and not session[2]:
            session[2] = True
            await reply(message, ":thumbsup:")
            await log(2, "{0} ({1}) FDAY".format(message.author.name, message.author.id))


    @commands.command('fnight', [1, 2], "```\n{0}fnight takes no arguments\n\nForces day to end.```")
    async def cmd_fnight(self, ctx, message, parameters):
        if session[0] and session[2]:
            session[2] = False
            await reply(message, ":thumbsup:")
            await log(2, "{0} ({1}) FNIGHT".format(message.author.name, message.author.id))


    @commands.command('frole', [1, 2], "```\n{0}frole <player> <role>\n\nSets <player>'s role to <role>.```")
    async def cmd_frole(self, ctx, message, parameters):
        if parameters == '':
            return
        player = parameters.split(' ')[0]
        role = parameters.split(' ', 1)[1]
        temp_player = get_player(player)
        if temp_player:
            if session[0]:
                if role in roles or role in ['cursed']:
                    if role not in ['cursed'] + TEMPLATES_ORDERED:
                        session[1][temp_player][1] = role
                    if role == 'cursed villager':
                        session[1][temp_player][1] = 'villager'
                        for i in range(session[1][temp_player][3].count('cursed')):
                            session[1][temp_player][3].remove('cursed')
                        session[1][temp_player][3].append('cursed')
                    elif role == 'cursed':
                        for i in range(session[1][temp_player][3].count('cursed')):
                            session[1][temp_player][3].remove('cursed')
                        session[1][temp_player][3].append('cursed')
                    elif role in TEMPLATES_ORDERED:
                        for i in range(session[1][temp_player][3].count(role)):
                            session[1][temp_player][3].remove(role)
                        session[1][temp_player][3].append(role)
                    await reply(message, "Successfully set **{}**'s role to **{}**.".format(get_name(temp_player), role))
                else:
                    await reply(message, "Cannot find role named **" + role + "**")
            else:
                session[1][temp_player][1] = role
        else:
            await reply(message, "Cannot find player named **" + player + "**")
        await log(2, "{0} ({1}) FROLE {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('force', [1, 2], "```\n{0}force <player> <target>\n\nSets <player>'s target flag (session[1][player][2]) to <target>.```")
    async def cmd_force(self, ctx, message, parameters):
        if parameters == '':
            await reply(message, commands['force'][2].format(BOT_PREFIX))
            return
        player = parameters.split(' ')[0]
        target = ' '.join(parameters.split(' ')[1:])
        temp_player = get_player(player)
        if temp_player:
            session[1][temp_player][2] = target
            await reply(message, "Successfully set **{}**'s target to **{}**.".format(get_name(temp_player), target))
        else:
            await reply(message, "Cannot find player named **" + player + "**")
        await log(2, "{0} ({1}) FORCE {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('session', [1, 1], "```\n{0}session takes no arguments\n\nReplies with the contents of the session variable in pm for debugging purposes. Admin only.```")
    async def cmd_session(self, ctx, message, parameters):
        await client.send_message(message.author, "```py\n{}\n```".format(str(session)))
        await log(2, "{0} ({1}) SESSION".format(message.author.name, message.author.id))


    @commands.command('time', [0, 0], "```\n{0}time takes no arguments\n\nChecks in-game time.```", 't')
    async def cmd_time(self, ctx, message, parameters):
        if session[0]:
            seconds = 0
            timeofday = ''
            sunstate = ''
            if session[2]:
                seconds = day_timeout - (datetime.now() - session[3][1]).seconds
                timeofday = 'daytime'
                sunstate = 'sunset'
            else:
                seconds = night_timeout - (datetime.now() - session[3][0]).seconds
                timeofday = 'nighttime'
                sunstate = 'sunrise'
            await reply(message, "It is now **{0}**. There is **{1:02d}:{2:02d}** until {3}.".format(timeofday, seconds // 60, seconds % 60, sunstate))
        else:
            if len(session[1]) > 0:
                timeleft = GAME_START_TIMEOUT - (datetime.now() - session[5]).seconds
                await reply(message, "There is **{0:02d}:{1:02d}** left to start the game until it will be automatically cancelled. "
                                    "GAME_START_TIMEOUT is currently set to **{2:02d}:{3:02d}**.".format(
                                        timeleft // 60, timeleft % 60, GAME_START_TIMEOUT // 60, GAME_START_TIMEOUT % 60))


    @commands.command('give', [2, 0], "```\n{0}give <player>\n\nIf you are a shaman or wolf shaman, gives your totem to <player>. You can see your totem by using `myrole` in pm.```")
    async def cmd_give(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or session[1][message.author.id][1] not in ['shaman', 'crazed shaman', 'wolf shaman'] or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You may only give totems during the night.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        if session[1][message.author.id][2] not in totems and session[1][message.author.id][1] != 'wolf shaman':
            await reply(message, "You have already given your totem to **" + get_name(session[1][message.author.id][2]) + "**.")
            return
        elif session[1][message.author.id][1] == 'wolf shaman' and not [x for x in session[1][message.author.id][4] if x.startswith('totem:')]:
            given_to = [x.split(":")[1] for x in session[1][message.author.id][4] if x.startswith('lasttarget:')]
            if given_to:
                await reply(message, "You have already given your totem to **{}**.".format(get_name(given_to[0])))
                return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        if 'lasttarget:{}'.format(player) in session[1][message.author.id][4]:
                            await reply(message, "You gave your totem to **{}** last time, you must choose someone else.".format(get_name(player)))
                            return
                        if session[1][message.author.id][1] in ["shaman", "crazed shaman"]:
                            totem = session[1][message.author.id][2]
                        else:
                            totem = [x for x in session[1][message.author.id][4] if x.startswith("totem:")][0].split(':')[1]
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        session[1][player][4].append(totem)
                        if session[1][message.author.id][1] == "wolf shaman":
                            session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if x != "totem:{}".format(totem)]

                        else:
                            if 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus' and totem not in ["protection_totem", "revealing_totem", "desperation_totem", "influence_totem", "luck_totem", "pestilence_totem", "retribution_totem"]:
                                await reply(message, "You may not give a succubus.")
                                return
                            session[1][message.author.id][2] = player
                            session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if not x.startswith('lasttarget:')] + ['lasttarget:{}'.format(player)]
                        await reply(message, "You have given your totem to **" + get_name(player) + "**.")
                        if session[1][message.author.id][1] == 'wolf shaman':
                            await wolfchat("**{0}** has given a totem to **{1}**.".format(get_name(message.author.id), get_name(player)))
                        session[1][message.author.id][4].append('given:{}'.format(totem))
                        await log(1, "{0} ({1}) GAVE {2} ({3}) {4}".format(get_name(message.author.id), message.author.id, get_name(player), player, totem))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('info', [0, 0], "```\n{0}info takes no arguments\n\nGives information on how the game works.```")
    async def cmd_info(self, ctx, message, parameters):
        msg = "In Werewolf, there are two teams, village and wolves. The villagers try to get rid of all of the wolves, and the wolves try to kill all of the villagers.\n"
        msg += "There are two phases, night and day. During night, the wolf/wolves choose a target to kill, and some special village roles like seer perform their actions. "
        msg += "During day, the village discusses everything and chooses someone to lynch. "
        msg += "Once you die, you can't talk in the lobby channel but you can discuss the game with the spectators in #spectator-chat.\n\n"
        msg += "To join a game, use `{0}join`. If you cannot chat in #lobby, then either a game is ongoing or you are dead.\n"
        msg += "For a list of roles, use the command `{0}roles`. For information on a particular role, use `{0}role role`. For statistics on the current game, use `{0}stats`. "
        msg += "For a list of commands, use `{0}list`. For help on a command, use `{0}help command`. To see the in-game time, use `{0}time`.\n\n"
        msg += "Please let belungawhale know about any bugs you might find."
        await reply(message, msg.format(BOT_PREFIX))


    @commands.command('notify_role', [0, 0], "```\n{0}notify_role [<true|false>]\n\nGives or take the " + WEREWOLF_NOTIFY_ROLE_NAME + " role.```")
    async def cmd_notify_role(self, ctx, message, parameters):
        if not WEREWOLF_NOTIFY_ROLE:
            await reply(message, "Error: A " + WEREWOLF_NOTIFY_ROLE_NAME + " role does not exist. Please let an admin know.")
            return
        member = client.get_server(WEREWOLF_SERVER).get_member(message.author.id)
        if not member:
            await reply(message, "You are not in the server!")
        has_role = WEREWOLF_NOTIFY_ROLE in member.roles
        if parameters == '':
            has_role = not has_role
        elif parameters in ['true', '+', 'yes']:
            has_role = True
        elif parameters in ['false', '-', 'no']:
            has_role = False
        else:
            await reply(message, commands['notify_role'][2].format(BOT_PREFIX))
            return
        if has_role:
            await client.add_roles(member, WEREWOLF_NOTIFY_ROLE)
            await reply(message, "You will be notified by @" + WEREWOLF_NOTIFY_ROLE.name + ".")
        else:
            await client.remove_roles(member, WEREWOLF_NOTIFY_ROLE)
            await reply(message, "You will not be notified by @" + WEREWOLF_NOTIFY_ROLE.name + ".")


    @commands.command('ignore', [1, 1], "```\n{0}ignore <add|remove|list> <user>\n\nAdds or removes <user> from the ignore list, or outputs the ignore list.```")
    async def cmd_ignore(self, ctx, message, parameters):
        parameters = ' '.join(message.content.strip().split(' ')[1:])
        parameters = parameters.strip()
        global IGNORE_LIST
        if parameters == '':
            await reply(message, commands['ignore'][2].format(BOT_PREFIX))
        else:
            action = parameters.split(' ')[0].lower()
            target = ' '.join(parameters.split(' ')[1:])
            member_by_id = client.get_server(WEREWOLF_SERVER).get_member(target.strip('<@!>'))
            member_by_name = client.get_server(WEREWOLF_SERVER).get_member_named(target)
            member = None
            if member_by_id:
                member = member_by_id
            elif member_by_name:
                member = member_by_name
            if action not in ['+', 'add', '-', 'remove', 'list']:
                await reply(message, "Error: invalid flag `" + action + "`. Supported flags are add, remove, list")
                return
            if not member and action != 'list':
                await reply(message, "Error: could not find target " + target)
                return
            if action in ['+', 'add']:
                if member.id in IGNORE_LIST:
                    await reply(message, member.name + " is already in the ignore list!")
                else:
                    IGNORE_LIST.append(member.id)
                    await reply(message, member.name + " was added to the ignore list.")
            elif action in ['-', 'remove']:
                if member.id in IGNORE_LIST:
                    IGNORE_LIST.remove(member.id)
                    await reply(message, member.name + " was removed from the ignore list.")
                else:
                    await reply(message, member.name + " is not in the ignore list!")
            elif action == 'list':
                if len(IGNORE_LIST) == 0:
                    await reply(message, "The ignore list is empty.")
                else:
                    msg_dict = {}
                    for ignored in IGNORE_LIST:
                        member = client.get_server(WEREWOLF_SERVER).get_member(ignored)
                        msg_dict[ignored] = member.name if member else "<user not in server with id " + ignored + ">"
                    await reply(message, str(len(IGNORE_LIST)) + " ignored users:\n```\n" + '\n'.join([x + " (" + msg_dict[x] + ")" for x in msg_dict]) + "```")
            else:
                await reply(message, commands['ignore'][2].format(BOT_PREFIX))
            await log(2, "{0} ({1}) IGNORE {2}".format(message.author.name, message.author.id, parameters))

    # TODO
    async def cmd_pingif(self, ctx, message, parameters):
        global pingif_dict
        if parameters == '':
            if message.author.id in pingif_dict:
                await reply(message, "You will be notified when there are at least **{}** players.".format(pingif_dict[message.author.id]))
            else:
                await reply(message, "You have not set a pingif yet. `{}pingif <number of players>`".format(BOT_PREFIX))
        elif parameters.isdigit():
            num = int(parameters)
            if num in range(MIN_PLAYERS, MAX_PLAYERS + 1):
                pingif_dict[message.author.id] = num
                await reply(message, "You will be notified when there are at least **{}** players.".format(pingif_dict[message.author.id]))
            else:
                await reply(message, "Please enter a number between {} and {} players.".format(MIN_PLAYERS, MAX_PLAYERS))
        else:
            await reply(message, "Please enter a valid number of players to be notified at.")


    @commands.command('online', [1, 1], "```\n{0}online takes no arguments\n\nNotifies all online users.```")
    async def cmd_online(self, ctx, message, parameters):
        members = [x.id for x in message.server.members]
        online = ["<@{}>".format(x) for x in members if is_online(x)]
        await reply(message, "PING! {}".format(''.join(online)), cleanmessage=False)


    @commands.command('notify', [0, 0], "```\n{0}notify [<true|false>]\n\nNotifies all online users who want to be notified, or adds/removes you from the notify list.```")
    async def cmd_notify(self, ctx, message, parameters):
        if session[0]:
            return
        notify = message.author.id in notify_me
        if parameters == '':
            online = ["<@{}>".format(x) for x in notify_me if is_online(x) and x not in session[1] and\
            (x in stasis and stasis[x] == 0 or x not in stasis)]
            await reply(message, "PING! {}".format(''.join(online)), cleanmessage=False)
        elif parameters in ['true', '+', 'yes']:
            if notify:
                await reply(message, "You are already in the notify list.")
                return
            notify_me.append(message.author.id)
            await reply(message, "You will be notified by {}notify.".format(BOT_PREFIX))
        elif parameters in ['false', '-', 'no']:
            if not notify:
                await reply(message, "You are not in the notify list.")
                return
            notify_me.remove(message.author.id)
            await reply(message, "You will not be notified by {}notify.".format(BOT_PREFIX))
        else:
            await reply(message, commands['notify'][2].format(BOT_PREFIX))


    @commands.command('getrole', [1, 1], "```\n{0}getrole <player> <revealtype>\n\nTests get_role command.```")
    async def cmd_getrole(self, ctx, message, parameters):
        if not session[0] or parameters == '':
            await reply(message, commands['getrole'][2].format(BOT_PREFIX))
            return
        player = parameters.split(' ')[0]
        revealtype = ' '.join(parameters.split(' ')[1:])
        temp_player = get_player(player)
        if temp_player:
            role = get_role(temp_player, revealtype)
            await reply(message, "**{}** is a **{}** using revealtype **{}**".format(get_name(temp_player), role, revealtype))
        else:
            await reply(message, "Cannot find player named **" + player + "**")


    @commands.command('entrance', [2, 0], "```\n{0}entrance <player>\n\nIf you are a succubus, entrances <player>. You will die if you visit the victim of the wolves.```")
    async def cmd_entrance(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['entrance'] or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You may only entrance during the night.")
            return
        if session[1][message.author.id][2]:
            await reply(message, "You are already entrancing **{}** tonight.".format(get_name(session[1][message.author.id][2])))
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "You may not entrance yourself. Use `pass` to not entrance anyone tonight.")
                    if get_role(player, 'role') == 'succubus':
                        await reply(message, "You cannot entrance another succubus.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id)
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id])
                        if 'entranced' not in session[1][player][4]:
                            await reply(message, "You are entrancing **{}** tonight.".format(get_name(player)))
                            session[1][message.author.id][2] = player
                            member = client.get_server(WEREWOLF_SERVER).get_member(player)
                            role = get_role(player, 'role')
                            templates = get_role(player, 'templates')
                            session[1][player][4].append('entranced')
                            succubus_message = "You have become entranced by **{0}**. From this point on, you must vote along with them or risk dying. You **cannot win with your own team**, but you will win should all alive players become entranced."
                            if role in COMMANDS_FOR_ROLE['kill'] and message.author.id in session[1][player][2]:
                                session[1][player][2] = ''
                                succubus_message += " You discover that **{0}** is a succubus and have retracted your kill as a result.\n".format(get_name(message.author.id))
                            if 'assassin' in templates and 'assassinate:{}'.format(message.author.id) in session[1][player][4]:
                                session[1][player][4].remove('assassinate:{}'.format(message.author.id))
                                succubus_message += " You discover that **{0}** is a succubus and must now target someone else.\n".format(get_name(message.author.id))
                            if role == 'hag' and session[1][player][2] == message.author.id:
                                succubus_message += " You discover that **{0}** is a succubus and have retracted your hex as a result.\n".format(get_name(message.author.id))
                                session[1][player][2] = ''
                                session[1][player][4].remove('lasttarget:{}'.format(message.author.id))
                            if role == 'piper' and ('tocharm' in session[1][message.author.id][4] or 'charmed' in session[1][message.author.id][4]):
                                succubus_message += " You discover that **{0}** is a succubus and have retracted your charm as a result.\n".format(get_name(message.author.id))
                                session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if x not in ['charmed', 'tocharm']]
                                session[1][player][4].append('charm')
                            if role in COMMANDS_FOR_ROLE['give']:
                                totem = ''
                                if role == 'wolf shaman' and not [x for x in session[1][player][4] if x.startswith('totem:')] and 'lasttarget:{}'.format(message.author.id) in session[1][player][4]:
                                    totem = [x.split(':')[1] for x in session[1][player][4] if x.startswith('given:')].pop()
                                elif message.author.id == session[1][player][2]:
                                    totem = [x.split(':')[1] for x in session[1][player][4] if x.startswith('given:')].pop()
                                if totem not in ["protection_totem", "revealing_totem", "desperation_totem", "influence_totem", "luck_totem", "pestilence_totem", "retribution_totem", '']:
                                    succubus_message += " You discover that **{0}** is a succubus and have retracted your totem as a result."
                                    session[1][message.author.id][4].remove(totem)
                                    session[1][player][4].remove('given:{}'.format(totem))
                                    session[1][player][4].remove('lasttarget:{}'.format(message.author.id))
                                    if role == 'wolf shaman':
                                        session[1][player][4].append('totem:{}'.format(totem))
                                    else:
                                        session[1][player][2] == totem
                            if member:
                                try:
                                    await client.send_message(member, succubus_message.format(get_name(message.author.id)))
                                except discord.Forbidden:
                                    pass
                            await log(1, "{0} ({1}) ENTRANCE {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                        else:
                            await reply(message, "**{}** is already entranced.".format(get_name(player)))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('curse', [2, 0], "```\n{0}curse <player>\n\nIf you are a warlock, curses <player>. Be fast though as the curse takes effect as soon as you use the command.```")
    async def cmd_curse(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['curse'] or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You may only curse during the night.")
            return
        if session[1][message.author.id][2]:
            await reply(message, "You have already cursed someone tonight.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "That would be a waste.")
                    elif player in [x for x in session[1] if roles[get_role(x, 'role')][0] == 'wolf' and get_role(x, 'role') not in ['minion', 'cultist']]:
                        await reply(message, "Cursing a fellow wolf would be a waste.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not curse a succubus.")
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        templates = get_role(player, 'templates')
                        if 'cursed' not in templates:
                            await reply(message, "You have cast a curse on **{}**.".format(get_name(player)))
                            await wolfchat("**{}** has cast a curse on **{}**.".format(get_name(message.author.id), get_name(player)))
                            session[1][message.author.id][2] = player
                            session[1][player][3].append('cursed')
                            await log(1, "{0} ({1}) CURSE {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                        else:
                            await reply(message, "**{}** is already cursed.".format(get_name(player)))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('charm', [2, 0], "```\n{0}charm <player1> [and <player2>]\n\nIf you are a piper, charms <player1> and <player2>. You can choose to charm only one player.```")
    async def cmd_charm(self, ctx, message, parameters):
        if not session[0] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['charm'] or not session[1][message.author.id][0] or not message.channel.is_private:
            return
        if parameters == "":
            await reply(message, roles[session[1][message.author.id][1]][2].format(BOT_PREFIX))
        elif "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if 'charm' not in session[1][message.author.id][4]:
                await reply(message, "You are already charming tonight.")
                return
            targets = parameters.split(' and ')
            if len(targets) <= 2:
                actual_targets = []
                for target in targets:
                    player = get_player(target)
                    if not player:
                        await reply(message, "Could not find player " + target)
                        return
                    actual_targets.append(player)
                actual_targets = set(actual_targets)
                valid_targets = []
                for player in actual_targets:
                    if not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                        return
                    elif 'charmed' in session[1][player][4] or 'tocharm' in session[1][player][4]:
                        await reply(message, "**{}** is already charmed!".format(get_name(player)))
                        return
                    elif get_role(player, 'role') == 'piper':
                        await reply(message, "That would be a waste.")
                        return
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not charm a succubus.")
                        return
                    else:
                        valid_targets.append(player)
                redirected_targets = []
                for player in valid_targets:
                    if 'misdirection_totem2' in session[1][message.author.id][4]:
                        new_target = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4]) and not ('charmed' in session[1][x][4] or 'tocharm' in session[1][x][4])])
                        redirected_targets.append(new_target)
                    elif 'luck_totem2' in session[1][player][4]:
                        new_target = misdirect(player)
                        redirected_targets.append(new_targe, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4]) and not 'charmed' in session[1][x][4] or 'tocharm' in session[1][x][4]])
                    else:
                        redirected_targets.append(player)
                if len(valid_targets) == 2:
                    await reply(message, "You have charmed **{}** and **{}**.".format(*map(get_name, redirected_targets)))
                    await log(1, "{} ({}) CHARM {} ({}) AND {} ({})".format(get_name(message.author.id), message.author.id, get_name(redirected_targets[0]), redirected_targets[0], get_name(redirected_targets[1]), redirected_targets[1]))
                    for piper in [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'piper' and x != message.author.id]:
                        member = client.get_server(WEREWOLF_SERVER).get_member(piper)
                        if member:
                            try:
                                await client.send_message(member, "Another piper has charmed **{}** and **{}**!".format(*map(get_name, redirected_targets)))
                            except discord.Forbidden:
                                pass
                elif len(valid_targets) == 1:
                    await reply(message, "You have charmed **{}**.".format(*map(get_name, redirected_targets)))
                    await log(1, "{} ({}) CHARM {} ({})".format(get_name(message.author.id), message.author.id, get_name(redirected_targets[0]), redirected_targets[0]))
                    for piper in [x for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'piper' and x != message.author.id]:
                        member = client.get_server(WEREWOLF_SERVER).get_member(piper)
                        if member:
                            try:
                                await client.send_message(member, "Another piper has charmed **{}**!".format(*map(get_name, redirected_targets)))
                            except discord.Forbidden:
                                pass
                session[1][message.author.id][4].remove('charm')
                for charmed in redirected_targets:
                    session[1][charmed][4].append('tocharm')
            else:
                await reply(message, "You must choose two different players.")


    @commands.command('clone', [2, 0], "```\n{0}clone <player1>\n\n If you are a clone, makes <player> your cloning target.```")
    async def cmd_clone(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['clone'] or not session[1][message.author.id][0]:
            return
        if 'clone' not in session[1][message.author.id][4]:
            await reply(message, "You have already chosen someone to clone.")
            return
        if session[2]:
            await reply(message, "You can only clone during the night.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "You can't clone yourself!")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        session[1][message.author.id][4].append("clone:{}".format(player))
                        await reply(message, "You have chosen to clone **{}**. If they die you will take their role.".format(get_name(player)))
                        await log(1, "{0} ({1}) CLONE TARGET {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                        session[1][message.author.id][4].remove('clone')
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('side', [2, 0], "```\n{0}side <villagers>/<wolves>\n\nIf you are a turncoat, switches which team you are siding with.```")
    async def cmd_side(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['side'] or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You can only switch sides during the night.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        if 'sided2' in session[1][message.author.id][4]:
            await reply(message, "You cannot switch sides again until tomorrow night.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            elif parameters in ["villagers", "village", "v", "vils", "vil"] :
                if 'side:villagers' not in session[1][message.author.id][4]:
                    session[1][message.author.id][2] = 'villagers'
                    await reply(message, "You are now siding with the village.")
                    return
                else:
                    session[1][message.author.id][2] = 'pass'
                    await reply(message, "You have decided not to change sides tonight.")
            elif parameters in ["wolves", "wolf", "w", "woof"] :
                if 'side:wolves' not in session[1][message.author.id][4]:
                    session[1][message.author.id][2] = 'wolves'
                    await reply(message, "You are now siding with the wolves.")
                    return
                else:
                    session[1][message.author.id][2] = 'pass'
                    await reply(message, "You have decided not to change sides tonight.")
            else:
                return
                    

    @commands.command('visit', [2, 0], "```\n{0}visit <player>\n\nIf you are a harlot, visits <player>. You can stay home by visiting yourself. "
                        "You will die if you visit a wolf or the victim of the wolves. If you are a succubus, entrances <player>```")
    async def cmd_visit(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['visit'] or not session[1][message.author.id][0]:
            return
        if get_role(message.author.id, 'role') == 'succubus':
            await cmd_entrance(message, parameters)
            return
        if session[2]:
            await reply(message, "You may only visit during the night.")
            return
        if session[1][message.author.id][2]:
            if message.author.id == session[1][message.author.id][2]:
                await reply(message, "You are already spending the night at home.")
            else:
                await reply(message, "You are already spending the night with **{}**.".format(get_name(session[1][message.author.id][2])))
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "You have chosen to stay home tonight.")
                        session[1][message.author.id][2] = message.author.id
                        await log(1, "{0} ({1}) STAY HOME".format(get_name(message.author.id), message.author.id))
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not visit a succubus.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        await reply(message, "You are spending the night with **{}**. Have a good time!".format(get_name(player)))
                        session[1][message.author.id][2] = player
                        member = client.get_server(WEREWOLF_SERVER).get_member(player)
                        if member:
                            try:
                                await client.send_message(member, "You are spending the night with **{}**. Have a good time!".format(get_name(message.author.id)))
                            except discord.Forbidden:
                                pass
                        await log(1, "{0} ({1}) VISIT {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('totem', [0, 0], "```\n{0}totem [<totem>]\n\nReturns information on a totem, or displays a list of totems.```", 'totems')
    async def cmd_totem(self, ctx, message, parameters):
        if not parameters == '':
            reply_totems = []
            for totem in totems:
                if totem.startswith(parameters):
                    reply_totems.append(totem)
            if _autocomplete(parameters, totems)[1] == 1:
                totem = _autocomplete(parameters, totems)[0]
                reply_msg = "```\n"
                reply_msg += totem[0].upper() + totem[1:].replace('_', ' ') + "\n\n"
                reply_msg += totems[totem] + "```"
                await reply(message, reply_msg)
                return
        await reply(message, "Available totems: " + ", ".join(sorted([x.replace('_', ' ') for x in totems])))


    @commands.command('fgame', [1, 2], "```\n{0}fgame [<gamemode>]\n\nForcibly sets or unsets [<gamemode>].```")
    async def cmd_fgame(self, ctx, message, parameters):
        if session[0]:
            return
        if parameters == '':
            if session[6] != '':
                session[6] = ''
                await reply(message, "Successfully unset gamemode.")
            else:
                await reply(message, "Gamemode has not been set.")
        else:
            if parameters.startswith('roles'):
                role_string = ' '.join(parameters.split(' ')[1:])
                if role_string == '':
                    await reply(message, "`{}fgame roles wolf:1,traitor:1,shaman:2,cursed villager:2,etc.`".format(BOT_PREFIX))
                else:
                    session[6] = parameters
                    await reply(message, "Successfully set gamemode roles to `{}`".format(role_string))
            else:
                choices, num = _autocomplete(parameters, gamemodes)
                if num == 1:
                    session[6] = choices
                    await reply(message, "Successfuly set gamemode to **{}**.".format(choices))
                elif num > 1:
                    await reply(message, "Multiple choices: {}".format(', '.join(sorted(choices))))
                else:
                    await reply(message, "Could not find gamemode {}".format(parameters))
        await log(2, "{0} ({1}) FGAME {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('github', [0, 0], "```\n{0}github takes no arguments\n\nReturns a link to the bot's Github repository.```")
    async def cmd_github(self, ctx, message, parameters):
        await reply(message, "http://github.com/belguawhale/Discord-Werewolf")


    @commands.command('ftemplate', [1, 2], "```\n{0}ftemplate <player> [<add|remove|set>] [<template1 [template2 ...]>]\n\nManipulates a player's templates.```")
    async def cmd_ftemplate(self, ctx, message, parameters):
        if not session[0]:
            return
        if parameters == '':
            await reply(message, commands['ftemplate'][2].format(BOT_PREFIX))
            return
        params = parameters.split(' ')
        player = get_player(params[0])
        if len(params) > 1:
            action = parameters.split(' ')[1]
        else:
            action = ""
        if len(params) > 2:
            templates = parameters.split(' ')[2:]
        else:
            templates = []
        if player:
            reply_msg = "Successfully "
            if action in ['+', 'add', 'give']:
                session[1][player][3] += templates
                reply_msg += "added templates **{0}** to **{1}**."
            elif action in ['-', 'remove', 'del']:
                for template in templates[:]:
                    if template in session[1][player][3]:
                        session[1][player][3].remove(template)
                    else:
                        templates.remove(template)
                reply_msg += "removed templates **{0}** from **{1}**."
            elif action in ['=', 'set']:
                session[1][player][3] = templates
                reply_msg += "set **{1}**'s templates to **{0}**."
            else:
                reply_msg = "**{1}**'s templates: " + ', '.join(session[1][player][3])
        else:
            reply_msg = "Could not find player {1}."

        await reply(message, reply_msg.format(', '.join(templates), get_name(player)))
        await log(2, "{0} ({1}) FTEMPLATE {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('fother', [1, 2], "```\n{0}fother <player> [<add|remove|set>] [<other1 [other2 ...]>]\n\nManipulates a player's other flag (totems, traitor).```")
    async def cmd_fother(self, ctx, message, parameters):
        if not session[0]:
            return
        if parameters == '':
            await reply(message, commands['fother'][2].format(BOT_PREFIX))
            return
        params = parameters.split(' ')
        player = get_player(params[0])
        if len(params) > 1:
            action = parameters.split(' ')[1]
        else:
            action = ""
        if len(params) > 2:
            others = parameters.split(' ')[2:]
        else:
            others = []
        if player:
            reply_msg = "Successfully "
            if action in ['+', 'add', 'give']:
                session[1][player][4] += others
                reply_msg += "added **{0}** to **{1}**'s other flag."
            elif action in ['-', 'remove', 'del']:
                for other in others[:]:
                    if other in session[1][player][4]:
                        session[1][player][4].remove(other)
                    else:
                        others.remove(other)
                reply_msg += "removed **{0}** from **{1}**'s other flag."
            elif action in ['=', 'set']:
                session[1][player][4] = others
                reply_msg += "set **{1}**'s other flag to **{0}**."
            else:
                reply_msg = "**{1}**'s other flag: " + ', '.join(session[1][player][4])
        else:
            reply_msg = "Could not find player {1}."

        await reply(message, reply_msg.format(', '.join(others), get_name(player)))
        await log(2, "{0} ({1}) FOTHER {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('faftergame', [2, 2], "```\n{0}faftergame <command> [<parameters>]\n\nSchedules <command> to run with [<parameters>] after the next game ends.```")
    async def cmd_faftergame(self, ctx, message, parameters):
        if parameters == "":
            await reply(message, commands['faftergame'][2].format(BOT_PREFIX))
            return
        command = parameters.split(' ')[0]
        if command in commands:
            global faftergame
            faftergame = message
            await reply(message, "Command `{}` will run after the next game ends.".format(parameters))
        else:
            await reply(message, "{} is not a valid command!".format(command))


    @commands.command('uptime', [0, 0], "```\n{0}uptime takes no arguments\n\nChecks the bot's uptime.```")
    async def cmd_uptime(self, ctx, message, parameters):
        delta = datetime.now() - starttime
        output = [[delta.days, 'day'],
                [delta.seconds // 3600, 'hour'],
                [delta.seconds // 60 % 60, 'minute'],
                [delta.seconds % 60, 'second']]
        for i in range(len(output)):
            if output[i][0] != 1:
                output[i][1] += 's'
        reply_msg = ''
        if output[0][0] != 0:
            reply_msg += "{} {} ".format(output[0][0], output[0][1])
        for i in range(1, len(output)):
            reply_msg += "{} {} ".format(output[i][0], output[i][1])
        reply_msg = reply_msg[:-1]
        await reply(message, "Uptime: **{}**".format(reply_msg))


    @commands.command('fstasis', [1, 1], "```\n{0}fstasis <player> [<add|remove|set>] [<amount>]\n\nManipulates a player's stasis.```")
    async def cmd_fstasis(self, ctx, message, parameters):
        if parameters == '':
            await reply(message, commands['fstasis'][2].format(BOT_PREFIX))
            return
        params = parameters.split(' ')
        player = params[0].strip('<!@>')
        member = client.get_server(WEREWOLF_SERVER).get_member(player)
        name = "user not in server with id " + player
        if member:
            name = member.display_name
        if len(params) > 1:
            action = parameters.split(' ')[1]
        else:
            action = ''
        if len(params) > 2:
            amount = parameters.split(' ')[2]
            if amount.isdigit():
                amount = int(amount)
            else:
                amount = -1
        else:
            amount = -2
        if player.isdigit():
            if action and amount >= -1:
                if amount >= 0:
                    if player not in stasis:
                        stasis[player] = 0
                    reply_msg = "Successfully "
                    if action in ['+', 'add', 'give']:
                        stasis[player] += amount
                        reply_msg += "increased **{0}** ({1})'s stasis by **{2}**."
                    elif action in ['-', 'remove', 'del']:
                        amount = min(amount, stasis[player])
                        stasis[player] -= amount
                        reply_msg += "decreased **{0}** ({1})'s stasis by **{2}**."
                    elif action in ['=', 'set']:
                        stasis[player] = amount
                        reply_msg += "set **{0}** ({1})'s stasis to **{2}**."
                    else:
                        if player not in stasis:
                            amount = 0
                        else:
                            amount = stasis[player]
                        reply_msg = "**{0}** ({1}) is in stasis for **{2}** game{3}."
                else:
                    reply_msg = "Stasis must be a non-negative integer."
            else:
                if player not in stasis:
                    amount = 0
                else:
                    amount = stasis[player]
                reply_msg = "**{0}** ({1}) is in stasis for **{2}** game{3}."
        else:
            reply_msg = "Invalid mention/id: {0}."

        await reply(message, reply_msg.format(name, player, amount, '' if int(amount) == 1 else 's'))
        await log(2, "{0} ({1}) FSTASIS {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('gamemode', [0, 0], "```\n{0}gamemode [<gamemode>]\n\nDisplays information on [<gamemode>] or displays a "
                            "list of gamemodes.```", 'game', 'gamemodes')
    async def cmd_gamemode(self, ctx, message, parameters):
        gamemode, num = _autocomplete(parameters, gamemodes)
        if num == 1 and parameters != '':
            await reply(message, "<https://werewolf.miraheze.org/wiki/{}>\n```\nGamemode: {}\nPlayers: {}\nDescription: {}\n\nUse the command "
                                "`!roles {} guide` to view roles for this gamemode.```".format(gamemode + "_(gamemode)" if gamemode == "lycan" else gamemode.replace(' ', '_'),
            gamemode, str(gamemodes[gamemode]['min_players']) + '-' + str(gamemodes[gamemode]['max_players']),
            gamemodes[gamemode]['description'], gamemode))
        else:
            game_list = ""
            game_list += "\n```ini\n[Main Modes] " + ", ".join(sorted(x for x in (gamemodes) if gamemodes[x]['chance'] != 0))
            game_list += "\n[Majority Only] " + ", ".join(sorted(x for x in (gamemodes) if gamemodes[x]['chance'] == 0)) + "```"
            await reply(message, game_list)


    @commands.command('verifygamemode', [1, 1], "```\n{0}verifygamemode [<gamemode>]\n\nChecks to make sure [<gamemode>] is valid.```", 'verifygamemodes')
    async def cmd_verifygamemode(self, ctx, message, parameters):
        if parameters == '':
            await reply(message, "```\n{}\n```".format(verify_gamemodes()))
        elif _autocomplete(parameters, gamemodes)[1] == 1:
            await reply(message, "```\n{}\n```".format(verify_gamemode(_autocomplete(parameters, gamemodes)[0])))
        else:
            await reply(message, "Invalid gamemode: {}".format(parameters))


    @commands.command('shoot', [0, 2], "```\n{0}shoot <player>\n\nIf you have a gun, shoots <player> during the day. You may only use this command in channel.```")
    async def cmd_shoot(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or not session[1][message.author.id][0]:
            return
        if ('gunner' not in get_role(message.author.id, 'templates') and 'sharpshooter' not in get_role(message.author.id, 'templates')):
            try:
                await client.send_message(message.author, "You don't have a gun.")
            except discord.Forbidden:
                pass
            return
        if not session[2]:
            try:
                await client.send_message(message.author, "You may only shoot players during the day.")
            except discord.Forbidden:
                pass
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            try:
                await client.send_message(message.author, "You have been silenced, and are unable to use any special powers.")
            except discord.Forbidden:
                pass
            return
        msg = ''
        pm = False
        ded = None
        outcome = ''
        if session[1][message.author.id][4].count('bullet') < 1:
            msg = "You have no more bullets."
            pm = True
        else:
            if parameters == "":
                msg = commands['shoot'][2].format(BOT_PREFIX)
                pm = True
            else:
                target = get_player(parameters.split(' ')[0])
                if not target:
                    target = get_player(parameters)
                if not target:
                    msg = 'Could not find player {}'.format(parameters)
                elif target == message.author.id:
                    msg = "You are holding it the wrong way."
                elif not session[1][target][0]:
                    msg = "Player **{}** is dead!".format(get_name(target))
                else:
                    if 'misdirection_totem2' in session[1][message.author.id][4]:
                        target = misdirect(message.author.id)
                    elif 'luck_totem2' in session[1][target][4]:
                        target = misdirect(target, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id])
                    if get_role(message.author.id, 'role') == 'village drunk':
                        SUICIDE = DRUNK_SUICIDE
                        MISS = DRUNK_MISS
                        HEADSHOT = DRUNK_HEADSHOT
                        INJURE = DRUNK_INJURE
                    else:
                        SUICIDE = GUNNER_SUICIDE
                        MISS = GUNNER_MISS
                        HEADSHOT = GUNNER_HEADSHOT
                        INJURE = GUNNER_INJURE
                    wolf = get_role(message.author.id, 'role') in WOLFCHAT_ROLES
                    session[1][message.author.id][4].remove('bullet')
                    if wolf:
                        if get_role(target, 'role') in WOLFCHAT_ROLES:
                            outcome = 'miss'
                    else:
                        if get_role(target, 'role') in ACTUAL_WOLVES:
                            if get_role(target, 'role') in ['werekitten']:
                                outcome = random.choice((['suicide'] * SUICIDE + ['miss'] * (MISS + HEADSHOT + INJURE)) if 'sharpshooter' not in get_role(message.author.id, 'templates') else ['miss'])
                            else:
                                outcome = 'killwolf'
                        elif get_role(target, 'role') == 'succubus':
                            outcome = random.choice((['suicide'] * SUICIDE + ['miss'] * (MISS + HEADSHOT) + ['injure'] * INJURE) if 'sharpshooter' not in get_role(message.author.id, 'templates') else ['killvictim'])
                    if outcome == '':
                        outcome = random.choice((['miss'] * MISS + ['suicide'] * SUICIDE \
                                                + ['killvictim'] * HEADSHOT + ['injure'] * INJURE)  if 'sharpshooter' not in get_role(message.author.id, 'templates') else ['killvictim'])
                    if outcome in ['injure', 'killvictim', 'killwolf']:
                        msg = "**{}** shoots **{}** with a bullet!\n\n".format(get_name(message.author.id), get_name(target))
                    if outcome == 'miss':
                        msg += "**{}** is a lousy shooter and missed!".format(get_name(message.author.id))
                    elif outcome == 'killwolf':
                        if session[6] == 'noreveal':
                            msg += "**{}** is a wolf and is dying from the silver bullet!".format(get_name(target))
                        else:
                            msg += "**{}** is a **{}** and is dying from the silver bullet!".format(get_name(target),
                                get_role(target, 'death'))
                        ded = target
                    elif outcome == 'suicide':
                        msg += "Oh no! **{}**'s gun was poorly maintained and has exploded! ".format(get_name(message.author.id))
                        if session[6] != 'noreveal':
                            msg += "The village mourns a **gunner-{}**.".format(get_role(message.author.id, 'death'))
                        ded = message.author.id
                    elif outcome == 'killvictim':
                        if session[6] == 'noreveal':
                            msg += "**{}** is not a wolf but was fatally injured.".format(get_name(target))
                        else:
                            msg += "**{}** is not a wolf but was fatally injured. The village has sacrificed a **{}**.".format(
                                get_name(target), get_role(target, 'death'))
                        ded = target
                    elif outcome == 'injure':
                        msg += "**{}** is a villager and was injured. Luckily the injury is minor and will heal after a day of rest.".format(
                                get_name(target))
                        session[1][target][4].append('injured')
                    else:
                        msg += "wtf? (this is an error, please report to an admin)"

                    await log(1, "{} ({}) SHOOT {} ({}) WITH OUTCOME {}".format(get_name(message.author.id), message.author.id,
                        get_name(target), target, outcome))

        if pm:
            target = message.author
        else:
            target = client.get_channel(GAME_CHANNEL)
        try:
            await client.send_message(target, msg)
        except discord.Forbidden:
            pass

        if ded:
            await player_deaths({ded : ('gunner ' + outcome, get_role(message.author.id, "actualteam"))})
            await check_traitor()
        elif outcome == 'injured':
            session[1][target][4].append('injured')


    @commands.command('target', [2, 0], "```\n{0}target <player>\n\nIf you are an assassin, makes <player> your target during the night.```", 'assassinate')
    async def cmd_target(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or COMMANDS_FOR_ROLE['target'][0] not in get_role(message.author.id, "templates") or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You may only target a player during the night.")
            return
        if [x for x in session[1][message.author.id][4] if x.startswith("assassinate:")]:
            await reply(message, "You have already targeted someone. You must wait until they die to target again.")
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "You can't target yourself!")
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not target a succubus.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        session[1][message.author.id][4].append("assassinate:{}".format(player))
                        await reply(message, "You have chosen to target **{}**. They will be your target until they die.".format(
                            get_name(player)))
                        await log(1, "{0} ({1}) TARGET {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('fsay', [1, 1], "```\n{0}fsay <message>\n\nSends <message> to the lobby channel.```")
    async def cmd_fsay(self, ctx, message, parameters):
        if parameters:
            await send_lobby(parameters)
            await log(2, "{} ({}) FSAY {}".format(message.author.name, message.author.id, parameters))
        else:
            await reply(message, commands['fsay'][2].format(BOT_PREFIX))


    @commands.command('observe', [2, 0], "```\n{0}observe <player>\n\nIf you are a werecrow, tells you if <player> was in their bed for the night. "
                            "If you are a sorcerer, tells you if <player> has supernatural powers (seer, etc.).```")
    async def cmd_observe(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['observe'] or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You may only observe during the night.")
            return
        if get_role(message.author.id, 'role') == 'werecrow':
            if 'observe' in session[1][message.author.id][4]:
                await reply(message, "You are already observing someone!.")
                return
            if "silence_totem2" in session[1][message.author.id][4]:
                await reply(message, "You have been silenced, and are unable to use any special powers.")
                return
            else:
                if parameters == "":
                    await reply(message, roles[session[1][message.author.id][1]][2])
                else:
                    player = get_player(parameters)
                    if player:
                        if player == message.author.id:
                            await reply(message, "That would be a waste.")
                        elif player in [x for x in session[1] if roles[get_role(x, 'role')][0] == 'wolf' and get_role(x, 'role') not in ['minion', 'cultist']]:
                            await reply(message, "Observing another wolf is a waste of time.")
                        elif not session[1][player][0]:
                            await reply(message, "Player **" + get_name(player) + "** is dead!")
                        elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                            await reply(message, "You may not observe a succubus.")
                        else:
                            session[1][message.author.id][4].append('observe')
                            if 'misdirection_totem2' in session[1][message.author.id][4]:
                                player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                            elif 'luck_totem2' in session[1][player][4]:
                                player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                            await reply(message, "You transform into a large crow and start your flight to **{0}'s** house. You will "
                                                "return after collecting your observations when day begins.".format(get_name(player)))
                            await wolfchat("**{}** is observing **{}**.".format(get_name(message.author.id), get_name(player)))
                            await log(1, "{0} ({1}) OBSERVE {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                            while not session[2] and win_condition() == None and session[0]:
                                await asyncio.sleep(0.1)
                            if 'observe' in session[1][message.author.id][4]:
                                session[1][message.author.id][4].remove('observe')
                            if get_role(player, 'role') in ['seer', 'oracle', 'harlot', 'hunter', 'augur', 'bodyguard', 'guardian angel', 'succubus']\
                                and session[1][player][2] in set(session[1]) - set(player)\
                                or get_role(player, 'role') in ['shaman', 'crazed shaman', 'piper', ]\
                                and session[1][player][2] in session[1]:
                                    msg = "not in bed all night"
                            else:
                                    msg = "sleeping all night long"
                            try:
                                await client.send_message(message.author, "As the sun rises, you conclude that **{}** was {}, and you fly back to your house.".format(
                                    get_name(player), msg))
                            except discord.Forbidden:
                                pass
                    else:
                        await reply(message, "Could not find player " + parameters)
        elif get_role(message.author.id, 'role') == 'sorcerer':
            if session[1][message.author.id][2]:
                await reply(message, "You have already used your power.")
            elif parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "Using your power on yourself would be a waste.")
                    elif player in [x for x in session[1] if roles[get_role(x, 'role')][0] == 'wolf' and get_role(x, 'role') != 'cultist']:
                        await reply(message, "Observing another wolf is a waste of time.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    elif 'entranced' in session[1][message.author.id][4] and get_role(player, 'role') == 'succubus':
                        await reply(message, "You may not observe a succubus.")
                    else:
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id, alive_players=[x for x in session[1] if session[1][x][0] and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and get_role(x, 'role') not in WOLFCHAT_ROLES and not (get_role(x, 'role') == 'succubus' and 'entranced' in session[1][message.author.id][4])])
                        session[1][message.author.id][2] = player
                        target_role = get_role(player, 'role')
                        if target_role == 'amnesiac':
                            target_role = [x.split(':')[1].replace("_", " ") for x in session[1][player][4] if x.startswith("role:")].pop()
                        if target_role in ['seer', 'oracle', 'augur']:
                            debug_msg = target_role
                            msg = "**{}** is a **{}**!".format(get_name(player), get_role(player, 'role'))
                        else:
                            debug_msg = "not paranormal"
                            msg = "**{}** does not have paranormal senses.".format(get_name(player))
                        await wolfchat("**{}** is observing **{}**.".format(get_name(message.author.id), get_name(player)))
                        await reply(message, "After casting your ritual, you determine that " + msg)
                        await log(1, "{0} ({1}) OBSERVE {2} ({3}) AS {4}".format(get_name(message.author.id), message.author.id, get_name(player), player, debug_msg))
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('id', [2, 0], "```\n{0}id <player>\n\nIf you are a detective, investigates <player> during the day.```")
    async def cmd_id(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['id'] or not session[1][message.author.id][0]:
            return
        if not session[2]:
            await reply(message, "You may only investigate during the day.")
            return
        if 'investigate' in session[1][message.author.id][4]:
            await reply(message, "You have already investigated someone.")
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if player == message.author.id:
                        await reply(message, "Investigating yourself would be a waste.")
                    elif not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                    else:
                        session[1][message.author.id][4].append('investigate')
                        if 'misdirection_totem2' in session[1][message.author.id][4]:
                            player = misdirect(message.author.id)
                        elif 'luck_totem2' in session[1][player][4]:
                            player = misdirect(player, alive_players=[x for x in session[1] if session[1][x][0] and x != message.author.id])
                        await reply(message, "The results of your investigation have returned. **{}** is a **{}**!".format(
                            get_name(player), get_role(player, 'role') if not get_role(player, 'role') == 'amnesiac' else [x.split(':')[1].replace("_", " ") for x in session[1][player][4] if x.startswith("role:")].pop()))
                        await log(1, "{0} ({1}) INVESTIGATE {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                        if random.random() < DETECTIVE_REVEAL_CHANCE:
                            await wolfchat("Someone accidentally drops a paper. The paper reveals that **{}** ({}) is the detective!".format(
                                get_name(message.author.id), message.author.id))
                            await log(1, "{0} ({1}) DETECTIVE REVEAL".format(get_name(message.author.id), message.author.id))
                        while session[2] and win_condition() == None and session[0]:
                            await asyncio.sleep(0.1)
                        if 'investigate' in session[1][message.author.id][4]:
                            session[1][message.author.id][4].remove('investigate')
                else:
                    await reply(message, "Could not find player " + parameters)


    @commands.command('frevive', [1, 2], "```\n{0}frevive <player>\n\nRevives <player>. Used for debugging purposes.```")
    async def cmd_frevive(self, ctx, message, parameters):
        if not session[0]:
            return
        if parameters == "":
            await reply(message, commands['frevive'][2].format(BOT_PREFIX))
        else:
            player = get_player(parameters)
            if player:
                if session[1][player][0]:
                    await reply(message, "Player **{}** is already alive!".format(player))
                else:
                    session[1][player][0] = True
                    await reply(message, ":thumbsup:")
            else:
                await reply(message, "Could not find player {}".format(parameters))
        await log(2, "{} ({}) FREVIVE {}".format(message.author.name, message.author.id, parameters))


    @commands.command('pass', [2, 0], "```\n{0}pass takes no arguments\n\nChooses to not perform your action tonight.```")
    async def cmd_pass(self, ctx, message, parameters):
        role = get_role(message.author.id, 'role')
        if not session[0] or message.author.id not in session[1] or role not in COMMANDS_FOR_ROLE['pass'] or not session[1][message.author.id][0]:
            return
        if session[2] and role in ('harlot', 'hunter', 'guardian angel'):
            await reply(message, "You may only pass during the night.")
            return
        if session[1][message.author.id][2] != '':
            return
        if role == 'harlot':
            session[1][message.author.id][2] = message.author.id
            await reply(message, "You have chosen to stay home tonight.")
        elif role == 'succubus':
            session[1][message.author.id][2] = message.author.id
            await reply(message, "You have chosen to not entrance anyone tonight.")
        elif role == 'warlock':
            session[1][message.author.id][2] = message.author.id
            await reply(message, "You have chosen not to curse anyone tonight.")
            await wolfchat("**{}** has chosen not to curse anyone tonight.".format(get_name(message.author.id)))
        elif role == 'hunter':
            session[1][message.author.id][2] = message.author.id
            await reply(message, "You have chosen to not kill anyone tonight.")
        elif role in ['guardian angel', 'bodyguard']:
            session[1][message.author.id][2] = 'pass'
            await reply(message, "You have chosen to not guard anyone tonight.")
        elif role == 'piper':
            session[1][message.author.id][4] = [x for x in session[1][message.author.id][4] if x != 'charm']
            await reply(message, "You have chosen not to charm anyone tonight.")
        elif role == 'turncoat':
            if 'sided2' in session[1][message.author.id][4]:
                return
            session[1][message.author.id][2] = 'pass'
            await reply(message, "You have chosen not to switch sides tonight.")
        else:
            await reply(message, "wtf? (this is an error; please report to an admin")
        await log(1, "{0} ({1}) PASS".format(get_name(message.author.id), message.author.id))

    @commands.command('cat', [0, 0], "```\n{0}cat takes no arguments\n\nFlips a cat.```")
    async def cmd_cat(self, ctx, message, parameters):
        await reply(message, "The cat landed on **its feet**!")


    @commands.command('fgoat', [1, 1], "```\n{0}fgoat <target>\n\nForcibly sends a goat to violently attack <target>.```")
    async def cmd_fgoat(self, ctx, message, parameters):
        if parameters == '':
            await reply(message, commands['fgoat'][2].format(BOT_PREFIX))
            return
        action = random.choice(['kicks', 'headbutts'])
        await send_lobby("**{}**'s goat walks by and {} **{}**.".format(message.author.name, action, parameters))


    @commands.command('guard', [2, 0], "```\n{0}guard <target>\n\nGuards <player>, preventing them from dying this night. Can guard yourself, however "
                        "cannot be used on the same target twice in a row.```", 'protect')
    async def cmd_guard(self, ctx, message, parameters):
        if not session[0] or message.author.id not in session[1] or get_role(message.author.id, 'role') not in COMMANDS_FOR_ROLE['guard'] \
        or not session[1][message.author.id][0]:
            return
        if session[2]:
            await reply(message, "You may only guard players during the night.")
            return
        if session[1][message.author.id][2]:
            if session[1][message.author.id][2] == 'pass':
                await reply(message, "You have already chosen to not guard anyone tonight.")
            else:
                await reply(message, "You are already guarding **{}**.".format(get_name(session[1][message.author.id][2])))
            return
        if "silence_totem2" in session[1][message.author.id][4]:
            await reply(message, "You have been silenced, and are unable to use any special powers.")
            return
        else:
            if parameters == "":
                await reply(message, roles[session[1][message.author.id][1]][2])
            else:
                player = get_player(parameters)
                if player:
                    if 'lasttarget:' + player in session[1][message.author.id][4]: # so hacky but whaterver
                        await reply(message, "You already guarded **{}** last night. You may not guard the same player two nights in a row.".format(get_name(player)))
                        return
                    session[1][message.author.id][4][:] = [x for x in session[1][message.author.id][4] if not x.startswith('lasttarget:')]
                    if not session[1][player][0]:
                        await reply(message, "Player **" + get_name(player) + "** is dead!")
                        return
                    if 'misdirection_totem2' in session[1][message.author.id][4]:
                        new_target = misdirect(message.author.id)
                        while 'lasttarget:' + new_target in session[1][message.author.id][4]:
                            new_target = misdirect(message.author.id)
                        player = new_target
                    elif 'luck_totem2' in session[1][player][4]:
                        new_target = misdirect(player)
                        while 'lasttarget:' + new_target in session[1][message.author.id][4]:
                            new_target = misdirect(player)
                        player = new_target
                    if get_role(message.author.id, 'role') == 'guardian angel':
                        session[1][message.author.id][4].append('lasttarget:' + player)
                    if player == message.author.id:
                        if get_role(message.author.id, 'role') == 'guardian angel':
                            await reply(message, "You have chosen to guard yourself tonight.")
                            session[1][message.author.id][2] = message.author.id
                            session[1][message.author.id][4].append("guarded")
                            await log(1, "{0} ({1}) GUARD SELF".format(get_name(message.author.id), message.author.id))
                        else:
                            await reply(message, "You cannot guard yourself. Use pass if you do not wish to guard anyone tonight.")
                            return
                    else:
                        await reply(message, "You have chosen to guard **{}**.".format(get_name(player)))
                        session[1][message.author.id][2] = player
                        if get_role(message.author.id, 'role') == 'guardian angel':
                            session[1][player][4].append("guarded")
                        elif get_role(message.author.id, 'role') == 'guardian angel':
                            session[1][player][4].append("bodyguard:{}".format(message.author.id))
                        member = client.get_server(WEREWOLF_SERVER).get_member(player)
                        if member:
                            try:
                                await client.send_message(member, "You can sleep well tonight, for you are being protected.")
                            except discord.Forbidden:
                                pass
                        await log(1, "{0} ({1}) GUARD {2} ({3})".format(get_name(message.author.id), message.author.id, get_name(player), player))
                else:
                    await reply(message, "Could not find player " + parameters)

    @commands.command('shutdown', [2, 2], "```\n{0}shutdown takes no arguments\n\nShuts down the bot. Owner-only.```")
    async def cmd_shutdown(self, ctx, message, parameters):
        if parameters.startswith("-fstop"):
            await cmd_fstop(message, "-force")
        elif parameters.startswith("-stop"):
            await cmd_fstop(message, parameters[len("-stop"):])
        elif parameters.startswith("-fleave"):
            await cmd_fleave(message, 'all')
        await reply(message, "Shutting down...")
        await client.logout()


    @commands.command('ping', [0, 0], "```\n{0}ping takes no arguments\n\nTests the bot\'s responsiveness.```")
    async def cmd_ping(self, ctx, message, parameters):
        msg = random.choice(lang['ping']).format(
            bot_nick=client.user.display_name, author=message.author.name, p=BOT_PREFIX)
        await reply(message, msg)


    @commands.command('eval', [2, 2], "```\n{0}eval <evaluation string>\n\nEvaluates <evaluation string> using Python\'s eval() function and returns a result. Owner-only.```")
    async def cmd_eval(self, ctx, message, parameters):
        output = None
        parameters = ' '.join(message.content.split(' ')[1:])
        if parameters == '':
            await reply(message, commands['eval'][2].format(BOT_PREFIX))
            return
        try:
            output = eval(parameters)
        except:
            await reply(message, '```\n' + str(traceback.format_exc()) + '\n```')
            traceback.print_exc()
            return
        if asyncio.iscoroutine(output):
            output = await output
        await reply(message, '```py\n' + str(output) + '\n```', cleanmessage=False)


    @commands.command('exec', [2, 2], "```\n{0}exec <exec string>\n\nExecutes <exec string> using Python\'s exec() function. Owner-only.```")
    async def cmd_exec(self, ctx, message, parameters):
        parameters = ' '.join(message.content.split(' ')[1:])
        if parameters == '':
            await reply(message, commands['exec'][2].format(BOT_PREFIX))
            return
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        try:
            exec(parameters)
        except Exception:
            await reply(message, '```py\n{}\n```'.format(traceback.format_exc()))
            return
        finally:
            sys.stdout = old_stdout
        output = str(redirected_output.getvalue())
        if output == '':
            output = ":thumbsup:"
        await client.send_message(message.channel, output)


    @commands.command('async', [2, 2], "```\n{0}async <code>\n\nExecutes <code> as a coroutine.```")
    async def cmd_async(self, ctx, message, parameters, recursion=0):
        if parameters == '':
            await reply(message, commands['async'][2].format(PREFIX))
            return
        env = {'message' : message,
            'parameters' : parameters,
            'recursion' : recursion,
            'client' : client,
            'channel' : message.channel,
            'author' : message.author,
            'server' : message.server}
        env.update(globals())
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        result = None
        exec_string = "async def _temp_exec(self, ctx, ):\n"
        exec_string += '\n'.join(' ' * 4 + line for line in parameters.split('\n'))
        try:
            exec(exec_string, env)
        except Exception:
            traceback.print_exc()
            result = traceback.format_exc()
        else:
            _temp_exec = env['_temp_exec']
            try:
                returnval = await _temp_exec()
                value = redirected_output.getvalue()
                if returnval == None:
                    result = value
                else:
                    result = value + '\n' + str(returnval)
            except Exception:
                traceback.print_exc()
                result = traceback.format_exc()
        finally:
            sys.stdout = old_stdout
        await client.send_message(message.channel, "```py\n{}\n```".format(result))


    @commands.command('help', [0, 0], "```\n{0}help <command>\n\nReturns hopefully helpful information on <command>. Try {0}list for a listing of commands.```")
    async def cmd_help(self, ctx, message, parameters):
        if parameters == '':
            parameters = 'help'
        if parameters in commands:
            await reply(message, commands[parameters][2].format(BOT_PREFIX))
        else:
            await reply(message, 'No help found for command ' + parameters)


    @commands.command('list', [0, 0], "```\n{0}list takes no arguments\n\nDisplays a listing of commands. Try {0}help <command> for help regarding a specific command.```")
    async def cmd_list(self, ctx, message, parameters):
        cmdlist = []
        for key in commands:
            if message.channel.is_private:
                if has_privileges(commands[key][1][1], message):
                    cmdlist.append(key)
            else:
                if has_privileges(commands[key][1][0], message):
                    cmdlist.append(key)
        await reply(message, "Available commands: {}".format(", ".join(sorted(cmdlist))))


    @commands.command('join', [0, 1], "```\n{0}join [<gamemode>]\n\nJoins the game if it has not started yet. Votes for [<gamemode>] if it is given.```", 'j')
    async def cmd_join(self, ctx, message, parameters):
        global wait_timer # ugh globals
        global wait_bucket
        if session[0]:
            return
        if message.author.id in stasis and stasis[message.author.id] > 0:
            await reply(message, "You are in stasis for **{}** game{}. Please do not break rules, idle out or use !leave during a game.".format(
                                    stasis[message.author.id], '' if stasis[message.author.id] == 1 else 's'))
            return
        if len(session[1]) >= MAX_PLAYERS:
            await reply(message, random.choice(lang['maxplayers']).format(MAX_PLAYERS))
            return
        if message.author.id in session[1]:
            await reply(message, random.choice(lang['alreadyin']).format(message.author.name))
        else:
            session[1][message.author.id] = [True, '', '', [], []]
            if len(session[1]) == 1:
                wait_bucket = WAIT_BUCKET_INIT
                wait_timer = datetime.now() + timedelta(seconds=WAIT_AFTER_JOIN)
                client.loop.create_task(game_start_timeout_loop())
                client.loop.create_task(wait_timer_loop())
                await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.idle)
                await send_lobby(random.choice(lang['gamestart']).format(
                                                message.author.name, p=BOT_PREFIX))
            else:
                await client.send_message(message.channel, "**{}** joined the game and raised the number of players to **{}**.".format(
                                                            message.author.name, len(session[1])))
            if parameters:
                await cmd_vote(message, parameters)
            #                            alive, role, action, [templates], [other]
            await client.add_roles(client.get_server(WEREWOLF_SERVER).get_member(message.author.id), PLAYERS_ROLE)
            wait_timer = datetime.now() + timedelta(seconds=WAIT_AFTER_JOIN)
            client.loop.create_task(player_idle(message))


    @commands.command('leave', [0, 1], "```\n{0}leave takes no arguments\n\nLeaves the current game. If you need to leave, please do it before the game starts.```", 'q')
    async def cmd_leave(self, ctx, message, parameters):
        if session[0] and message.author.id in session[1] and session[1][message.author.id][0]:
            if parameters != '-force':
                msg = await client.send_message(message.channel, "Are you sure you want to quit during game? Doing "
                                                                "so will result in {} games of stasis. You may bypass "
                                                                "this confirmation by using `{}leave -force`.".format(
                                                                    QUIT_GAME_STASIS, BOT_PREFIX))
                def check(m):
                    c = m.content.lower()
                    return c in ['yes', 'y', 'no', 'n']
                response = await client.wait_for_message(author=message.author, channel=message.channel, timeout=5, check=check)
                await client.delete_message(msg)
                if not response or response.content.lower() not in ['yes', 'y']:
                    return
            if not session[1][message.author.id][0]:
                # prevent race condition where user runs this command multiple times and then says "yes"
                return
            if session[6] == 'noreveal':
                await send_lobby(random.choice(lang['leavedeathnoreveal']).format(message.author.name))       
            else:
                await send_lobby(random.choice(lang['leavedeath']).format(
                    message.author.name, get_role(message.author.id, 'death')))
            await player_deaths({message.author.id : ('leave', "bot")})
            if message.author.id in stasis:
                stasis[message.author.id] += QUIT_GAME_STASIS
            else:
                stasis[message.author.id] = QUIT_GAME_STASIS
            if session[0] and win_condition() == None:
                await check_traitor()
            await log(1, "{} ({}) QUIT DURING GAME".format(message.author.display_name, message.author.id))
        else:
            if message.author.id in session[1]:
                if session[0]:
                    await reply(message, "wot?")
                    return
                await player_deaths({message.author.id : ('leave', "bot")})
                await send_lobby(random.choice(lang['leavelobby']).format(message.author.name, len(session[1])))
                if len(session[1]) == 0:
                    await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.online)
            else:
                await reply(message, random.choice(lang['notplayingleave']))


    @commands.command('wait', [0, 1], "```\n{0}wait takes no arguments\n\nIncreases the wait time until {0}start may be used.```", 'w')
    async def cmd_wait(self, ctx, message, parameters):
        global wait_bucket
        global wait_timer
        if session[0] or message.author.id not in session[1]:
            return
        if wait_bucket <= 0:
            wait_bucket = 0
            await reply(message, "That command is ratelimited.")
        else:
            wait_timer = max(datetime.now() + timedelta(seconds=EXTRA_WAIT), wait_timer + timedelta(seconds=EXTRA_WAIT))
            wait_bucket -= 1
            await send_lobby("**{}** increased the wait time by {} seconds.".format(message.author.name, EXTRA_WAIT))


    @commands.command('fjoin', [1, 1], "```\n{0}fjoin <mentions of users>\n\nForces each <mention> to join the game.```")
    async def cmd_fjoin(self, ctx, message, parameters):
        if session[0]:
            return
        if parameters == '':
            await reply(message, commands['fjoin'][2].format(BOT_PREFIX))
            return
        raw_members = parameters.split(' ')
        join_list = []
        for member in raw_members:
            if member.strip('<!@>').isdigit():
                join_list.append(member.strip('<!@>'))
            elif '-' in member:
                left = member.split('-')[0]
                right = member.split('-')[1]
                if left.isdigit() and right.isdigit():
                    join_list += list(map(str, range(int(left), int(right) + 1)))
        if join_list == []:
            await reply(message, "ERROR: no valid mentions found")
            return
        join_msg = ""
        for member in sort_players(join_list):
            session[1][member] = [True, '', '', [], []]
            join_msg += "**" + get_name(member) + "** was forced to join the game.\n"
            if client.get_server(WEREWOLF_SERVER).get_member(member):
                await client.add_roles(client.get_server(WEREWOLF_SERVER).get_member(member), PLAYERS_ROLE)
        join_msg += "New player count: **{}**".format(len(session[1]))
        if len(session[1]) > 0:
            await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.idle)
        await client.send_message(message.channel, join_msg)
        await log(2, "{0} ({1}) used FJOIN {2}".format(message.author.name, message.author.id, parameters))


    @commands.command('fleave', [1, 1], "```\n{0}fleave <mentions of users | all>\n\nForces each <mention> to leave the game. If the parameter is all, removes all players from the game.```")
    async def cmd_fleave(self, ctx, message, parameters):
        if parameters == '':
            await reply(message, commands['fleave'][2].format(BOT_PREFIX))
            return
        raw_members = parameters.split(' ')
        leave_list = []
        if parameters == 'all':
            leave_list = list(session[1])
        else:
            for member in raw_members:
                if member.strip('<!@>').isdigit():
                    leave_list.append(member.strip('<!@>'))
                elif '-' in member:
                    left = member.split('-')[0]
                    right = member.split('-')[1]
                    if left.isdigit() and right.isdigit():
                        leave_list += list(map(str, range(int(left), int(right) + 1)))
        if leave_list == []:
            await reply(message, "ERROR: no valid mentions found")
            return
        leave_msg = ""

        for member in sort_players(leave_list):
            if member in list(session[1]):
                if session[0]:
                    if session[6] == 'noreveal':
                        leave_msg += "**" + get_name(member) + "** was forcibly shoved into a fire. The air smells of freshly burnt flesh.\n"
                    else:
                        leave_msg += "**" + get_name(member) + "** was forcibly shoved into a fire. The air smells of freshly burnt **" + get_role(member, 'death') + "**.\n"
                else:
                    leave_msg += "**" + get_name(member) + "** was forced to leave the game.\n"
            if len(session[1]) == 0:
                await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.online)
        leave_dict = {}
        for p in [x for x in sort_players(leave_list) if x in session[1]]:
            leave_dict[p] = ('fleave', "bot")
        await player_deaths(leave_dict)
        if not session[0]:
            leave_msg += "New player count: **{}**".format(len(session[1]))
        await send_lobby(leave_msg)
        await log(2, "{0} ({1}) used FLEAVE {2}".format(message.author.name, message.author.id, parameters))
        if session[0] and win_condition() == None:
            await check_traitor()


    @commands.command('refresh', [1, 1], "```\n{0}refresh [<language file>]\n\nRefreshes the current language's language file from GitHub. Admin only.```")
    async def cmd_refresh(self, ctx, message, parameters):
        global lang
        if parameters == '':
            parameters = MESSAGE_LANGUAGE
        url = "https://raw.githubusercontent.com/belguawhale/Discord-Werewolf/master/lang/{}.json".format(parameters)
        codeset = parameters
        temp_lang, temp_str = get_jsonparsed_data(url)
        if not temp_lang:
            await reply(message, "Could not refresh language {} from Github.".format(parameters))
            return
        with open('lang/{}.json'.format(parameters), 'w', encoding='utf-8') as f:
            f.write(temp_str)
        lang = temp_lang
        await reply(message, 'The messages with language code `' + codeset + '` have been refreshed from GitHub.')


    @commands.command('start', [0, 1], "```\n{0}start takes no arguments\n\nVotes to start the game. A game needs at least " +\
                        str(MIN_PLAYERS) + " players to start.```")
    async def cmd_start(self, ctx, message, parameters):
        if session[0]:
            return
        if message.author.id not in session[1]:
            await reply(message, random.choice(lang['notplayingstart']))
            return
        if len(session[1]) < MIN_PLAYERS:
            await reply(message, random.choice(lang['minplayers']).format(MIN_PLAYERS))
            return
        if session[1][message.author.id][1]:
            return
        if datetime.now() < wait_timer:
            await reply(message, "Please wait at least {} more second{}.".format(
                int((wait_timer - datetime.now()).total_seconds()), '' if int((wait_timer - datetime.now()).total_seconds()) == 1 else 's'))
            return
        session[1][message.author.id][1] = 'start'
        votes = len([x for x in session[1] if session[1][x][1] == 'start'])
        votes_needed = max(2, min(len(session[1]) // 4 + 1, 4))
        if votes < votes_needed:
            await send_lobby("**{}** has voted to start the game. **{}** more vote{} needed.".format(
                message.author.display_name, votes_needed - votes, '' if (votes_needed - votes == 1) else 's'))
        else:
            await run_game()
        if votes == 1:
            await start_votes(message.author.id)


    @commands.command('fstart', [1, 2], "```\n{0}fstart takes no arguments\n\nForces game to start.```")
    async def cmd_fstart(self, ctx, message, parameters):
        if session[0]:
            return
        if len(session[1]) < MIN_PLAYERS:
            await reply(message, random.choice(lang['minplayers']).format(MIN_PLAYERS))
        else:
            await send_lobby("**" + message.author.name + "** forced the game to start.")
            await log(2, "{0} ({1}) FSTART".format(message.author.name, message.author.id))
            await run_game()


    @commands.command('fstop', [1, 1], "```\n{0}fstop [<-force|reason>]\n\nForcibly stops the current game with an optional [<reason>]. Use {0}fstop -force if "
                        "bot errors.```")
    async def cmd_fstop(self, ctx, message, parameters):
        msg = "Game forcibly stopped by **" + message.author.name + "**"
        if parameters == "":
            msg += "."
        elif parameters == "-force":
            if not session[0]:
                return
            msg += ". Here is some debugging info:\n```py\n{0}\n```".format(str(session))
            session[0] = False
            perms = client.get_channel(GAME_CHANNEL).overwrites_for(client.get_server(WEREWOLF_SERVER).default_role)
            perms.send_messages = True
            await client.edit_channel_permissions(client.get_channel(GAME_CHANNEL), client.get_server(WEREWOLF_SERVER).default_role, perms)
            player_dict = {}
            for player in list(session[1]):
                player_dict[player] = ('fstop', "bot")
            await player_deaths(player_dict)
            session[3] = [datetime.now(), datetime.now()]
            session[4] = [timedelta(0), timedelta(0)]
            session[6] = ''
            session[7] = {}
            await send_lobby(msg)
            return
        else:
            msg += " for reason: `" + parameters + "`."

        if not session[0]:
            await reply(message, "There is no currently running game!")
            return
        else:
            await log(2, "{0} ({1}) FSTOP {2}".format(message.author.name, message.author.id, parameters))
        await end_game(msg + '\n\n' + end_game_stats())


    @commands.command('sync', [1, 1], "```\n{0}sync takes no arguments\n\nSynchronizes all player roles and channel permissions with session.```")
    async def cmd_sync(self, ctx, message, parameters):
        for member in client.get_server(WEREWOLF_SERVER).members:
            if member.id in session[1] and session[1][member.id][0]:
                if not PLAYERS_ROLE in member.roles:
                    await client.add_roles(member, PLAYERS_ROLE)
            else:
                if PLAYERS_ROLE in member.roles:
                    await client.remove_roles(member, PLAYERS_ROLE)
        perms = client.get_channel(GAME_CHANNEL).overwrites_for(client.get_server(WEREWOLF_SERVER).default_role)
        if session[0]:
            perms.send_messages = False
        else:
            perms.send_messages = True
        await client.edit_channel_permissions(client.get_channel(GAME_CHANNEL), client.get_server(WEREWOLF_SERVER).default_role, perms)
        await log(2, "{0} ({1}) SYNC".format(message.author.name, message.author.id))
        await reply(message, "Sync successful.")


    @commands.command('op', [1, 1], "```\n{0}op takes no arguments\n\nOps yourself if you are an admin```")
    async def cmd_op(self, ctx, message, parameters):
        await log(2, "{0} ({1}) OP {2}".format(message.author.name, message.author.id, parameters))
        if parameters == "":
            await client.add_roles(client.get_server(WEREWOLF_SERVER).get_member(message.author.id), ADMINS_ROLE)
            await reply(message, ":thumbsup:")
        else:
            member = client.get_server(WEREWOLF_SERVER).get_member(parameters.strip("<!@>"))
            if member:
                if member.id in ADMINS:
                    await client.add_roles(member, ADMINS_ROLE)
                    await reply(message, ":thumbsup:")


    @commands.command('deop', [1, 1], "```\n{0}deop takes no arguments\n\nDeops yourself so you can play with the players ;)```")
    async def cmd_deop(self, ctx, message, parameters):
        await log(2, "{0} ({1}) DEOP {2}".format(message.author.name, message.author.id, parameters))
        if parameters == "":
            await client.remove_roles(client.get_server(WEREWOLF_SERVER).get_member(message.author.id), ADMINS_ROLE)
            await reply(message, ":thumbsup:")
        else:
            member = client.get_server(WEREWOLF_SERVER).get_member(parameters.strip("<!@>"))
            if member:
                if member.id in ADMINS:
                    await client.remove_roles(member, ADMINS_ROLE)
                    await reply(message, ":thumbsup:")


    @commands.command('role', [0, 0], "```\n{0}role [<role | number of players | gamemode>] [<number of players>]\n\nIf a <role> is given, "
                        "displays a description of <role>. If a <number of players> is given, displays the quantity of each "
                        "role for the specified <number of players> for the specified <gamemode>, defaulting to default. If "
                        "only a <gamemode> is given, displays a role guide for <gamemode>. "
                        "If left blank, displays a list of roles.```", 'roles')
    async def cmd_role(self, ctx, message, parameters):
        if parameters == "" and not session[0] or parameters == 'list':
            roles_message = ''
            roles_message += "\n```ini\n[Village Team] " + ", ".join(sort_roles(VILLAGE_ROLES_ORDERED))
            roles_message += "\n[Wolf Team] " + ", ".join(sort_roles(WOLF_ROLES_ORDERED))
            roles_message += "\n[Neutrals] " + ", ".join(sort_roles(NEUTRAL_ROLES_ORDERED))
            roles_message += "\n[Templates] " + ", ".join(sort_roles(TEMPLATES_ORDERED)) + "```"
            await reply(message, roles_message)
            return
        elif parameters == "" and session[0]:
            msg = "**{}** players playing **{}** gamemode:```\n".format(len(session[1]),
            'roles' if session[6].startswith('roles') else session[6])
            if session[6] in ('random',):
                msg += "!role is disabled for the {} gamemode.\n```".format(session[6])
                await reply(message, msg)
                return

            game_roles = dict(session[7])

            msg += '\n'.join(["{}: {}".format(x, game_roles[x]) for x in sort_roles(game_roles)])
            msg += '```'
            await reply(message, msg)
            return
        elif _autocomplete(parameters, roles)[1] == 1:
            role = _autocomplete(parameters, roles)[0]
            await reply(message, "<https://werewolf.miraheze.org/wiki/{}>\n```\nRole name: {}\nTeam: {}\nDescription: {}\n```".format(
                role + "_(role)" if role == "lycan" else role.replace(' ', '_'), role, roles[role][0], roles[role][2]))
            return
        params = parameters.split(' ')
        gamemode = 'default'
        num_players = -1
        choice, num = _autocomplete(params[0], gamemodes)
        if num == 1:
            gamemode = choice

        if params[0].isdigit():
            num_players = params[0]
        elif len(params) == 2 and params[1].isdigit():
            num_players = params[1]
        if num_players == -1:
            if len(params) == 2:
                if params[1] == 'table':
                    # generate role table
                    WIDTH = 20
                    role_dict = dict()
                    for role in gamemodes[gamemode]['roles']:
                        if max(gamemodes[gamemode]['roles'][role]):
                            role_dict.update({role : gamemodes[gamemode]['roles'][role]})
                    role_guide = "Role table for gamemode **{}**:\n".format(gamemode)
                    role_guide += "```\n" + " " * (WIDTH + 2)
                    role_guide += ','.join("{}{}".format(' ' * (2 - len(str(x))), x) for x in range(gamemodes[gamemode]['min_players'], gamemodes[gamemode]['max_players'] + 1)) + '\n'
                    role_guide += '\n'.join(role + ' ' * (WIDTH - len(role)) + ": " + repr(\
                    role_dict[role][gamemodes[gamemode]['min_players'] - MIN_PLAYERS:gamemodes[gamemode]['max_players']]) for role in sort_roles(role_dict))
                    role_guide += "\n```"
                elif params[1] == 'guide':
                    # generate role guide
                    role_dict = gamemodes[gamemode]['roles']
                    prev_dict = dict((x, 0) for x in roles if x != 'villager')
                    role_guide = 'Role guide for gamemode **{}**:\n'.format(gamemode)
                    for i in range(gamemodes[gamemode]['max_players'] - MIN_PLAYERS + 1):
                        current_dict = {}
                        for role in sort_roles(roles):
                            if role == 'villager':
                                continue
                            if role in role_dict:
                                current_dict[role] = role_dict[role][i]
                            else:
                                current_dict[role] = 0
                        # compare previous and current
                        if current_dict == prev_dict:
                            # same
                            continue
                        role_guide += '**[{}]** '.format(i + MIN_PLAYERS)
                        for role in sort_roles(roles):
                            if role == 'villager':
                                continue
                            if current_dict[role] == 0 and prev_dict[role] == 0:
                                # role not in gamemode
                                continue
                            if current_dict[role] > prev_dict[role]:
                                # role increased
                                role_guide += role
                                if current_dict[role] > 1:
                                    role_guide += " ({})".format(current_dict[role])
                                role_guide += ', '
                            elif prev_dict[role] > current_dict[role]:
                                role_guide += '~~{}'.format(role)
                                if prev_dict[role] > 1:
                                    role_guide += " ({})".format(prev_dict[role])
                                role_guide += '~~, '
                        role_guide = role_guide.rstrip(', ') + '\n'
                        # makes a copy
                        prev_dict = dict(current_dict)
                else:
                    role_guide = "Please choose one of the following: " + ', '.join(['guide', 'table'])
            else:
                role_guide = "Please choose one of the following for the third parameter: {}".format(', '.join(['guide', 'table']))
            if not len(role_guide)>2000:
                await reply(message, role_guide)
            else:
                pass # temporary until a solution is found
        else:
            num_players = int(num_players)
            if num_players in range(gamemodes[gamemode]['min_players'], gamemodes[gamemode]['max_players'] + 1):
                if gamemode in ('random',):
                    msg = "!role is disabled for the **{}** gamemode.".format(gamemode)
                else:
                    msg = "Roles for **{}** players in gamemode **{}**:```\n".format(num_players, gamemode)
                    game_roles = get_roles(gamemode, num_players)
                    msg += '\n'.join("{}: {}".format(x, game_roles[x]) for x in sort_roles(game_roles))
                    msg += '```'
                await reply(message, msg)
            else:
                await reply(message, "Please choose a number of players between " + str(gamemodes[gamemode]['min_players']) +\
                " and " + str(gamemodes[gamemode]['max_players']) + ".")


    async def _send_role_info(self, ctx, player, sendrole=True):
        if session[0] and player in session[1]:
            member = client.get_server(WEREWOLF_SERVER).get_member(player)
            if member and session[1][player][0]:
                role = get_role(player, 'role') if get_role(player, 'role') not in ['amnesiac', 'vengeful ghost', 'time lord'] else "villager"
                templates = get_role(player, 'templates')
                if member and session[1][player][0]:
                    try:
                        if sendrole:
                            await client.send_message(member, "Your role is **" + role + "**. " + roles[role][2] + '\n')
                        msg = []
                        living_players = [x for x in session[1] if session[1][x][0]]
                        living_players_string = ['{} ({})'.format(get_name(x), x) for x in living_players]
                        if role in COMMANDS_FOR_ROLE['kill'] and roles[role][0] == 'wolf':
                            if 'angry' in session[1][player][4]:
                                num_kills = session[1][player][4].count('angry')
                                msg.append("You are **angry** tonight, and may kill {} targets by using `kill {}`.\n".format(
                                    num_kills + 1, ' AND '.join('player' + str(x + 1) for x in range(num_kills + 1))))
                        if roles[role][0] == 'wolf' and role != 'cultist' and (role != 'minion' or str(session[4][1]) == "0:00:00"):
                            living_players_string = []
                            for plr in living_players:
                                temprole = get_role(plr, 'role')
                                temptemplates = get_role(plr, 'templates')
                                role_string = []
                                if 'cursed' in temptemplates and role != 'minion':
                                    role_string.append('cursed')
                                if roles[temprole][0] == 'wolf' and temprole not in ['minion', 'cultist']:
                                    role_string.append(temprole)
                                living_players_string.append("{} ({}){}".format(get_name(plr), plr,
                                ' ({})'.format(' '.join(role_string)) if role_string else ''))
                        if role == 'succubus':
                            living_players_string = []
                            for plr in living_players:
                                temprole = get_role(plr, 'role')
                                role_string = []
                                if 'entranced' in session[1][plr][4]:
                                    role_string.append('entranced')
                                if temprole == 'succubus':
                                    role_string.append(temprole)
                                living_players_string.append("{} ({}){}".format(get_name(plr), plr,
                                ' ({})'.format(' '.join(role_string)) if role_string else ''))
                        if role == 'piper':
                            living_players_string = []
                            for plr in living_players:
                                temprole = get_role(plr, 'role')
                                role_string = []
                                if 'charmed' in session[1][plr][4]:
                                    role_string.append('charmed')
                                if temprole == 'piper':
                                    role_string.append(temprole)
                                living_players_string.append("{} ({}){}".format(get_name(plr), plr,
                                ' ({})'.format(' '.join(role_string)) if role_string else ''))
                        if role in ['shaman', 'wolf shaman']:
                            totem = ''
                            if session[1][player][2] in totems:
                                totem = session[1][player][2]
                            elif [x for x in session[1][player][4] if x.startswith("totem:")]:
                                totem = [x.split(':')[1] for x in session[1][player][4] if x.startswith("totem:")].pop()
                            if totem:
                                msg.append("You have the **{}**. {}\n".format(totem.replace('_', ' '), totems[totem]))
                        if role in ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic', 'traitor', 'sorcerer', 'seer',
                                    'oracle', 'shaman', 'harlot', 'hunter', 'augur', 'detective', 'guardian angel',
                                    'crazed shaman', 'succubus', 'hag', 'piper', 'bodyguard', 'warlock']:
                            msg.append("Living players: ```basic\n" + '\n'.join(living_players_string) + '\n```')
                        #mystic stuff/wolf mystic stuff
                        if role == 'mystic':
                            wolfcount = 0
                            for player in session[1]:
                                if get_role(player, 'actualteam') == 'wolf' and session[1][player][0]:
                                    wolfcount += 1
                            try:
                                if member:
                                    if "silence_totem2" in session[1][player][4]:
                                        await client.send_message(member, "You are silenced and unable to sense anything of significance.".format(wolfcount))
                                    else:
                                        await client.send_message(member, "You sense that there are **{}** wolves.".format(wolfcount))
                            except discord.Forbidden:
                                pass
                        if role == 'wolf mystic':
                            vilcount = 0
                            for player in session[1]:
                                if ((get_role(player, 'actualteam') == 'village' and get_role(player, 'role') != 'villager') or get_role(player, 'role') == ('fool' or 'monster' or 'succubus' or  'piper' or 'demoniac')) and session[1][player][0]:
                                    vilcount += 1
                            try:
                                if member:
                                    if "silence_totem2" in session[1][player][4]:
                                        await client.send_message(member, "You are silenced and unable to sense anything of significance.".format(wolfcount))
                                    else:
                                        await client.send_message(member, "You sense that there are **{}** villagers.".format(vilcount))
                            except discord.Forbidden:
                                pass
                        #turncoat being told when they can turn
                        if role == 'turncoat' and 'sided2' not in session[1][player][4]:
                            await client.send_message(member, "You can switch sides tonight.")
                        if 'gunner' in templates:
                            msg.append("You have a gun and **{}** bullet{}. Use the command "
                                    "`{}role gunner` for more information.".format(
                                session[1][player][4].count('bullet'), '' if session[1][player][4].count('bullet') == 1 else 's',
                                BOT_PREFIX))
                        if 'sharpshooter' in templates:
                            msg.append("You have a gun and **{}** bullet{}. Use the command "
                                    "`{}role sharpshooter` for more information.".format(
                                session[1][player][4].count('bullet'), '' if session[1][player][4].count('bullet') == 1 else 's',
                                BOT_PREFIX))
                        if 'assassin' in templates:
                            target = ""
                            for o in session[1][player][4]:
                                if o.startswith("assassinate:"):
                                    target = o.split(":")[1]
                            if target:
                                if role == 'village drunk':
                                    msg.append("In your drunken stupor you have selected **{0}** as your target. Use the command `{1}role assassin` for more information.".format(get_name(target), BOT_PREFIX))
                                else:
                                    msg.append("Your target is **{0}**. Use the command `{1}role assassin`"
                                    "for more information.".format(get_name(target), BOT_PREFIX))
                            else:
                                msg.append("You are an **assassin**, and wish to spread chaos. Type `target <player>` to make them your target. If you die, you take them with you, but if they die, you may choose another target.\nLiving players: ```basic\n" + '\n'.join(living_players_string) + '\n```')
                        if role == 'matchmaker' and sendrole:
                            msg.append("Living players: ```basic\n" + '\n'.join(living_players_string) + '\n```')
                        if role == 'minion' and str(session[4][1]) == "0:00:00":
                            msg.append("Living players: ```basic\n" + '\n'.join(living_players_string) + '\n```')
                        if msg:
                            await client.send_message(member, '\n'.join(msg))
                    except discord.Forbidden:
                        await send_lobby(member.mention + ", you cannot play the game if you block me")
            elif member and get_role(player, 'role') == 'vengeful ghost' and [x for x in session[1][player][4] if x.startswith("vengeance:")]:
                try:
                    against = 'wolf'
                    if [x for x in session[1][player][4] if x.startswith("vengeance:")]:
                        against = [x.split(':')[1] for x in session[1][player][4] if x.startswith('vengeance:')].pop()
                    await client.send_message(member, "You are a **vengeful ghost**, sworn to take revenge on the {0} that you believe killed you. You must kill one of them with `kill <player>` tonight. If you do not, one of them will be selected at random.".format('wolves' if against == 'wolf' else 'villagers'))
                    living_players = [x for x in session[1] if session[1][x][0] if roles[get_role(x, "role")][0] == against]
                    living_players_string = ['{} ({})'.format(get_name(x), x) for x in living_players]
                    await client.send_message(member, "Living players: ```basic\n" + '\n'.join(living_players_string) + '\n```')
                except discord.Forbidden:
                    pass
            

def setup(bot):
    bot.add_cog(Werewolf(bot))