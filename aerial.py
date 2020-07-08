import fortnitepy
import requests
import asyncio
import json
from aiohttp import TCPConnector
from functools import partial

###
# Cosmetic Functions
###


def cosmetic(name_or_id: str, type: str = None):
    if name_or_id.startswith((
            "CID_",
            "BID_",
            "EID_",
            "Emoji_",
            "Pickaxe_ID_"
    )):
        item = requests.get(
            "https://benbotfn.tk/api/v1/cosmetics/br/" + name_or_id
        )

        if item.status_code == 404:
            return {
                "name": name_or_id,
                "id": name_or_id
            }
        else:
            return item.json()

    else:
        item = requests.get(
            "https://benbotfn.tk/api/v1/cosmetics/br/search",
            params={
                "lang": "en",
                "searchLang": "en",
                "matchMethod": "contains",
                "name": name_or_id,
                "backendType": type
            }
        )

        if item.status_code == 404:
            return None
        else:
            return item.json()


def playlist(name_or_id: str):
    if name_or_id.startswith("Playlist_"):
        return name_or_id

    else:
        id = requests.get(
            "https://scuffedapi.xyz/api/playlists/search",
            params={
                "displayName": name_or_id
            }
        )

        if id.status_code == 404:
            return None
        else:
            return id.json().get("id", None)

###
# Clients
###


class DisposableClient(fortnitepy.Client):

    def __init__(self, name: str, details: dict):
        self.name = name
        self.task = None

        super().__init__(
            platform=fortnitepy.Platform.MAC,
            connector=TCPConnector(limit=None),
            auth=fortnitepy.AdvancedAuth(**details)
        )

class SelfHostClient(fortnitepy.Client):

    def __init__(self, config: dict):
        self.config = config

        super().__init__(
            platform=config.get("Platform", "WIN"),
            connector=TCPConnector(limit=None),
            auth=fortnitepy.AdvancedAuth(
                
            )
        )


class PublicClient(fortnitepy.Client):

    def __init__(self, details: dict):
        super().__init__(
            platform=fortnitepy.Platform.XBOX,
            connector=TCPConnector(limit=None),
            auth=fortnitepy.AdvancedAuth(**details),
            default_party_config=fortnitepy.DefaultPartyConfig(
                privacy=fortnitepy.PartyPrivacy.PUBLIC,
                team_change_allowed=False,
                chat_enabled=False
            )
        )


    async def refresh_status(self, member: fortnitepy.PartyMember = None):
        if self.party.member_count < 4:
            await self.set_status(f"🍀 {self.party.member_count}/16 | {len(self.friends)} Users")
        elif self.party.member_count < 8:
            await self.set_status(f"🔶 {self.party.member_count}/16 | {len(self.friends)} Users")
        else:
            await self.set_status(f"🛑 {self.party.member_count}/16 | {len(self.friends)} Users")


    async def event_ready(self):
        await self.refresh_status()
        for f in list(self.pending_friends.values()):
            if type(f) == fortnitepy.IncomingPendingFriend:
                await f.accept()

        await self.party.me.edit_and_keep(
            partial(
                self.party.me.set_outfit,
                "CID_565_Athena_Commando_F_RockClimber"
            ),
            partial(
                self.party.me.set_backpack,
                "BID_122_HalloweenTomato"
            ),
            partial(
                self.party.me.set_banner,
                icon="otherbanner31",
                color="defaultcolor3",
                season_level=1337
            )
        )

        self.set_avatar(
            fortnitepy.Avatar(
                asset="CID_565_Athena_Commando_F_RockClimber",
                background_colors=[
                    "7c0dc8",
                    "b521cc",
                    "ed34d0"
                ]
            )
        )

        self.add_event_handler("event_party_member_join", self.refresh_status)
        self.add_event_handler("event_party_member_leave", self.refresh_status)

    async def event_party_invite(self, invitation: fortnitepy.ReceivedPartyInvitation):
        await invitation.decline()
        await invitation.sender.invite()

    async def event_friend_request(self, request: fortnitepy.IncomingPendingFriend):
        if request.direction == "INBOUND":
            await request.accept()

    async def event_party_member_confirm(self, confirmation: fortnitepy.PartyJoinConfirmation):
        if self.party.me.leader:
            await confirmation.confirm()
        else:
            friend = self.get_friend(confirmation.user.id)

            if friend is not None:
                await friend.send("Your request to join the party was declined because the bot is not leader.")

            await confirmation.reject()

###
# Client Functions
###


async def start(client, timeout: float):

    loop = asyncio.get_running_loop()
    client.task = loop.create_task(client.start())

    try:
        await asyncio.wait_for(
            client.wait_until_ready(),
            timeout=timeout
        )

    except asyncio.TimeoutError:
        client.task.cancel()
        del client.task
        return False

    else:
        for f in list(client.friends.values()):
            await f.remove()

        for f in list(client.pending_friends.values()):
            await f.decline()

        await client.party.me.edit_and_keep(
            partial(
                client.party.me.set_outfit,
                "CID_565_Athena_Commando_F_RockClimber"
            ),
            partial(
                client.party.me.set_backpack,
                "BID_122_HalloweenTomato"
            ),
            partial(
                client.party.me.set_banner,
                icon="otherbanner31",
                color="defaultcolor3",
                season_level=1337
            )
        )

        client.set_avatar(
            fortnitepy.Avatar(
                asset="CID_565_Athena_Commando_F_RockClimber",
                background_colors=[
                    "7c0dc8",
                    "b521cc",
                    "ed34d0"
                ]
            )
        )

        return True


async def stop(client, timeout: float):

    try:
        await asyncio.wait_for(
            client.wait_until_ready(),
            timeout=10.0
        )

    except asyncio.TimeoutError:
        pass

    else:
        for f in list(client.friends.values()):
            await f.remove()

        for f in list(client.pending_friends.values()):
            await f.decline()

    try:
        await asyncio.wait_for(
            client.close(),
            timeout=timeout
        )

    except asyncio.TimeoutError:

        if client.task is not None:
            task.cancel()
            return True
        else:
            return False

    else:
        return True
