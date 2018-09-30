#
# cogs/info/alias.py
#
# futaba - A Discord Mod bot for the Programming server
# Copyright (c) 2017-2018 Jake Richardson, Ammon Smith, jackylam5
#
# futaba is available free of charge under the terms of the MIT
# License. You are free to redistribute and/or modify it under those
# terms. It is distributed in the hopes that it will be useful, but
# WITHOUT ANY WARRANTY. See the LICENSE file for more details.
#

'''
Tracking for aliases of members, storing previous usernames, nicknames, and avatars.
'''

import asyncio
import logging
import re
from datetime import datetime

import discord
from discord.ext import commands

from futaba import permissions
from futaba.download import download_link
from futaba.enums import Reactions
from futaba.exceptions import SendHelp
from futaba.parse import get_user_id
from futaba.str_builder import StringBuilder
from futaba.utils import fancy_timedelta, user_discrim

logger = logging.getLogger(__package__)

__all__ = [
    'Alias',
]

EXTENSION_REGEX = re.compile(r'\.([a-z]+)\?.+$')

class MemberChanges:
    __slots__ = (
        'avatar_url',
        'username',
        'nickname',
    )

    def __init__(self):
        self.avatar_url = None
        self.username = None
        self.nickname = None

    def __bool__(self):
        for field in self.__slots__:
            if getattr(self, field) is not None:
                return True
        return False

class Alias:
    '''
    Cog for member alias information.
    '''

    __slots__ = (
        'bot',
        'journal',
    )

    def __init__(self, bot):
        self.bot = bot
        self.journal = bot.get_broadcaster('/alias')

    async def member_update(self, before, after):
        ''' Handles update of member information. '''

        changes = MemberChanges()
        timestamp = datetime.now()

        if before.avatar != after.avatar:
            logger.info("Member '%s' (%d) has changed their profile picture (%s)",
                    before.name, before.id, after.avatar)
            changes.avatar_url = after.avatar_url

        if before.name != after.name:
            logger.info("Member '%s' (%d) has changed name to '%s'",
                    before.name, before.id, after.name)
            changes.username = after.name

        if before.nick != after.nick and after.nick is not None:
            logger.info("Member '%s' (%d) has changed nick to '%s'",
                    before.display_name, before.id, after.nick)
            changes.nickname = after.nick

        # Check if there were any changes
        if not changes:
            return

        if changes.avatar_url is not None:
            avatar = await download_link(changes.avatar_url)
            match = EXTENSION_REGEX.match(changes.avatar_url)
            if match is None:
                raise ValueError(f"Avatar URL does not match extension regex: {changes.avatar_url}")
            avatar_ext = match[1]

        attrs = StringBuilder(sep=', ')
        with self.bot.sql.transaction():
            if changes.avatar_url is not None:
                self.bot.sql.alias.add_avatar(before, timestamp, avatar, avatar_ext)
                attrs.write(f'avatar: {changes.avatar_url}')
            if changes.username is not None:
                self.bot.sql.alias.add_username(before, timestamp, changes.username)
                attrs.write(f'name: {changes.username}')
            if changes.nickname is not None:
                self.bot.sql.alias.add_nickname(before, timestamp, changes.nickname)
                attrs.write(f'nick: {changes.nickname}')

        content = f'Member {user_discrim(before)} was updated: {attrs}'
        self.journal.send('member/update', before.guild, content, icon='person',
                before=before, after=after, changes=changes)

    @commands.command(name='aliases')
    async def aliases(self, ctx, *, name: str):
        ''' Gets information about known aliases of the given user. '''

        logger.info("Getting and printing alias information for some user '%s'", name)

        embed = discord.Embed(colour=discord.Colour.dark_teal())
        embed.set_author(name='Member alias information')

        user = await self.bot.find_user(name, ctx.guild)
        if user is None:
            embed.colour = discord.Colour.dark_red()
            embed.description = f'No user information found for `{name}`'

            await asyncio.gather(
                ctx.send(embed=embed),
                Reactions.FAIL.add(ctx.message),
            )
            return

        logger.debug("Found user! %r. Now fetching alias information...", user)
        avatars, usernames, nicknames, alt_user_ids = self.bot.sql.alias.get_aliases(ctx.guild, user)

        # Remove self from chain
        try:
            alt_user_ids.remove(user.id)
        except KeyError:
            pass

        if not any((avatars, usernames, nicknames, alt_user_ids)):
            embed.colour = discord.Colour.dark_purple()
            embed.description = f'No information found for {user.mention}'

            await asyncio.gather(
                ctx.send(embed=embed),
                Reactions.SUCCESS.add(ctx.message),
            )
            return

        embed.description = f'{user.mention}\n'
        content = StringBuilder()
        files = []

        if avatars:
            for i, (avatar_bin, avatar_ext, timestamp) in enumerate(avatars, 1):
                time_since = fancy_timedelta(timestamp)
                content.writeln(f'#{i} set {time_since} ago')
                files.append(discord.File(avatar_bin, filename=f'avatar {time_since}.{avatar_ext}'))
            embed.add_field(name='Past avatars', value=str(content))
            content.clear()

        if usernames:
            for username, timestamp in usernames:
                content.writeln(f'- `{username}` set {fancy_timedelta(timestamp)} ago')
            embed.add_field(name='Past usernames', value=str(content))
            content.clear()

        if nicknames:
            for nickname, timestamp in nicknames:
                content.writeln(f'- `{nickname}` set {fancy_timedelta(timestamp)} ago')
            embed.add_field(name='Past nicknames', value=str(content))
            content.clear()

        if alt_user_ids:
            for alt_user_id in alt_user_ids:
                content.writeln(f'<@!{alt_user_id}>')
            embed.add_field(name='Possible alts', value=str(content))

        await asyncio.gather(
            ctx.send(embed=embed, files=files),
            Reactions.SUCCESS.add(ctx.message),
        )

    @commands.group(name='alts')
    @commands.guild_only()
    async def alts(self, ctx):
        ''' Manages the list of suspected alternate accounts. '''

        if ctx.invoked_subcommand is None:
            raise SendHelp(ctx.command)

    @alts.command(name='add')
    @commands.guild_only()
    @permissions.check_mod()
    async def add_alt(self, ctx, first_name: str, second_name: str):
        ''' Add a suspected alternate account for a user. '''

        logger.info("Adding suspected alternate account pair for '%s' and '%s'",
                first_name, second_name)

        first_user, second_user = await asyncio.gather(
            self.bot.find_user(first_name, ctx.guild),
            self.bot.find_user(second_name, ctx.guild),
        )

        embed = discord.Embed(colour=discord.Colour.dark_red())
        content = StringBuilder()

        if first_user is None:
            content.writeln(f'No user information found for `{first_name}`')
        if second_user is None:
            content.writeln(f'No user information found for `{second_name}`')
        if content:
            embed.description = str(content)
            await asyncio.gather(
                ctx.send(embed=embed),
                Reactions.FAIL.add(ctx.message),
            )
            return

        with self.bot.sql.transaction():
            self.bot.sql.alias.add_possible_alt(ctx.guild, first_user, second_user)

        content = f'Added {first_user.mention} and {second_user.mention} as possible alt accounts.'
        self.journal.send('alt/add', ctx.guild, content, icon='item_add', users=[first_user, second_user])
        await Reactions.SUCCESS.add(ctx.message)

    @alts.command(name='delchain')
    @commands.guild_only()
    @permissions.check_mod()
    async def del_alt_chain(self, ctx, name: str):
        ''' Removes all suspected alternate accounts for a user. '''

        user = await self.bot.find_user(name, ctx.guild)
        if user is None:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'No user information found for `{name}`'
            await asyncio.gather(
                ctx.send(embed=embed),
                Reactions.FAIL.add(ctx.message),
            )
            return

        with self.bot.sql.transaction():
            self.bot.sql.alias.all_delete_possible_alts(ctx.guild, user)

        content = f"Removed all alt accounts in {user.mention}'s chain"
        self.journal.send('alt/clear', ctx.guild, content, icon='item_clear', user=user)
        await Reactions.SUCCESS.add(ctx.message)
