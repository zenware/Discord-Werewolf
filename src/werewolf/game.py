import datetime
import locale
import textwrap

class WerewolfGameEngine:
    """This object carries the state of a game ofr Werewolf"""
    
    def __init__(self):
        self.players = [] # TODO: Perhaps this should be a dict
        self.playing = False # True while the game is not paused
        self.day = False # True while it is daytime
        self.gamemode = "default" # TODO: There should be a selection of supported gamemode objects with a default

        # Use the first two characters from the system locale to determine the langauge.
        self.langauge = self._load_language(locale.getdefaultlocale()[0].split("_")[0])

        # TODO: Game Day Cycles might be their own object, and
        # even if not, some lifecycle methods should likely control these values
        self.night_start = datetime.timedelta(0)
        self.day_start = datetime.timedelta(0)
        self.night_elapsed = datetime.timedelta(0)
        self.day_elapsed = datetime.timedelta(0)

    def pretty_game_stats(self):
        """Return the 'relevant' game stats as a string
        
        This is a nice pretty string so you can print it to console or send it as a message.
        """
        num_players = len(self.players)
        if num_players == 0:
            return f"There is currently no active game. Try {BOT_PREFIX}join to start a new game!"

        if not self.playing:
            # If the game isn't currently running, list out the players...
            return f"{num_players} in lobby: ```\n{'\n'.join(self.players)}\n```"

        time = "day" if self.day else "night"
        # TODO: Implement the __str__ method of the gamemodes to show a nice name.
        # NOTE: This message in the original implementation is complicated enough it might warrant a templating system.
        # Jinja2?
        output_string = textwrap.dedent(
        f"""
        It is now **{time}time**. Using the **{self.gamemode}** gamemode.
        """)
        return output_string

    def _load_language(self, language):
        file = 'lang/{}.json'.format(language)
        if not os.path.isfile(file):
            file = 'lang/en.json'
            print("Could not find language file {}.json, fallback on en.json".format(language))
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def run_game(self):
        await client.change_presence(game=client.get_server(WEREWOLF_SERVER).me.game, status=discord.Status.dnd)
        session[0] = True
        session[2] = False
        if session[6] == '':
            vote_dict = {}
            for player in session[1]:
                vote = session[1][player][2]
                if vote in vote_dict:
                    vote_dict[vote] += 1
                elif vote != '':
                    vote_dict[vote] = 1
            for gamemode in vote_dict:
                if vote_dict[gamemode] >= len(session[1]) // 2 + 1:
                    session[6] = gamemode
            if not session[6]:
                #setting the mode taking votes and chances into consideration for probabilities
                #aleatoire, charming, default, evilvillage, foolish, lycan, mad, mudkip, and noreveal
                ALEATOIRE = gamemodes['aleatoire']['chance'] 
                if len(session[1]) < gamemodes['aleatoire']['min_players'] or len(session[1]) > gamemodes['aleatoire']['max_players']:
                    ALEATOIRE = 0
                elif 'aleatoire' in vote_dict:
                    ALEATOIRE += int((vote_dict['aleatoire']/len(session[1])) * 200)
                CHARMING = gamemodes['charming']['chance'] 
                if len(session[1]) < gamemodes['charming']['min_players'] or len(session[1]) > gamemodes['charming']['max_players']:
                    CHARMING = 0
                elif 'charming' in vote_dict:
                    CHARMING += int((vote_dict['charming']/len(session[1])) * 200)
                DEFAULT = gamemodes['default']['chance'] 
                if len(session[1]) < gamemodes['default']['min_players'] or len(session[1]) > gamemodes['default']['max_players']:
                    DEFAULT = 0
                elif 'default' in vote_dict:
                    DEFAULT += int((vote_dict['default']/len(session[1])) * 200)
                EVIL = gamemodes['evilvillage']['chance'] 
                if len(session[1]) < gamemodes['evilvillage']['min_players'] or len(session[1]) > gamemodes['evilvillage']['max_players']:
                    EVIL = 0
                elif 'evilvillage' in vote_dict:
                    EVIL += int((vote_dict['evilvillage']/len(session[1])) * 200)
                FOOLISH = gamemodes['foolish']['chance'] 
                if len(session[1]) < gamemodes['foolish']['min_players'] or len(session[1]) > gamemodes['foolish']['max_players']:
                    FOOLISH = 0
                elif 'foolish' in vote_dict:
                    FOOLISH += int((vote_dict['foolish']/len(session[1])) * 200)
                LYCAN = gamemodes['lycan']['chance'] 
                if len(session[1]) < gamemodes['lycan']['min_players'] or len(session[1]) > gamemodes['lycan']['max_players']:
                    LYCAN = 0
                elif 'lycan' in vote_dict:
                    LYCAN += int((vote_dict['lycan']/len(session[1])) * 200)
                MAD = gamemodes['mad']['chance'] 
                if len(session[1]) < gamemodes['mad']['min_players'] or len(session[1]) > gamemodes['mad']['max_players']:
                    MAD = 0
                elif 'mad' in vote_dict:
                    MAD += int((vote_dict['mad']/len(session[1])) * 200)
                MUDKIP = gamemodes['mudkip']['chance'] 
                if len(session[1]) < gamemodes['mudkip']['min_players'] or len(session[1]) > gamemodes['mudkip']['max_players']:
                    MUDKIP = 0
                elif 'mudkip' in vote_dict:
                    MUDKIP += int((vote_dict['mudkip']/len(session[1])) * 200)
                NOREVEAL = gamemodes['noreveal']['chance'] 
                if len(session[1]) < gamemodes['noreveal']['min_players'] or len(session[1]) > gamemodes['noreveal']['max_players']:
                    NOREVEAL = 0
                elif 'noreveal' in vote_dict:
                    NOREVEAL += int((vote_dict['noreveal']/len(session[1])) * 200)
                mode = (random.choice((['aleatoire'] * ALEATOIRE + ['charming'] * CHARMING + ['default'] * DEFAULT + ['evilvillage'] * EVIL\
                + ['foolish'] * FOOLISH + ['lycan'] * LYCAN + ['mad'] * MAD + ['mudkip'] * MUDKIP + ['noreveal'] * NOREVEAL)))
                session[6] = mode
        for player in session[1]:
            session[1][player][1] = ''
            session[1][player][2] = ''
        perms = client.get_channel(GAME_CHANNEL).overwrites_for(client.get_server(WEREWOLF_SERVER).default_role)
        perms.send_messages = False
        await client.edit_channel_permissions(client.get_channel(GAME_CHANNEL), client.get_server(WEREWOLF_SERVER).default_role, perms)
        if not get_roles(session[6], len(session[1])):
            session[6] = 'default' # Fallback if invalid number of players for gamemode or invalid gamemode somehow

        for stasised in [x for x in stasis if stasis[x] > 0]:
            stasis[stasised] -= 1
        await send_lobby("<@{}>, Welcome to Werewolf, the popular detective/social party game (a theme of Mafia). "
                                "Using the **{}** game mode with **{}** players.\nAll players check for PMs from me for instructions. "
                                "If you did not receive a pm, please let {} know.".format('> <@'.join(sort_players(session[1])),
                                'roles' if session[6].startswith('roles') else session[6], len(session[1]),
                                client.get_server(WEREWOLF_SERVER).get_member(OWNER_ID).name))
        for i in range(RETRY_RUN_GAME):
            try:
                if datetime.now().date() == __import__('datetime').date(2018, 4, 1):
                    gamemode = "mudkip" if session[6] == 'default' else ('default' if session[6] == 'mudkip' else session[6])
                else:
                    gamemode = session[6]
                await assign_roles(gamemode)
                break
            except:
                await log(2, "Role attribution failed with error: ```py\n{}\n```".format(traceback.format_exc()))
        else:
            msg = await send_lobby("<@{}>, role attribution failed 3 times. Cancelling game. "
                                                                            "Here is some debugging info:```py\n{}\n```".format(
                    '> <@'.join(sort_players(session[1])), session))
            await cmd_fstop(msg, '-force')
            return

        for i in range(RETRY_RUN_GAME):
            try:
                if i == 0:
                    await game_loop()
                else:
                    await game_loop(session)
                break
            except:
                await send_lobby("<@{}>, game loop broke. Attempting to resume game...".format(
                    '> <@'.join(sort_players(session[1])), session))
                await log(3, "Game loop broke with error: ```py\n{}\n```".format(traceback.format_exc()))
        else:
            msg = await send_lobby("<@{}>, game loop broke 3 times. Cancelling game.".format(
                    '> <@'.join(sort_players(session[1])), session))
            await cmd_fstop(msg, '-force')


    def gameloop(self):
        if ses:
            await send_lobby("<@{}>, Welcome to Werewolf, the popular detective/social party game (a theme of Mafia). "
                                "Using the **{}** game mode with **{}** players.\nAll players check for PMs from me for instructions. "
                                "If you did not receive a pm, please let {} know.".format('> <@'.join(sort_players(session[1])),
                                'roles' if session[6].startswith('roles') else session[6], len(session[1]),
                                client.get_server(WEREWOLF_SERVER).get_member(OWNER_ID).name))
            globals()['session'] = ses
        await log(1, "Game object: ```py\n{}\n```".format(session))
        night = 1
        global day_warning
        global day_timeout
        global night_warning
        global night_timeout
        # GAME START
        while win_condition() == None and session[0]:
            if not session[2]: # NIGHT
                session[3][0] = datetime.now()
                log_msg = ['SUNSET LOG:']
                num_kills = 1
                for player in session[1]:
                    member = client.get_server(WEREWOLF_SERVER).get_member(player)
                    role = get_role(player, 'role')
                    if "silence_totem2" not in session[1][player][4]:
                        if role in ['shaman', 'crazed shaman', 'wolf shaman'] and session[1][player][0]:
                            if role == 'shaman':
                                if session[6] == "mudkip":
                                    session[1][player][2] = random.choice(["pestilence_totem", "death_totem"]) if not night == 1 else "death_totem"
                                elif session[6] == 'aleatoire':
                                    #protection (40%), death (20%), retribution (20%), silence (10%), desperation (5%), pestilence (5%).
                                    session[1][player][2] = random.choice(["protection_totem"] * 8 + ["death_totem"] * 4 + ["retribution_totem"] * 4 + ["silence_totem"] * 2 + ["desperation_totem"] + ["pestilence_totem"])
                                else:
                                    session[1][player][2] = random.choice(SHAMAN_TOTEMS)
                            elif role == 'wolf shaman':
                                if session[6] == "mudkip":
                                    session[1][player][4].append("totem:{}".format(random.choice(["protection_totem", "misdirection_totem"])))
                                else:
                                    session[1][player][4].append("totem:{}".format(random.choice(WOLF_SHAMAN_TOTEMS)))
                            elif role == 'crazed shaman':
                                session[1][player][2] = random.choice(list(totems))
                            log_msg.append("{} ({}) HAS {}".format(get_name(player), player, (session[1][player][2] if role != "wolf shaman" else [x.split(":")[1] for x in session[1][player][4] if x.startswith("totem:")].pop())))
                        elif role == 'doomsayer':
                            session[1][player][4].append('doom:{}'.format(random.choice(['sick', 'lycan', 'death'])))
                        elif role == 'piper':
                            session[1][player][4].append('charm')
                    else:
                        if role in ['shaman', 'crazed shaman', 'piper'] and session[1][player][0]:
                            session[1][player][2] = player
                    if role == 'hunter' and session[1][player][0] and 'hunterbullet' not in session[1][player][4]:
                        session[1][player][2] = player
                    if night == 1:
                        await _send_role_info(player)
                    else:
                        await _send_role_info(player, sendrole=False)        
                await log(1, '\n'.join(log_msg))
                
                session[3][0] = datetime.now()
                await send_lobby("It is now **nighttime**.")
                warn = False
                # NIGHT LOOP
                while win_condition() == None and not session[2] and session[0]:
                    end_night = True
                    wolf_kill_dict = {}
                    num_wolves = 0
                    for player in session[1]:
                        role = get_role(player, 'role')
                        templates = get_role(player, 'templates')
                        if session[1][player][0]:
                            if role in ['wolf', 'werecrow', 'doomsayer', 'werekitten', 'wolf shaman', 'wolf mystic', 'sorcerer',
                                        'seer', 'oracle', 'harlot', 'hunter', 'augur',
                                        'guardian angel', 'succubus', 'hag', 'warlock', 'bodyguard', 'turncoat'] and 'silence_totem2' not in session[1][player][4]:
                                end_night = end_night and (session[1][player][2] != '')
                            if role in ['shaman', 'crazed shaman']:
                                end_night = end_night and (session[1][player][2] in session[1])
                            if role == "wolf shaman":
                                end_night = end_night and not [x for x in session[1][player][4] if x.startswith("totem:")]
                            if role == 'matchmaker':
                                end_night = end_night and 'match' not in session[1][player][4]
                            if role == 'clone':
                                end_night = end_night and 'clone' not in session[1][player][4]
                            if role == 'piper':
                                end_night = end_night and 'charm' not in session[1][player][4]
                            if "assassin" in templates:
                                end_night = end_night and [x for x in session[1][player][4] if x.startswith("assassinate:")]
                            if role == 'doomsayer':
                                end_night = end_night and not [x for x in session[1][player][4] if x.startswith("doom:")]
                            if roles[role][0] == 'wolf' and role in COMMANDS_FOR_ROLE['kill']:
                                num_wolves += 1
                                num_kills = session[1][player][4].count('angry') + 1
                                t = session[1][player][2]
                                # if no target then t == '' and that will be a key in wolf_kill_dict
                                targets = t.split(',')
                                for target in targets:
                                    try:
                                        wolf_kill_dict[target] += 1
                                    except KeyError:
                                        wolf_kill_dict[target] = 1
                        if role == "vengeful ghost" and [x for x in session[1][player][4] if x.startswith("vengeance:")] and not session[1][player][0]:
                            end_night = end_night and session[1][player][2] != ''
                    end_night = end_night and len(wolf_kill_dict) == num_kills
                    for t in wolf_kill_dict:
                        end_night = end_night and wolf_kill_dict[t] == num_wolves
                        # night will only end if all wolves select same target(s)
                    end_night = end_night or (datetime.now() - session[3][0]).total_seconds() > night_timeout
                    if end_night:
                        session[2] = True
                        session[3][1] = datetime.now() # attempted fix for using !time right as night ends
                    if (datetime.now() - session[3][0]).total_seconds() > night_warning and warn == False:
                        warn = True
                        await send_lobby("**A few villagers awake early and notice it is still dark outside. "
                                                "The night is almost over and there are still whispers heard in the village.**")
                    await asyncio.sleep(0.1)
                night_elapsed = datetime.now() - session[3][0]
                session[4][0] += night_elapsed

                # BETWEEN NIGHT AND DAY
                session[3][1] = datetime.now() # fixes using !time screwing stuff up
                killed_msg = ''
                killed_dict = {}
                for player in session[1]:
                    if "blessed" in get_role(player, 'templates'):
                        killed_dict[player] = -1
                    else:
                        killed_dict[player] = 0
                killed_players = []
                alive_players = [x for x in session[1] if (session[1][x][0] or (get_role(x, 'role') == "vengeful ghost" and [a for a in session[1][x][4] if a.startswith("vengeance:")]))]
                log_msg = ["SUNRISE LOG:"]
                if session[0]:
                    for player in alive_players:
                        role = get_role(player, 'role')
                        templates = get_role(player, 'templates')
                        member = client.get_server(WEREWOLF_SERVER).get_member(player)
                        if "silence_totem2" in session[1][player][4] and (role != 'matchmaker'):
                            if "assassin" in templates and not [x for x in session[1][player][4] if x.startswith("assassinate:")]:
                                if "misdirection_totem2" in session[1][player][4]:
                                    target = misdirect(player)
                                else:
                                    target = random.choice([x for x in alive_players if x != player and "luck_totem2" not in session[1][x][4]])
                                session[1][player][4].append("assassinate:{}".format(target))
                                log_msg.append("{0} ({1}) TARGET RANDOMLY {2} ({3})".format(get_name(player), player, get_name(target), target))

                                if member:
                                    try:
                                        await client.send_message(member, "Because you forgot to select a target at night, you are now targeting **{0}**.".format(get_name(target)))
                                    except discord.Forbidden:
                                        pass
                            continue
                        if role == 'doomsayer':
                            session[1][player][4] = [x for x in session[1][player][4] if not x.startswith('doom:')]
                        if role == 'piper':
                            session[1][player][4] = [x for x in session[1][player][4] if not x == 'charm']
                        if (role in ['shaman', 'crazed shaman'] and session[1][player][2] in totems) or (role == "wolf shaman" and [x for x in session[1][player][4] if x.startswith("totem:")]):
                            if "misdirection_totem2" in session[1][player][4]:
                                totem_target = misdirect(player)
                            else:
                                totem_target = random.choice([x for x in alive_players if x != player and "luck_totem2" not in session[1][x][4]])
                            if role in ['shaman', 'crazed shaman']:
                                totem = session[1][player][2]
                            else:
                                totem = [x for x in session[1][player][4] if x.startswith("totem:")][0].split(":")[1]
                            session[1][totem_target][4].append(totem)
                            if role in ['shaman', 'crazed shaman']:
                                session[1][player][2] = totem_target
                            else:
                                session[1][player][4] = [x for x in session[1][player][4] if not x.startswith("totem:")]
                            session[1][player][4] = [x for x in session[1][player][4] if not x.startswith("lasttarget")] + ["lasttarget:{}".format(totem_target)]
                            log_msg.append(player + '\'s ' + totem + ' given to ' + totem_target)
                            if member:
                                try:
                                    random_given = "wtf? this is a bug; pls report to admins"
                                    if role in ['shaman', 'wolf shaman']:
                                        random_given = "Because you forgot to give your totem out at night, your **{0}** was randomly given to **{1}**.".format(
                                            totem.replace('_', ' '), get_name(totem_target))
                                    elif role == 'crazed shaman':
                                        random_given = "Because you forgot to give your totem out at night, your totem was randomly given to **{0}**.".format(get_name(totem_target))
                                    await client.send_message(member, random_given)
                                except discord.Forbidden:
                                    pass
                        elif role == 'matchmaker' and 'match' in session[1][player][4] and str(session[4][1]) == "0:00:00":
                            trycount = 0
                            alreadytried = []
                            while True:
                                player1 = random.choice([x for x in session[1] if session[1][x][0]])
                                player2 = random.choice([x for x in session[1] if session[1][x][0] and x != player1])
                                if not ("lover:" + player2 in session[1][player1][4] or "lover:" + player1 in session[1][player2][4]):
                                    session[1][player][4].remove('match')
                                    session[1][player1][4].append('lover:' + player2)
                                    session[1][player2][4].append('lover:' + player1)
                                    try:
                                        await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(player1),
                                                            "You are in love with **{0}**. If that player dies for any reason, the pain will be too much for you to bear and you will commit suicide.".format(
                                                                get_name(player2)))
                                    except:
                                        pass
                                    try:
                                        await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(player2),
                                                            "You are in love with **{0}**. If that player dies for any reason, the pain will be too much for you to bear and you will commit suicide.".format(
                                                                get_name(player1)))
                                    except:
                                        pass
                                    await log(1, "{0} ({1}) MATCH {2} ({3}) AND {4} ({5})".format(get_name(player), player, get_name(player1), player1, get_name(player2), player2))
                                    break
                                elif [player1 + player2] not in alreadytried:
                                    trycount += 1
                                    alreadytried.append([player1 + player2])
                                if trycount >= (len([x for x in session[1] if session[1][x][0]])*(len([x for x in session[1] if session[1][x][0]]) - 1)): #all possible lover sets are done
                                    break
                            try:
                                await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(player),
                                                        "Because you forgot to choose lovers at night, two lovers have been selected for you.")
                            except:
                                pass
                        elif role == 'harlot' and session[1][player][2] == '':
                            session[1][player][2] = player
                            log_msg.append("{0} ({1}) STAY HOME".format(get_name(player), player))
                            if member:
                                try:
                                    await client.send_message(member, "You will stay home tonight.")
                                except discord.Forbidden:
                                    pass
                        elif role == 'succubus' and session[1][player][2] == '':
                            session[1][player][2] = player
                            log_msg.append("{0} ({1}) STAY HOME".format(get_name(player), player))
                            if member:
                                try:
                                    await client.send_message(member, "You have chosen to not entrance anyone tonight.")
                                except discord.Forbidden:
                                    pass
                        elif role == 'hunter' and session[1][player][2] == '':
                            session[1][player][2] = player
                            log_msg.append("{0} ({1}) PASS".format(get_name(player), player))
                            if member:
                                try:
                                    await client.send_message(member, "You have chosen to not kill anyone tonight.")
                                except discord.Forbidden:
                                    pass
                                    
                        elif role == 'guardian angel' and session[1][player][2] in ['pass', '']:
                            session[1][player][2] = ''
                            session[1][player][4][:] = [x for x in session[1][player][4] if not x.startswith('lasttarget:')]
                            # clear previous target since no target selected
                            log_msg.append("{0} ({1}) NO GUARD".format(get_name(player), player))
                            if member and not session[1][player][2]:
                                try:
                                    await client.send_message(member, "You have chosen to not guard anyone tonight.")
                                except discord.Forbidden:
                                    pass
                                    
                        elif role == 'vengeful ghost' and [x for x in session[1][player][4] if x.startswith('vengeance:')] and not session[1][player][0] and session[1][player][2] == '' and 'consecrated' not in session[1][player][4] and 'driven' not in session[1][player][4]:
                            against = 'wolf'
                            if [x for x in session[1][player][4] if x.startswith("vengeance:")]:
                                against = [x.split(':')[1] for x in session[1][player][4] if x.startswith('vengeance:')].pop()
                            if "misdirection_totem2" in session[1][player][4]:
                                target = misdirect(player, alive_players=[x for x in alive_players if x != player and get_role(x, 'actualteam') == against and 'luck_totem2' not in session[1][x][4]])
                            else:
                                target = random.choice([x for x in alive_players if x != player and "luck_totem2" not in session[1][x][4] and get_role(x, 'actualteam') == against])
                            session[1][player][2] = target
                            log_msg.append("{0} ({1}) VENGEFUL KILL {2} ({3})".format(get_name(player), player, get_name(target), target))
                        #randomly choose clone targets if unchosen
                        elif role == 'clone' and 'clone' in session[1][player][4]:
                            target = random.choice([x for x in alive_players if x != player])
                            session[1][player][4].append("clone:{}".format(target))
                            if member:
                                try:
                                    await client.send_message(member, "Because you did not choose someone to clone, you are cloning **{}**. If they die you will take their role.".format(get_name(target)))
                                except discord.Forbidden:
                                    pass
                            session[1][player][4].remove('clone')
                            await log(1, "{0} ({1}) CLONE TARGET {2} ({3})".format(get_name(player), player, get_name(target), target))
                            
                        #turncoat siding
                        elif role == 'turncoat' and session[1][player][2]:
                            if session[1][player][2] == 'wolves':
                                session[1][player][4].append('sided')
                                session[1][player][4].append('side:wolves')
                                if 'side:villagers' in session[1][player][4]:
                                    session[1][player][4].remove('side:villagers')
                            elif session[1][player][2] == 'villagers':
                                session[1][player][4].append('sided')
                                session[1][player][4].append('side:villagers')
                                if 'side:wolves' in session[1][player][4]:
                                    session[1][player][4].remove('side:wolves')
                        
                        if "assassin" in templates and not [x for x in session[1][player][4] if x.startswith("assassinate:")]:
                            if "misdirection_totem2" in session[1][player][4]:
                                target = misdirect(player)
                            else:
                                target = random.choice([x for x in alive_players if x != player and "luck_totem2" not in session[1][x][4]])
                            session[1][player][4].append("assassinate:{}".format(target))
                            log_msg.append("{0} ({1}) TARGET RANDOMLY {2} ({3})".format(get_name(player), player, get_name(target), target))
                            if member:
                                try:
                                    await client.send_message(member, "Because you forgot to select a target at night, you are now targeting **{0}**.".format(get_name(target)))
                                except discord.Forbidden:
                                    pass

                # BELUNGA
                for player in [x for x in session[1] if session[1][x][0]]:
                    for i in range(session[1][player][4].count('belunga_totem')):
                        session[1][player][4].append(random.choice(list(totems) + ['belunga_totem', 'bullet']))
                        if random.random() < 0.1 and ('gunner' not in get_role(player, 'templates') or 'sharpshooter' not in get_role(player, 'templates')):
                            session[1][player][3].append('gunner')

                # Wolf kill
                wolf_votes = {}
                wolf_killed = []
                gunner_revenge = []
                wolf_deaths = []
                wolf_turn = []

                for player in alive_players:
                    if roles[get_role(player, 'role')][0] == 'wolf' and get_role(player, 'role') in COMMANDS_FOR_ROLE['kill']:
                        for t in session[1][player][2].split(','):
                            if t in wolf_votes:
                                wolf_votes[t] += 1
                            elif t != "":
                                wolf_votes[t] = 1
                if wolf_votes != {}:
                    sorted_votes = sorted(wolf_votes, key=lambda x: wolf_votes[x], reverse=True)
                    wolf_killed = sort_players(sorted_votes[:num_kills])
                    log_msg.append("WOLFKILL: " + ', '.join('{} ({})'.format(get_name(x), x) for x in wolf_killed))
                    for k in wolf_killed:
                        if get_role(k, 'role') == 'harlot' and session[1][k][2] != k:
                            killed_msg += "The wolves' selected victim was not at home last night, and avoided the attack.\n"
                        elif get_role(k, 'role') == 'monster':
                            pass
                        else:
                            killed_dict[k] += 1
                            wolf_deaths.append(k)

                # Guardian Angel stuff
                guarded = []
                guardeded = [] # like protect_totemed

                for angel in [x for x in alive_players if get_role(x, 'role') == 'guardian angel']:
                    target = session[1][angel][2]
                    if target: # GA makes more sense working on target even if they are harlot not at home
                        killed_dict[target] -= 50
                        guarded.append(target)

                # Harlot stuff
                for harlot in [x for x in alive_players if get_role(x, 'role') == 'harlot']:
                    visited = session[1][harlot][2]
                    if visited != harlot:
                        if visited in wolf_killed and not ('protection_totem' in session[1][visited][4] or 'blessed' in session[1][visited][4] or harlot in guarded):
                            killed_dict[harlot] += 1
                            killed_msg += "**{}**, a **harlot**, made the unfortunate mistake of visiting the victim's house last night and is now dead.\n".format(get_name(harlot))
                            wolf_deaths.append(harlot)
                        elif get_role(visited, 'role') in ACTUAL_WOLVES:
                            killed_dict[harlot] += 1
                            killed_msg += "**{}**, a **harlot**, made the unfortunate mistake of visiting a wolf's house last night and is now dead.\n".format(get_name(harlot))
                            wolf_deaths.append(harlot)

                # Succubus stuff
                for succubus in [x for x in alive_players if get_role(x, 'role') == 'succubus']:
                    visited = session[1][succubus][2]
                    if visited != succubus:
                        if visited in wolf_killed and not ('protection_totem' in session[1][visited][4] or 'blessed' in session[1][visited][4] or succubus in guarded):
                            killed_dict[succubus] += 1
                            killed_msg += "**{}**, a **succubus**, made the unfortunate mistake of visiting the victim's house last night and is now dead.\n".format(get_name(succubus))
                            wolf_deaths.append(succubus)
                for disobeyer in [x for x in alive_players if 'disobey' in session[1][x][4]]:
                    if random.random() < 0.5:
                        killed_dict[disobeyer] += 100 # this is what happens to bad bois

                # Hag stuff
                for hag in [x for x in alive_players if get_role(x, 'role') == 'hag']:
                    hexed = session[1][hag][2]
                    if hexed:
                        session[1][hexed][4].append('hex')

                # Doomsayer stuff
                for doomsayer in [x for x in session[1] if get_role(x, 'role') == 'doomsayer' and [a for a in session[1][x][4] if a.startswith('doomdeath:')]]:
                    target = [a.split(':')[1] for a in session[1][doomsayer][4] if a.startswith('doomdeath:')].pop()
                    killed_dict[target] += 1
                    session[1][doomsayer][4] = [a for a in session[1][doomsayer][4] if not a.startswith('doomdeath:')]

                # Hunter stuff
                for hunter in [x for x in session[1] if get_role(x, 'role') == 'hunter']:
                    target = session[1][hunter][2]
                    if target not in [hunter, '']:
                        if 'hunterbullet' in session[1][hunter][4]:
                            session[1][hunter][4].remove('hunterbullet')
                            killed_dict[target] += 100

                # Bodyguard stuff
                for bodyguard in [x for x in alive_players if get_role(x, 'role') == 'bodyguard']:
                    target = session[1][bodyguard][2]
                    if target in session[1]:
                        if target in wolf_deaths and not ('protection_totem' in session[1][target][4] or 'blessed' in session[1][target][4] or bodyguard in guarded):
                            killed_dict[bodyguard] += 1
                            print(killed_dict[bodyguard])
                            killed_dict[target] -= 1
                            print(killed_dict[target])
                            killed_msg += "**{}** sacrificed their life to guard that of another.\n".format(get_name(bodyguard))
                            wolf_deaths.append(bodyguard)
                            wolf_deaths.remove(target)
                        #elif get_role(target, 'role') in ACTUAL_WOLVES:
                        #    killed_dict[bodyguard] += 1
                        #    killed_msg += "**{}**, a **bodyguard**, made the unfortunate mistake of guarding a wolf last night and is now dead.\n".format(get_name(bodyguard))
                        #    wolf_deaths.append(bodyguard)

                # Vengeful ghost stuff
                for ghost in [x for x in session[1] if get_role(x, 'role') == 'vengeful ghost' and not session[1][x][0] and [a for a in session[1][x][4] if a.startswith('vengeance:')]]:
                    target = session[1][ghost][2]
                    if target:
                        killed_dict[target] += 1
                        if 'retribution_totem2' in session[1][target][4]:
                            session[1][ghost][4].append('driven')
                            killed_msg += "**{0}**'s totem emitted a brilliant flash of light last night. It appears that **{1}**'s spirit was driven away by the flash.\n".format(get_name(target), get_name(ghost))

                # Totem stuff
                totem_holders = []
                protect_totemed = []
                death_totemed = []
                ill_wolves = []
                revengekill = ""

                for player in sort_players(session[1]):
                    if len([x for x in session[1][player][4] if x in totems]) > 0:
                        totem_holders.append(player)
                    prot_tots = 0
                    death_tots = 0
                    death_tots += session[1][player][4].count('death_totem')
                    killed_dict[player] += death_tots
                    if get_role(player, 'role') != 'harlot' or session[1][player][2] == player:
                        # fix for harlot with protect
                        prot_tots = session[1][player][4].count('protection_totem')
                        killed_dict[player] -= prot_tots
                    if player in wolf_killed and killed_dict[player] < 1 and not (get_role(player, 'role') == 'harlot' and session[1][player][2] != player):
                        # if player was targeted by wolves but did not die and was not harlot avoiding attack
                        if player in guarded:
                            guardeded.append(player)
                        elif 'protection_totem' in session[1][player][4]:
                            protect_totemed.append(player)
                    if 'death_totem' in session[1][player][4] and killed_dict[player] > 0 and death_tots - prot_tots - guarded.count(player) > 0:
                        death_totemed.append(player)

                    if 'cursed_totem' in session[1][player][4]:
                        if 'cursed' not in get_role(player, 'templates'):
                            session[1][player][3].append('cursed')

                    if player in wolf_deaths and killed_dict[player] > 0 and player not in death_totemed:
                        # player was targeted and killed by wolves
                        if session[1][player][4].count('lycanthropy_totem2') > 0 or get_role(player, 'role') == 'lycan' or 'lycanthropy2' in session[1][player][4]:
                            killed_dict[player] -= 1
                            if killed_dict[player] == 0:
                                wolf_turn.append(player)
                                await wolfchat("{} is now a **wolf**!".format(get_name(player)))
                                if get_role(player, 'role') == 'lycan':
                                    lycan_message = "HOOOOOOOOOWL. You have become... a wolf!"
                                elif 'lycanthropy2' in session[1][player][4]:
                                    lycan_message = "You awake to a sharp pain, and realize you are being attacked by a werewolf! You suddenly feel the weight of fate upon you, and find yourself turning into a werewolf!"
                                else:
                                    lycan_message = "You awake to a sharp pain, and realize you are being attacked by a werewolf! Your totem emits a bright flash of light, and you find yourself turning into a werewolf!"
                                try:
                                    member = client.get_server(WEREWOLF_SERVER).get_member(player)
                                    if member:
                                        await client.send_message(member, lycan_message)
                                except discord.Forbidden:
                                    pass
                        elif "pestilence_totem2" in session[1][player][4]:
                            for p in session[1]:
                                if roles[get_role(p, 'role')][0] == 'wolf' and get_role(p, 'role') in COMMANDS_FOR_ROLE['kill']:
                                    ill_wolves.append(p)
                        if session[1][player][4].count('retribution_totem') > 0 and player not in wolf_turn:
                            revenge_targets = [x for x in session[1] if session[1][x][0] and get_role(x, 'role') in [
                                'wolf', 'doomsayer', 'werecrow', 'werekitten', 'wolf shaman', 'wolf mystic']]
                            if get_role(player, 'role') == 'harlot' and get_role(session[1][player][2], 'role') in [
                                'wolf', 'doomsayer', 'werecrow', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic']:
                                revenge_targets[:] = [session[1][player][2]]
                            else:
                                revenge_targets[:] = [x for x in revenge_targets if player in session[1][x][2].split(',')]
                            if revenge_targets:
                                revengekill = random.choice(revenge_targets)
                                killed_dict[revengekill] += 100
                                if killed_dict[revengekill] > 0:
                                    killed_msg += "While being attacked last night, **{}**'s totem emitted a bright flash of light. The dead body of **{}**".format(
                                                    get_name(player), get_name(revengekill))
                                    killed_msg += ", a **{}**, was found at the scene.\n".format(get_role(revengekill, 'role'))


                    other = session[1][player][4][:]
                    for o in other[:]:
                        # hacky way to get specific mechanisms to last 2 nights
                        if o in ['death_totem', 'cursed_totem', 'retribution_totem', 'lycanthropy_totem2',
                                'deceit_totem2', 'angry', 'silence_totem2', 'luck_totem2', 'misdirection_totem2',
                                'pestilence_totem2', 'consecrated', 'illness', 'disobey', 'lycanthropy2','sided2']:
                            other.remove(o)
                        elif o.startswith('given:'):
                            other.remove(o)
                        elif o == 'protection_totem':
                            other.remove(o)
                            other.append('protection_totem2') # only protects from assassin and mad
                        elif o in ['lycanthropy_totem']:
                            other.remove(o)
                            other.append('lycanthropy_totem2')
                        elif o == 'lycanthropy':
                            other.remove(o)
                            other.append('lycanthropy2')
                        elif o == 'deceit_totem':
                            other.remove(o)
                            other.append('deceit_totem2')
                        elif o in ['silence_totem', 'hex']:
                            other.remove(o)
                            other.append('silence_totem2')
                        elif o == 'misdirection_totem':
                            other.remove(o)
                            other.append('misdirection_totem2')
                        elif o == 'luck_totem':
                            other.remove(o)
                            other.append('luck_totem2')
                        elif o == 'pestilence_totem':
                            other.remove(o)
                            other.append('pestilence_totem2')
                        elif o == 'sick':
                            other.remove(o)
                            other.append('silence_totem2')
                            other.append('illness')
                        elif o == 'sided':
                            other.remove(o)
                            other.append('sided2')
                    session[1][player][4] = other
                for player in session[1]:
                    session[1][player][4] = [x for x in session[1][player][4] if x != "ill_wolf"]
                for wolf in ill_wolves:
                    session[1][wolf][4].append("ill_wolf")
                for player in sort_players(wolf_deaths):
                    if ('gunner' in get_role(player, 'templates') or 'sharpshooter' in get_role(player, 'templates')) and \
                    session[1][player][4].count('bullet') > 0 and killed_dict[player] > 0:
                        target = ""
                        if random.random() < GUNNER_REVENGE_WOLF:
                            revenge_targets = [x for x in session[1] if session[1][x][0] and get_role(x, 'role') in [
                                'wolf', 'doomsayer', 'werecrow', 'werekitten', 'wolf shaman', 'wolf mystic']]
                            if get_role(player, 'role') == 'harlot' and get_role(session[1][player][2], 'role') in [
                                'wolf', 'doomsayer', 'werecrow', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic']:
                                revenge_targets[:] = [session[1][player][2]]
                            else:
                                revenge_targets[:] = [x for x in revenge_targets if session[1][x][2] in wolf_killed]
                            revenge_targets[:] = [x for x in revenge_targets if x not in gunner_revenge]
                            if revenge_targets:
                                target = random.choice(revenge_targets)
                                gunner_revenge.append(target)
                                session[1][player][4].remove('bullet')
                                killed_dict[target] += 100
                                if killed_dict[target] > 0:
                                    if session[6] == 'noreveal':
                                        killed_msg += "Fortunately **{}** had bullets and **{}** was shot dead.\n".format(get_name(player), get_name(target))
                                    else:
                                        killed_msg += "Fortunately **{}** had bullets and **{}**, a **{}**, was shot dead.\n".format(
                                            get_name(player), get_name(target), get_role(target, 'death'))
                        if session[1][player][4].count('bullet') > 0:
                            give_gun_targets = [x for x in session[1] if session[1][x][0] and get_role(x, 'role') in WOLFCHAT_ROLES and x != target]
                            if len(give_gun_targets) > 0:
                                give_gun = random.choice(give_gun_targets)
                                if not 'gunner' in get_role(give_gun, 'templates'):
                                    session[1][give_gun][3].append('gunner')
                                session[1][give_gun][4].append('bullet')
                                member = client.get_server(WEREWOLF_SERVER).get_member(give_gun)
                                if member:
                                    try:
                                        await client.send_message(member, "While searching through **{}**'s belongings, you discover a gun loaded with 1 "
                                        "silver bullet! You may only use it during the day. If you shoot at a wolf, you will intentionally miss. If you "
                                        "shoot a villager, it is likely that they will be injured.".format(get_name(player)))
                                    except discord.Forbidden:
                                        pass

                for player in killed_dict:
                    if killed_dict[player] > 0:
                        killed_players.append(player)

                killed_players = sort_players(killed_players)

                killed_temp = killed_players[:]

                log_msg.append("PROTECT_TOTEMED: " + ", ".join("{} ({})".format(get_name(x), x) for x in protect_totemed))
                if guarded:
                    log_msg.append("GUARDED: " + ", ".join("{} ({})".format(get_name(x), x) for x in guarded))
                if guardeded:
                    log_msg.append("ACTUALLY GUARDED: " + ", ".join("{} ({})".format(get_name(x), x) for x in guardeded))
                log_msg.append("DEATH_TOTEMED: " + ", ".join("{} ({})".format(get_name(x), x) for x in death_totemed))
                log_msg.append("PLAYERS TURNED WOLF: " + ", ".join("{} ({})".format(get_name(x), x) for x in wolf_turn))
                if revengekill:
                    log_msg.append("RETRIBUTED: " + "{} ({})".format(get_name(revengekill), revengekill))
                if gunner_revenge:
                    log_msg.append("GUNNER_REVENGE: " + ", ".join("{} ({})".format(get_name(x), x) for x in gunner_revenge))
                log_msg.append("DEATHS FROM WOLF: " + ", ".join("{} ({})".format(get_name(x), x) for x in wolf_deaths))
                log_msg.append("KILLED PLAYERS: " + ", ".join("{} ({})".format(get_name(x), x) for x in killed_players))

                await log(1, '\n'.join(log_msg))

                if guardeded:
                    for gded in sort_players(guardeded):
                        killed_msg += "**{0}** was attacked last night, but luckily the guardian angel was on duty.\n".format(get_name(gded))

                if protect_totemed:
                    for protected in sort_players(protect_totemed):
                        killed_msg += "**{0}** was attacked last night, but their totem emitted a brilliant flash of light, blinding their attacker and allowing them to escape.\n".format(
                                            get_name(protected))



                if death_totemed:
                    for ded in sort_players(death_totemed):
                        if session[6] == 'noreveal':
                            killed_msg += "**{0}**'s totem emitted a brilliant flash of light last night. The dead body of **{0}** was found at the scene.\n".format(get_name(ded))
                        else:
                            killed_msg += "**{0}**'s totem emitted a brilliant flash of light last night. The dead body of **{0}**, a **{1}** was found at the scene.\n".format(
                                            get_name(ded), get_role(ded, 'death'))
                        killed_players.remove(ded)
                if revengekill and revengekill in killed_players:
                    # retribution totem
                    killed_players.remove(revengekill)

                for player in gunner_revenge:
                    if player in killed_players:
                        killed_players.remove(player)

                if len(killed_players) == 0:
                    if not (guardeded or protect_totemed or death_totemed or [x for x in wolf_killed if get_role(x, 'role') == 'harlot']):
                        killed_msg += random.choice(lang['nokills']) + '\n'
                elif len(killed_players) == 1:
                    if session[6] == 'noreveal':
                        killed_msg += "The dead body of **{}** was found. Those remaining mourn the tragedy.\n".format(get_name(killed_players[0]))
                    else:
                        killed_msg += "The dead body of **{}**, a **{}**, was found. Those remaining mourn the tragedy.\n".format(get_name(killed_players[0]), get_role(killed_players[0], 'death'))
                else:
                    if session[6] == 'noreveal':
                        if len(killed_players) == 2:
                            killed_msg += "The dead bodies of **{0}** and **{1}** were found. Those remaining mourn the tragedy.\n".format(get_name(killed_players[0]), get_name(killed_players[1]))
                        else:
                            killed_msg += "The dead bodies of **{0}**, and **{1}** were found. Those remaining mourn the tragedy.\n".format(('**, **'.join(map(get_name, killed_players[:-1])), get_name(killed_players[-1])))
                    else:
                        killed_msg += "The dead bodies of **{}**, and **{}**, a **{}**, were found. Those remaining mourn the tragedy.\n".format(
                        '**, **'.join(get_name(x) + '**, a **' + get_role(x, 'death') for x in killed_players[:-1]), get_name(killed_players[-1]), get_role(killed_players[-1], 'death'))

                if session[0] and win_condition() == None:
                    await send_lobby("Night lasted **{0:02d}:{1:02d}**. The villagers wake up and search the village.\n\n{2}".format(
                                                                                            night_elapsed.seconds // 60, night_elapsed.seconds % 60, killed_msg))

                killed_dict = {}
                for player in killed_temp:
                    kill_team = "wolf" if player not in gunner_revenge + list(revengekill) + death_totemed and player in wolf_deaths else "village"
                    killed_dict[player] = ("night kill", kill_team)
                if killed_dict:
                    await player_deaths(killed_dict)

                if session[0] and win_condition() == None:
                    totem_holders = sort_players(totem_holders)
                    if len(totem_holders) == 0:
                        pass
                    elif len(totem_holders) == 1:
                        await send_lobby(random.choice(lang['hastotem']).format(get_name(totem_holders[0])))
                    elif len(totem_holders) == 2:
                        await send_lobby(random.choice(lang['hastotem2']).format(get_name(totem_holders[0]), get_name(totem_holders[1])))
                    else:
                        await send_lobby(random.choice(lang['hastotems']).format('**, **'.join([get_name(x) for x in totem_holders[:-1]]), get_name(totem_holders[-1])))

                for player in wolf_turn:
                    session[1][player][4].append('turned:{}'.format(get_role(player, 'role')))
                    session[1][player][1] = 'wolf'

                for player in session[1]:
                    session[1][player][2] = ''

                charmed = sort_players([x for x in alive_players if 'charmed' in session[1][x][4]])
                tocharm = sort_players([x for x in alive_players if 'tocharm' in session[1][x][4]])
                for player in tocharm:
                    charmed_total = [x for x in charmed + tocharm if x != player]
                    session[1][player][4].remove('tocharm')
                    session[1][player][4].append('charmed')
                    piper_message = "You hear the sweet tones of a flute coming from outside your window... You inexorably walk outside and find yourself in the village square. "
                    if len(charmed_total) > 2:
                        piper_message += "You find out that **{0}**, and **{1}** are also charmed!".format('**, **'.join(map(get_name, charmed_total[:-1])), get_name(charmed_total[-1]))
                    elif len(charmed_total) == 2:
                        piper_message += "You find out that **{0}** and **{1}** are also charmed!".format(get_name(charmed_total[0]), get_name(charmed_total[1]))
                    elif len(charmed_total) == 1:
                        piper_message += "You find out that **{}** is also charmed!".format(get_name(charmed_total[0]))
                    try:
                        member = client.get_server(WEREWOLF_SERVER).get_member(player)
                        if member and piper_message:
                            await client.send_message(member,piper_message)
                    except discord.Forbidden:
                        pass
                fullcharmed = charmed + tocharm
                for player in charmed:
                    piper_message = ''
                    fullcharmed.remove(player)
                    if len(fullcharmed) > 1:
                        piper_message = "You, **{0}**, and **{1}** are all charmed!".format('**, **'.join(map(get_name, fullcharmed[:-1])), get_name(fullcharmed[-1]))
                    elif len(fullcharmed) == 1:
                        piper_message = "You and **{0}** are now charmed!".format(get_name(fullcharmed[0]))
                    elif len(fullcharmed) == 0:
                        piper_message = "You are the only charmed villager."
                    try:
                        member = client.get_server(WEREWOLF_SERVER).get_member(player)
                        if member and piper_message:
                            await client.send_message(member,piper_message)
                    except discord.Forbidden:
                        pass
                    fullcharmed.append(player)

                if session[0] and win_condition() == None:
                    await check_traitor()
            else: # DAY
                session[3][1] = datetime.now()
                if session[0] and win_condition() == None:
                    for player in session[1]:
                        session[1][player][4] = [x for x in session[1][player][4] if x not in ["guarded", "protection_totem2"] and not x.startswith('bodyguard:')]
                    await send_lobby("It is now **daytime**. Use `{}lynch <player>` to vote to lynch <player>.".format(BOT_PREFIX))

                for player in session[1]:
                    if session[1][player][0] and 'blinding_totem' in session[1][player][4]:
                        if 'injured' not in session[1][player][4]:
                            session[1][player][4].append('injured')
                            for i in range(session[1][player][4].count('blinding_totem')):
                                session[1][player][4].remove('blinding_totem')
                            try:
                                member = client.get_server(WEREWOLF_SERVER).get_member(player)
                                if member:
                                    await client.send_message(member, "Your totem emits a brilliant flash of light. "
                                                                    "It seems like you cannot see anything! Perhaps "
                                                                    "you should just rest during the day...")
                            except discord.Forbidden:
                                pass
                    if 'illness' in session[1][player][4]:
                        session[1][player][4].append('injured')
                    if get_role(player, 'role') == 'doomsayer':
                        session[1][player][4] = [x for x in session[1][player][4] if not x.startswith('doom:')]
                if session[6] != 'mudkip':
                    lynched_player = None
                    warn = False
                    totem_dict = {} # For impatience and pacifism
                    # DAY LOOP
                    while win_condition() == None and session[2] and lynched_player == None and session[0]:
                        for player in [x for x in session[1]]:
                            totem_dict[player] = session[1][player][4].count('impatience_totem') - session[1][player][4].count('pacifism_totem')
                        vote_dict = get_votes(totem_dict)
                        if vote_dict['abstain'] >= len([x for x in session[1] if session[1][x][0] and 'injured' not in session[1][x][4]]) / 2:
                            lynched_player = 'abstain'
                        max_votes = max([vote_dict[x] for x in vote_dict])
                        max_voted = []
                        if max_votes >= len([x for x in session[1] if session[1][x][0] and 'injured' not in session[1][x][4]]) // 2 + 1:
                            for voted in vote_dict:
                                if vote_dict[voted] == max_votes:
                                    max_voted.append(voted)
                            lynched_player = random.choice(max_voted)
                        if (datetime.now() - session[3][1]).total_seconds() > day_timeout:
                            session[3][0] = datetime.now() # hopefully a fix for time being weird
                            session[2] = False
                        if (datetime.now() - session[3][1]).total_seconds() > day_warning and warn == False:
                            warn = True
                            await send_lobby("**As the sun sinks inexorably toward the horizon, turning the lanky pine "
                                                    "trees into fire-edged silhouettes, the villagers are reminded that very little time remains for them to reach a "
                                                    "decision; if darkness falls before they have done so, the majority will win the vote. No one will be lynched if "
                                                    "there are no votes or an even split.**")
                        await asyncio.sleep(0.1)
                    if not lynched_player and win_condition() == None and session[0]:
                        vote_dict = get_votes(totem_dict)
                        max_votes = max([vote_dict[x] for x in vote_dict])
                        max_voted = []
                        for voted in vote_dict:
                            if vote_dict[voted] == max_votes and voted != 'abstain':
                                max_voted.append(voted)
                        if len(max_voted) == 1:
                            lynched_player = max_voted[0]
                    if session[0]:
                        session[3][0] = datetime.now() # hopefully a fix for time being weird
                        day_elapsed = datetime.now() - session[3][1]
                        session[4][1] += day_elapsed
                    lynched_msg = ""
                    if lynched_player and win_condition() == None and session[0]:
                        if lynched_player == 'abstain':
                            for player in [x for x in totem_dict if session[1][x][0] and totem_dict[x] < 0]:
                                lynched_msg += "**{}** meekly votes to not lynch anyone today.\n".format(get_name(player))
                            lynched_msg += "The village has agreed to not lynch anyone today."
                            await send_lobby(lynched_msg)
                        else:
                            for player in [x for x in totem_dict if session[1][x][0] and totem_dict[x] > 0 and x != lynched_player]:
                                lynched_msg += "**{}** impatiently votes to lynch **{}**.\n".format(get_name(player), get_name(lynched_player))
                            lynched_msg += '\n'
                            if 'revealing_totem' in session[1][lynched_player][4]:
                                lynched_msg += 'As the villagers prepare to lynch **{0}**, their totem emits a brilliant flash of light! When the villagers are able to see again, '
                                lynched_msg += 'they discover that {0} has escaped! The left-behind totem seems to have taken on the shape of a **{1}**.'
                                if get_role(lynched_player, 'role') == 'amnesiac':
                                    role = [x.split(':')[1].replace("_", " ") for x in session[1][lynched_player][4] if x.startswith("role:")].pop()
                                    session[1][lynched_player][1] = role
                                    session[1][lynched_player][4] = [x for x in session[1][lynched_player][4] if not x.startswith("role:")]
                                    try:
                                        await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(lynched_player), "Your totem clears your amnesia and you now fully remember who you are!")
                                        await _send_role_info(lynched_player)
                                        if role in WOLFCHAT_ROLES:
                                            await wolfchat("{0} is now a **{1}**!".format(get_name(lynched_player), role))
                                    except discord.Exception:
                                        pass
                                lynched_msg = lynched_msg.format(get_name(lynched_player), get_role(lynched_player, 'role'))
                                await send_lobby(lynched_msg)
                            elif 'mayor' in get_role(lynched_player, 'templates') and 'unrevealed' in session[1][lynched_player][4]:
                                lynched_msg += "While being dragged to the gallows, **{}** reveals that they are the **mayor**. The village agrees to let them live for now.".format(get_name(lynched_player))
                                session[1][lynched_player][4].remove('unrevealed')
                                await send_lobby(lynched_msg)
                            else:
                                if 'luck_totem2' in session[1][lynched_player][4]:
                                    lynched_player = misdirect(lynched_player)
                                if session[6] == 'noreveal':
                                    lynched_msg += random.choice(lang['lynchednoreveal']).format(get_name(lynched_player))
                                else:
                                    lynched_msg += random.choice(lang['lynched']).format(get_name(lynched_player), get_role(lynched_player, 'death'))
                                await send_lobby(lynched_msg)
                                if get_role(lynched_player, 'role') == 'jester':
                                    session[1][lynched_player][4].append('lynched')
                                lynchers_team = [get_role(x, 'actualteam') for x in session[1] if session[1][x][0] and session[1][x][2] == lynched_player]
                                await player_deaths({lynched_player : ('lynch', 'wolf' if lynchers_team.count('wolf') > lynchers_team.count('village') else 'village')})

                            if get_role(lynched_player, 'role') == 'fool' and 'revealing_totem' not in session[1][lynched_player][4]:
                                win_msg = "The fool has been lynched, causing them to win!\n\n" + end_game_stats()
                                lovers = []
                                for n in session[1][lynched_player][4]:
                                    if n.startswith('lover:'):
                                        lover = n.split(':')[1]
                                        if session[1][lover][0]:
                                            lovers.append(lover)

                                await end_game(win_msg, [lynched_player] + (lovers if session[6] == "random" else []) + [x for x in session[1] if get_role(x, "role") == "jester" and "lynched" in session[1][x][4]])
                                return
                    elif lynched_player == None and win_condition() == None and session[0]:
                        await send_lobby("Not enough votes were cast to lynch a player.")
                else:
                    lynched_players = []
                    warn = False
                    totem_dict = {} # For impatience and pacifism
                    # DAY LOOP
                    while win_condition() == None and session[2] and not lynched_players and session[0]:
                        for player in [x for x in session[1]]:
                            totem_dict[player] = session[1][player][4].count('impatience_totem') - session[1][player][4].count('pacifism_totem')
                        vote_dict = get_votes(totem_dict)
                        max_votes = max([vote_dict[x] for x in vote_dict])
                        max_voted = []
                        if vote_dict['abstain'] >= len([x for x in session[1] if session[1][x][0] and 'injured' not in session[1][x][4]]) / 2:
                            lynched_players = 'abstain'
                        elif max_votes >= len([x for x in session[1] if session[1][x][0] and 'injured' not in session[1][x][4]]) // 2 + 1 or not [x for x in session[1] if not session[1][x][2] and session[1][x][0]]:
                            for voted in vote_dict:
                                if vote_dict[voted] == max_votes:
                                    lynched_players.append(voted)
                        if (datetime.now() - session[3][1]).total_seconds() > day_timeout:
                            session[3][0] = datetime.now() # hopefully a fix for time being weird
                            session[2] = False
                        if (datetime.now() - session[3][1]).total_seconds() > day_warning and warn == False:
                            warn = True
                            await send_lobby("**As the sun sinks inexorably toward the horizon, turning the lanky pine "
                                                    "trees into fire-edged silhouettes, the villagers are reminded that very little time remains for them to reach a "
                                                    "decision; if darkness falls before they have done so, the majority will win the vote. No one will be lynched if "
                                                    "there are no votes or an even split.**")
                        await asyncio.sleep(0.1)
                    if not lynched_players and win_condition() == None and session[0]:
                        vote_dict = get_votes(totem_dict)
                        max_votes = max([vote_dict[x] for x in vote_dict])
                        max_voted = []
                        for voted in vote_dict:
                            if vote_dict[voted] == max_votes and voted != 'abstain':
                                max_voted.append(voted)
                        if max_voted:
                            lynched_players = max_voted
                    if session[0]:
                        session[3][0] = datetime.now() # hopefully a fix for time being weird
                        day_elapsed = datetime.now() - session[3][1]
                        session[4][1] += day_elapsed
                    lynched_msg = ""
                    lynch_deaths = {}
                    if lynched_players and win_condition() == None and session[0]:
                        if lynched_players == 'abstain':
                            for player in [x for x in totem_dict if session[1][x][0] and totem_dict[x] < 0]:
                                lynched_msg += "**{}** meekly votes to not lynch anyone today.\n".format(get_name(player))
                            lynched_msg += "The village has agreed to not lynch anyone today."
                            await send_lobby(lynched_msg)
                        else:
                            for lynched_player in lynched_players:
                                lynched_msg += "\n"
                                if 'revealing_totem' in session[1][lynched_player][4]:
                                    lynched_msg += 'As the villagers prepare to lynch **{0}**, their totem emits a brilliant flash of light! When the villagers are able to see again, '
                                    lynched_msg += 'they discover that {0} has escaped! The left-behind totem seems to have taken on the shape of a **{1}**.'
                                    if get_role(lynched_player, 'role') == 'amnesiac':
                                        role = [x.split(':')[1].replace("_", " ") for x in session[1][lynched_player][4] if x.startswith("role:")].pop()
                                        session[1][lynched_player][1] = role
                                        session[1][lynched_player][4] = [x for x in session[1][lynched_player][4] if not x.startswith("role:")]
                                        try:
                                            await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(lynched_player), "Your totem clears your amnesia and you now fully remember who you are!")
                                            await _send_role_info(lynched_player)
                                            if role in WOLFCHAT_ROLES:
                                                await wolfchat("{0} is now a **{1}**!".format(get_name(lynched_player), role))
                                        except discord.Exception:
                                            pass
                                    lynched_msg = lynched_msg.format(get_name(lynched_player), get_role(lynched_player, 'role'))
                                    await send_lobby(lynched_msg)
                                else:
                                    if 'luck_totem2' in session[1][lynched_player][4]:
                                        lynched_player = misdirect(lynched_player)
                                    if session[6] == 'noreveal':
                                        lynched_msg += random.choice(lang['lynchednoreveal']).format(get_name(lynched_player))
                                    else:
                                        lynched_msg += random.choice(lang['lynched']).format(get_name(lynched_player), get_role(lynched_player, 'death'))
                                    if get_role(lynched_player, 'role') == 'jester':
                                        session[1][lynched_player][4].append('lynched')
                                    lynchers_team = [get_role(x, 'actualteam') for x in session[1] if session[1][x][0] and session[1][x][2] == lynched_player]
                                    lynch_deaths.update({lynched_player : ('lynch', 'wolf' if lynchers_team.count('wolf') > lynchers_team.count('village') else 'village')})

                                if get_role(lynched_player, 'role') == 'fool' and 'revealing_totem' not in session[1][lynched_player][4]:
                                    win_msg = "The fool has been lynched, causing them to win!\n\n" + end_game_stats()
                                    lovers = []
                                    for n in session[1][lynched_player][4]:
                                        if n.startswith('lover:'):
                                            lover = n.split(':')[1]
                                            if session[1][lover][0]:
                                                lovers.append(lover)

                                    await end_game(win_msg, [lynched_player] + (lovers if session[6] == "random" else []) + [x for x in session[1] if get_role(x, "role") == "jester" and "lynched" in session[1][x][4]])
                                    return
                        await send_lobby(lynched_msg)
                        await player_deaths(lynch_deaths)
                    elif lynched_players == None and win_condition() == None and session[0]:
                        await send_lobby("Not enough votes were cast to lynch a player.")
                # BETWEEN DAY AND NIGHT
                session[2] = False
                night += 1
                if session[0] and win_condition() == None:
                    await send_lobby("Day lasted **{0:02d}:{1:02d}**. The villagers, exhausted from the day's events, go to bed.".format(
                                                                        day_elapsed.seconds // 60, day_elapsed.seconds % 60))
                    for player in [x for x in session[1] if session[1][x][0] and 'entranced' in session[1][x][4]]:
                        if session[1][player][2] not in [session[1][x][2] for x in session[1] if session[1][x][0] and get_role(x, 'role') == 'succubus']:
                            session[1][player][4].append('disobey')
                    for player in session[1]:
                        session[1][player][4][:] = [x for x in session[1][player][4] if x not in [
                            'revealing_totem', 'influence_totem', 'impatience_totem', 'pacifism_totem', 'injured', 'desperation_totem']]
                        session[1][player][2] = ''
                        session[1][player][4] = [x for x in session[1][player][4] if not x.startswith('vote:')]
                        if get_role(player, 'role') == 'amnesiac' and night == 3 and session[1][player][0]:
                            role = [x.split(':')[1].replace("_", " ") for x in session[1][player][4] if x.startswith("role:")].pop()
                            session[1][player][1] = role
                            session[1][player][4] = [x for x in session[1][player][4] if not x.startswith("role:")]
                            session[1][player][4].append('amnesiac')
                            try:
                                await client.send_message(client.get_server(WEREWOLF_SERVER).get_member(player), "Your amnesia clears and you now remember that you are a{0} **{1}**!".format("n" if role.lower()[0] in ['a', 'e', 'i', 'o', 'u'] else "", role))
                                if role in WOLFCHAT_ROLES:
                                    await wolfchat("{0} is now a **{1}**!".format(get_name(player), role))
                            except:
                                pass
                if session[0] and win_condition() == None:
                    await check_traitor()
                
        # GAME END
        if session[0]:
            win_msg = win_condition()
            await end_game(win_msg[1], win_msg[2])
            
