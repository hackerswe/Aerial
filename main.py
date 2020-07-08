# Files #
import aerial

# Modules #
import os
import discord
import fortnitepy
import yaml
import dotenv
import asyncio
import random
import requests
import sys
import logging
from functools import partial
from discord.ext import commands

# Logging #
logging.basicConfig(
    level=logging.INFO,
    filename="aerial.log",
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# Load Accounts #
if os.path.isfile("accounts.yml"):
    accounts = yaml.safe_load(open("accounts.yml"))
else:
    sys.exit("Cannot Load accounts.yml!")


def convert(ls: list):
    return {ls[i]: ls[i + 1] for i in range(0, len(ls), 2)}


# Variables #
dotenv.load_dotenv()
clients = {}
available = {}
owner = {}
messages = {}
status = os.getenv("STATUSPAGE")
hook = discord.Webhook.from_url(
    os.getenv("EXCEPTHOOK"),
    adapter=discord.RequestsWebhookAdapter()
)


# Exception Hook #
def excepthook(exctype, value, tb):
    hook.send(
        embed=discord.Embed(
            title="Exception",
            type="rich",
            description=str(exctype) + "\n\n" + str(value) + "\n\n" + str(tb)
        )
    )


loop = asyncio.get_event_loop()

# Discord Client #
dclient = commands.AutoShardedBot(
    command_prefix="a.",
    help_command=None,
    activity=discord.Streaming(
        platform="Twitch",
        name="Fortnite Bots",
        details="Fortnite Bots",
        game="Fortnite Bots",
        url="https://twitch.tv/andre4ik3"
    )
)


# Bot Functions #
async def refresh_message(client: aerial.DisposableClient):
    message = messages[client]
    await message.edit(
        embed=discord.Embed(
            title="<:Online:719038976677380138> " + client.user.display_name,
            type="rich",
            color=0xfc5fe2
        ).set_thumbnail(
            url=aerial.cosmetic(client.party.me.outfit, "AthenaCharacter")['icons']['icon']
        ).add_field(
            name="Discord Server",
            value="https://discord.gg/r7DHHfY",
            inline=True
        )
    )


async def stop_bot(client: aerial.DisposableClient, ownerid: int, text: str = None, delay: int = 0):

    await asyncio.sleep(delay)

    result = aerial.stop(
        client=client,
        timeout=30.0
    )

    if result is False:
        pass

    available[client.name] = client
    owner.pop(ownerid)

    await messages[client].edit(
        embed=discord.Embed(
            title="<:Offline:719321200098017330> Bot Offline",
            description=text,
            type="rich",
            color=0x747f8d
        )
    )

    hook.send(":heavy_minus_sign: " + dclient.get_user(ownerid).mention + " is no longer using the bot")


async def start_bot(member: discord.Member, time: int):

    try:
        message = await member.send(
            embed=discord.Embed(
                title="<a:Loading:719025775042494505> Starting Bot...",
                type="rich",
                color=0x7289da
            )
        )

    except discord.Forbidden:
        return

    if member.id in list(owner.keys()):
        await message.edit(
            embed=discord.Embed(
                title=":x: Bot Already Running!",
                color=0xe46b6b
            ),
            delete_after=3
        )
        return

    else:
        name = random.choice(list(available.keys()))
        client = available[name]
        available.pop(name)
        owner[member.id] = client
        messages[client] = message

    @client.event
    async def event_friend_request(friend: fortnitepy.IncomingPendingFriend):
        if member.id not in list(owner.keys()):
            return

        rmsg = await message.channel.send(
            embed=discord.Embed(
                title="<:FriendRequest:719042256849338429> Friend Request from " + friend.display_name,
                type="rich",
                description="<:Accept:719047548219949136> Accept    <:Reject:719047548819472446> Reject"
            )
        )

        await rmsg.add_reaction(":Accept:719047548219949136")
        await rmsg.add_reaction(":Reject:719047548819472446")

        def check(reaction, user):

            if str(reaction.emoji) in ["<:Accept:719047548219949136>", "<:Reject:719047548819472446>"] and not user.bot:
                return True

            else:
                return False

        try:
            reaction, user = await dclient.wait_for("reaction_add", timeout=60.0, check=check)

        except asyncio.TimeoutError:
            await rmsg.edit(
                delete_after=1,
                embed=discord.Embed(
                    title="<:FriendRequest:719042256849338429> Friend Request from " + friend.display_name,
                    type="rich",
                    color=0xf24949
                )
            )
            await friend.decline()

        else:
            if str(reaction.emoji) == "<:Accept:719047548219949136>":
                await rmsg.edit(
                    delete_after=1,
                    embed=discord.Embed(
                        title="<:FriendRequest:719042256849338429> Friend Request from " + friend.display_name,
                        type="rich",
                        color=0x43b581
                    )
                )
                await friend.accept()

            elif str(reaction.emoji) == "<:Reject:719047548819472446>":
                await rmsg.edit(
                    delete_after=1,
                    embed=discord.Embed(
                        title="<:FriendRequest:719042256849338429> Friend Request from " + friend.display_name,
                        type="rich",
                        color=0xf24949
                    )
                )
                await friend.decline()

    @client.event
    async def event_party_invite(invitation: fortnitepy.ReceivedPartyInvitation):

        if member.id not in list(owner.keys()):
            return

        rmsg = await message.channel.send(
            embed=discord.Embed(
                title="<:PartyInvite:719198827281645630> Party Invite from " + invitation.sender.display_name,
                type="rich",
                description="<:Accept:719047548219949136> Accept    <:Reject:719047548819472446> Reject"
            )
        )

        await rmsg.add_reaction(":Accept:719047548219949136")
        await rmsg.add_reaction(":Reject:719047548819472446")

        def check(reaction, user):

            if str(reaction.emoji) in ["<:Accept:719047548219949136>", "<:Reject:719047548819472446>"] and not user.bot:
                return True

            else:
                return False

        try:
            reaction, user = await dclient.wait_for("reaction_add", timeout=60.0, check=check)

        except asyncio.TimeoutError:
            await rmsg.edit(
                delete_after=1,
                embed=discord.Embed(
                    title="<:PartyInvite:719198827281645630> Party Invite from " + invitation.sender.display_name,
                    type="rich",
                    color=0xf24949
                )
            )
            await invitation.decline()

        else:
            if str(reaction.emoji) == "<:Accept:719047548219949136>":
                await rmsg.edit(
                    delete_after=1,
                    embed=discord.Embed(
                        title="<:PartyInvite:719198827281645630> Party Invite from " + invitation.sender.display_name,
                        type="rich",
                        color=0x43b581
                    )
                )
                await invitation.accept()

            elif str(reaction.emoji) == "<:Reject:719047548819472446>":
                await rmsg.edit(
                    delete_after=1,
                    embed=discord.Embed(
                        title="<:PartyInvite:719198827281645630> Party Invite from " + invitation.sender.display_name,
                        type="rich",
                        color=0xf24949
                    )
                )
                await invitation.decline()

    @client.event
    async def event_close():

        del client.event_friend_request
        del client.event_party_invite

    started = await aerial.start(
        client=client,
        timeout=30.0
    )

    if not started:
        await stop_bot(client, member.id, "An error occured while starting the bot. Please try again.", 0)
        return

    message2 = await message.channel.send(
        embed=discord.Embed(
            title="<:Online:719038976677380138> " + client.user.display_name,
            type="rich",
            color=0xfc5fe2
        ).set_thumbnail(
            url=aerial.cosmetic(client.party.me.outfit, "AthenaCharacter")['icons']['icon']
        ).add_field(
            name="Discord Server",
            value="https://discord.gg/r7DHHfY",
            inline=True
        )
    )

    await message.delete()
    messages[client] = message2
    hook.send(":heavy_plus_sign: " + member.mention + " is now using the bot (" + client.user.display_name + ")")
    await message.channel.send(content="Documentation is available here: **<https://aerial.now.sh/>**", delete_after=120)

    loop.create_task(
        stop_bot(
            client,
            member.id,
            "This bot automatically shuts down after " + str(time / 60) + " minutes.",
            time
        )
    )


async def parse_command(message: discord.Message):

    if type(message.channel) != discord.DMChannel or message.author.bot:
        return

    elif message.author.id not in list(owner.keys()):
        return

    msg = message.content.split(" ")

    client = owner[message.author.id]

    if msg[0].lower() == "stop" or msg[0].lower() == "logout":
        await stop_bot(client, message.author.id, "You requested the bot to shutdown.", 0)

    elif msg[0].lower() == "restart" or msg[0].lower() == "reboot":
        restartmsg = await message.channel.send(content="<a:Queue:720808283740569620> Restarting...")
        try:
            await asyncio.wait_for(client.restart(), timeout=30.0)
            await restartmsg.edit(content="<:Accept:719047548219949136> Restarted!", delete_after=10)
        except asyncio.TimeoutError:
            await stop_bot(client, message.author.id, "Something went wrong while restarting. Your bot has been shut down.", 0)
            await restartmsg.edit(content="<:Reject:719047548819472446> Something went wrong while restarting. Your bot has been shut down.", delete_after=20)
    elif msg[0].lower() == "help":
        await message.channel.send(content="Documentation is available here: **<https://aerial.now.sh/>**", delete_after=10)
    elif msg[0].lower() == "ready":
        await client.party.me.set_ready(fortnitepy.ReadyState.READY)
    elif msg[0].lower() == "unready" or msg[0].lower() == "sitin":
        await client.party.me.set_ready(fortnitepy.ReadyState.NOT_READY)
    elif msg[0].lower() == "sitout":
        await client.party.me.set_ready(fortnitepy.ReadyState.SITTING_OUT)
    elif msg[0].lower() == "leave":
        await client.party.me.leave()
    elif msg[0].lower() == "promote":
        msg[1] = " ".join(msg[1:])
        p = await client.fetch_profile(msg[1])
        if p is None:
            return
        p = client.party.get_member(p.id)
        if p is None:
            return
        try:
            await p.promote()
            await message.channel.send("<:Accept:719047548219949136> Promoted " + p.display_name, delete_after=10)
        except fortnitepy.errors.Forbidden:
            await message.channel.send("<:Reject:719047548819472446> I am Not Party Leader!", delete_after=10)
    elif msg[0].lower() == "kick":
        msg[1] = " ".join(msg[1:])
        p = await client.fetch_profile(msg[1])
        if p is None:
            return
        p = client.party.get_member(p.id)
        if p is None:
            return
        try:
            await p.kick()
            await message.channel.send("<:Accept:719047548219949136> Kicked " + p.display_name, delete_after=10)
        except fortnitepy.errors.Forbidden:
            await message.channel.send("<:Reject:719047548819472446> I am Not Party Leader!", delete_after=10)
    elif msg[0].lower() == "join":
        msg[1] = " ".join(msg[1:])
        p = await client.fetch_profile(msg[1])
        if p is None:
            return
        p = client.get_friend(p.id)
        if p is None:
            return
        try:
            await p.join_party()
            await message.channel.send("<:Accept:719047548219949136> Joined " + p.display_name, delete_after=10)
        except fortnitepy.errors.Forbidden:
            await message.channel.send("<:Reject:719047548819472446> Cannot Join " + p.display_name + " as their Party is Private", delete_after=10)
    elif msg[0].lower() == "set":
        if len(msg) < 3:
            return
        elif msg[1].lower() == "outfit" or msg[1].lower() == "skin":
            msg[2] = " ".join(msg[2:])
            cosmetic = aerial.cosmetic(msg[2], "AthenaCharacter")
            if cosmetic is None:
                await message.channel.send("<:Reject:719047548819472446> Cannot Find Outfit " + msg[2], delete_after=10)
            else:
                await client.party.me.edit_and_keep(partial(client.party.me.set_outfit, cosmetic['id']))
                await message.channel.send("<:Accept:719047548219949136> Set Outfit to " + cosmetic['name'], delete_after=10)
                await refresh_message(client)
        elif msg[1].lower() == "backbling" or msg[1].lower() == "backpack":
            msg[2] = " ".join(msg[2:])
            if msg[2].lower() == "none":
                await client.party.me.edit_and_keep(partial(client.party.me.clear_backpack))
                await message.channel.send("<:Accept:719047548219949136> Set Back Bling to None", delete_after=10)
            else:
                cosmetic = aerial.cosmetic(msg[2], "AthenaBackpack")
                if cosmetic is None:
                    await message.channel.send("<:Reject:719047548819472446> Cannot Find Back Bling " + msg[2], delete_after=10)
                else:
                    await client.party.me.edit_and_keep(partial(client.party.me.set_backpack, cosmetic['id']))
                    await message.channel.send("<:Accept:719047548219949136> Set Back Bling to " + cosmetic['name'], delete_after=10)
        elif msg[1].lower() == "emote" or msg[1].lower() == "dance":
            msg[2] = " ".join(msg[2:])
            if msg[2].lower() == "none":
                await client.party.me.clear_emote()
                await message.channel.send("<:Accept:719047548219949136> Set Emote to None", delete_after=10)
            else:
                cosmetic = aerial.cosmetic(msg[2], "AthenaDance")
                if cosmetic is None:
                    await message.channel.send("<:Reject:719047548819472446> Cannot Find Emote " + msg[2], delete_after=10)
                else:
                    await client.party.me.clear_emote()
                    await client.party.me.set_emote(cosmetic['id'])
                    await message.channel.send("<:Accept:719047548219949136> Set Emote to " + cosmetic['name'], delete_after=10)
        elif msg[1].lower() == "harvesting_tool" or msg[1].lower() == "harvestingtool" or msg[1].lower() == "pickaxe":
            msg[2] = " ".join(msg[2:])
            cosmetic = aerial.cosmetic(msg[2], "AthenaPickaxe")
            if cosmetic is None:
                await message.channel.send("<:Reject:719047548819472446> Cannot Find Harvesting Tool " + msg[2], delete_after=10)
            else:
                await client.party.me.edit_and_keep(partial(client.party.me.set_pickaxe, cosmetic['id']))
                await message.channel.send("<:Accept:719047548219949136> Set Harvesting Tool to " + cosmetic['name'], delete_after=10)
        elif msg[1].lower() == "banner" and len(msg) == 4:
            if msg[2].lower() == "design" or msg[2].lower() == "icon":
                await client.party.me.edit_and_keep(partial(client.party.me.set_banner, icon=msg[3], color=client.party.me.banner[1], season_level=client.party.me.banner[2]))
                await message.channel.send("<:Accept:719047548219949136> Set Banner Design to " + msg[3], delete_after=10)
            elif msg[2].lower() == "color" or msg[2].lower() == "colour":
                await client.party.me.edit_and_keep(partial(client.party.me.set_banner, icon=client.party.me.banner[0], color=msg[3], season_level=client.party.me.banner[2]))
                await message.channel.send("<:Accept:719047548219949136> Set Banner Color to " + msg[3], delete_after=10)
            elif msg[2].lower() == "season_level" or msg[2].lower() == "level":
                await client.party.me.edit_and_keep(partial(client.party.me.set_banner, icon=client.party.me.banner[0], color=client.party.me.banner[1], season_level=msg[3]))
                await message.channel.send("<:Accept:719047548219949136> Set Season Level to " + msg[3], delete_after=10)
        elif msg[1].lower() == "battlepass" or msg[1].lower() == "bp" and len(msg) == 4:
            if msg[2].lower() == "has_purchased":
                if msg[3] == "true":
                    await client.party.me.edit_and_keep(partial(client.party.me.set_battlepass_info, has_purchased=True))
                    await message.channel.send("<:Accept:719047548219949136> Set Battle Pass Purchase Status to True", delete_after=10)
                elif msg[3] == "false":
                    await client.party.me.edit_and_keep(partial(client.party.me.set_battlepass_info, has_purchased=False))
                    await message.channel.send("<:Accept:719047548219949136> Set Battle Pass Purchase Status to False", delete_after=10)
            elif msg[2].lower() == "level":
                await client.party.me.edit_and_keep(partial(client.party.me.set_battlepass_info, level=msg[3]))
                await message.channel.send("<:Accept:719047548219949136> Set Battle Pass Level to " + msg[3], delete_after=10)
            elif msg[2].lower() == "self_boost_xp":
                await client.party.me.edit_and_keep(partial(client.party.me.set_battlepass_info, self_boost_xp=msg[3]))
                await message.channel.send("<:Accept:719047548219949136> Set Battle Pass Self Boost to " + msg[3], delete_after=10)
            elif msg[2].lower() == "friend_boost_xp":
                await client.party.me.edit_and_keep(partial(client.party.me.set_battlepass_info, friend_boost_xp=msg[3]))
                await message.channel.send("<:Accept:719047548219949136> Set Battle Pass Friend Boost to " + msg[3], delete_after=10)
        elif msg[1].lower() == "status" or msg[1].lower() == "presence":
            msg[2] = " ".join(msg[2:])
            await client.set_status(msg[2])
            await message.channel.send("<:Accept:719047548219949136> Set Status to " + msg[2], delete_after=10)
        elif msg[1].lower() == "code":
            msg[2] = " ".join(msg[2:])
            try:
                await client.party.set_custom_key(msg[2])
                await message.channel.send("<:Accept:719047548219949136> Set Matchmaking Code to " + msg[2], delete_after=10)
            except fortnitepy.errors.Forbidden:
                await message.channel.send("<:Reject:719047548819472446> I am Not Party Leader!", delete_after=10)
        elif msg[1].lower() == "playlist" or msg[1].lower() == "gamemode" or msg[1].lower() == "mode":
            msg[2] = " ".join(msg[2:])
            if msg[2].startswith("Playlist_"):
                await client.party.set_playlist(msg[2])
                await message.channel.send("<:Accept:719047548219949136> Set Playlist to " + msg[2], delete_after=10)
            else:
                playlist = get_playlist(name=msg[2])
                if list(playlist.keys()) == ['error']:
                    await message.channel.send("<:Reject:719047548819472446> Cannot Find Playlist " + msg[2], delete_after=10)
                else:
                    try:
                        await client.party.set_playlist(playlist['id'])
                        await message.channel.send("<:Accept:719047548219949136> Set Playlist to " + playlist['name'], delete_after=10)
                    except fortnitepy.errors.Forbidden:
                        await message.channel.send("<:Reject:719047548819472446> I am Not Party Leader!", delete_after=10)
        elif msg[1].lower() == "variants" or msg[1].lower() == "variant":
            variants = convert(msg[3:])
            if msg[2].lower() == "outfit" or msg[2].lower() == "skin":
                await client.party.me.edit_and_keep(partial(client.party.me.set_outfit,
                    asset=client.party.me.outfit,
                    variants=client.party.me.create_variants(
                        item="AthenaCharacter",
                        **variants
                    )
                ))
                await message.channel.send("<:Accept:719047548219949136> Set Variants to " + str(variants), delete_after=10)
            elif msg[2].lower() == "backbling" or msg[2].lower() == "backpack":
                await client.party.me.edit_and_keep(partial(client.party.me.set_backpack,
                    asset=client.party.me.backpack,
                    variants=client.party.me.create_variants(
                        item="AthenaBackpack",
                        **variants
                    )
                ))
                await message.channel.send("<:Accept:719047548219949136> Set Variants to " + str(variants), delete_after=10)
            elif msg[2].lower() == "harvesting_tool" or msg[2].lower() == "harvestingtool" or msg[2].lower() == "pickaxe":
                await client.party.me.edit_and_keep(partial(client.party.me.set_pickaxe,
                    asset=client.party.me.pickaxe,
                    variants=client.party.me.create_variants(
                        item="AthenaPickaxe",
                        **variants
                    )
                ))
                await message.channel.send("<:Accept:719047548219949136> Set Variants to " + str(variants), delete_after=10)
        elif msg[1].lower() == "enlightenment" or msg[1].lower() == "enlighten":
            if msg[2].lower() == "outfit" or msg[2].lower() == "skin":
                await client.party.me.edit_and_keep(partial(client.party.me.set_outfit,
                    asset=client.party.me.outfit,
                    variants=client.party.me.outfit_variants,
                    enlightenment=(msg[3], msg[4])
                ))
                await message.channel.send("<:Accept:719047548219949136> Set Enlightenment to Season " + msg[3] + " Level " + msg[4], delete_after=10)
            elif msg[2].lower() == "backbling" or msg[2].lower() == "backpack":
                await client.party.me.edit_and_keep(partial(client.party.me.set_backpack,
                    asset=client.party.me.backpack,
                    variants=client.party.me.backpack_variants,
                    enlightenment=(msg[3], msg[4])
                ))
                await message.channel.send("<:Accept:719047548219949136> Set Enlightenment to Season " + msg[3] + " Level " + msg[4], delete_after=10)
            elif msg[2].lower() == "harvesting_tool" or msg[2].lower() == "harvestingtool" or msg[2].lower() == "pickaxe":
                await client.party.me.edit_and_keep(partial(client.party.me.set_pickaxe,
                    asset=client.party.me.pickaxe,
                    variants=client.party.me.pickaxe_variants,
                    enlightenment=(msg[3], msg[4])
                ))
                await message.channel.send("<:Accept:719047548219949136> Set Enlightenment to Season" + msg[3] + " Level " + msg[4], delete_after=10)
    elif msg[0].lower() == "friend":
        msg[2] = " ".join(msg[2:])
        p = await client.fetch_profile(msg[2])
        if p is None:
            return
        if msg[1].lower() == "add":
            await client.add_friend(p.id)
            await message.channel.send("<:Accept:719047548219949136> Sent Friend Request to " + p.display_name, delete_after=10)
        elif msg[1].lower() == "remove":
            p = client.get_friend(p.id)
            if p is None:
                await message.channel.send("<:Reject:719047548819472446> Not Friends with " + p.display_name, delete_after=10)
                return
            await p.remove()
            await message.channel.send("<:Accept:719047548219949136> Removed " + p.display_name, delete_after=10)
    elif msg[0].lower() == "send":
        msg[1] = " ".join(msg[1:])
        await client.party.send(msg[1])
        await message.channel.send("<:Accept:719047548219949136> Sent Party Message", delete_after=10)
    elif msg[0].lower() == "clone" or msg[0].lower() == "copy":
        msg[1] = " ".join(msg[1:])
        p = await client.fetch_profile(msg[1])
        if p is None:
            return
        p = client.party.get_member(p.id)
        if p is None:
            return
        await client.party.me.edit_and_keep(
            partial(
                client.party.me.set_outfit,
                asset=p.outfit,
                variants=p.outfit_variants
            ),
            partial(
                client.party.me.set_backpack,
                asset=p.backpack,
                variants=p.backpack_variants
            ),
            partial(
                client.party.me.set_pickaxe,
                asset=p.pickaxe,
                variants=p.pickaxe_variants
            ),
            partial(
                client.party.me.set_banner,
                icon=p.banner[0],
                color=p.banner[1],
                season_level=p.banner[2]
            ),
            partial(
                client.party.me.set_battlepass_info,
                has_purchased=p.battlepass_info[0],
                level=p.battlepass_info[1],
                self_boost_xp=p.battlepass_info[2],
                friend_boost_xp=p.battlepass_info[3]
            )
        )
        await message.channel.send("<:Accept:719047548219949136> Cloned " + p.display_name, delete_after=10)
    elif msg[0].lower() == "variants":
        if len(msg) < 2:
            return
        elif msg[1].lower() == "outfit" or msg[1].lower() == "skin":
            cosm = aerial.cosmetic(client.party.me.outfit, "AthenaCharacter")
        elif msg[1].lower() == "backbling" or msg[1].lower() == "backpack":
            cosm = aerial.cosmetic(client.party.me.backpack, "AthenaBackpack")
        elif msg[1].lower() == "harvesting_tool" or msg[1].lower() == "harvestingtool" or msg[1].lower() == "pickaxe":
            cosm = aerial.cosmetic(client.party.me.pickaxe, "AthenaPickaxe")
        else:
            cosm = aerial.cosmetic(" ".join(msg[1:]))
        if cosm is None:
            await message.channel.send("<:Reject:719047548819472446> Cannot Find Cosmetic " + msg[1])
            return
        elif "variants" not in list(cosm.keys()):
            await message.channel.send("<:Reject:719047548819472446> " + cosm['name'] + " has no variants")
            return
        await message.channel.send(embed=discord.Embed(
            title="Variants for " + cosm['name'],
            type="rich"
        ).set_thumbnail(
            url=cosm['icons']['icon']
        ).add_field(
            name="Description",
            value=cosm['description'] + "\n" + cosm['setText'],
            inline=True
        ).add_field(
            name="ID",
            value=cosm['id'],
            inline=True
        ), delete_after=300)
        for ch in cosm['variants']:
            embed = discord.Embed(
                title=ch['channel'],
                type="rich"
            )
            for st in ch['options']:
                embed.add_field(
                    name=st['tag'],
                    value=st['name'],
                    inline=True
                )
            await message.channel.send(embed=embed, delete_after=300)
    return True


###################
#     Discord     #
###################

loop.create_task(dclient.start(os.getenv("TOKEN")))


@dclient.event
async def on_ready():
    channel = dclient.get_channel(720787276329910363)
    membercount = dclient.get_channel(727141497081954364)
    guildcount = dclient.get_channel(727599283179749466)
    while True:
        name = str(len(owner)) + "/" + str(len(clients)) + " Clients Running"
        if name != channel.name:
            await channel.edit(
                name=name
            )
            membercounter = str(dclient.get_guild(718842309998805022).member_count) + " Members"
            if membercounter != membercount.name:
                await membercount.edit(
                    name=membercounter
                )
                guildcounter = str(len(dclient.guilds)) + " Guilds"
                if guildcounter != guildcount.name:
                    await guildcount.edit(
                        name=guildcounter
                    )
        await asyncio.sleep(300)


@dclient.event
async def on_message(message: discord.Message):
    if message.channel.id == 718979003968520283:
        if "start" in message.content.lower():
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            await start_bot(message.author, 5400)
        else:
            await message.delete()
    elif type(message.channel) == discord.DMChannel:
        await parse_command(message)
    else:
        await dclient.process_commands(message)


@dclient.command(name="create", aliases=["start", "startbot", "createbot"])
async def create(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    await start_bot(ctx.author, 1800)


@dclient.command(name="kill", aliases=["stop", "end"])
async def kill(ctx):
    if ctx.author.id not in list(owner.keys()):
        await ctx.send(ctx.author.mention + " :x: No Active Session Found!")
        return
    try:
        await ctx.send(ctx.author.mention + " Attempting to kill session... (Timeout of 60 seconds)")
        await asyncio.wait_for(
            stop_bot(
                owner[ctx.author.id],
                ctx.author.id,
                "The bot was killed via `a.kill`",
                0
            ), timeout=60.0)
        await ctx.send(":white_check_mark: Killed Session!")
    except asyncio.TimeoutError:
        await ctx.send(ctx.author.mention + " :x: Could not kill session. Maybe try again? (TimeoutError)")
    except:
        await ctx.send(ctx.author.mention + " :x: Could not kill session. Maybe try again? (UnknownError)")


for a in accounts:
    client = aerial.DisposableClient(
        name=a,
        details={
            "email": accounts[a]['Email'],
            "password": accounts[a]['Password'],
            "account_id": accounts[a]['Account ID'],
            "device_id": accounts[a]['Device ID'],
            "secret": accounts[a]['Secret']
        }
    )
    clients[a] = client
    available[a] = client


loop.run_forever()
