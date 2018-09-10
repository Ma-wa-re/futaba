#
# journal/impl/channel_output.py
#
# futaba - A Discord Mod bot for the Programming server
# Copyright (c) 2017 Jake Richardson, Ammon Smith, jackylam5
#
# futaba is available free of charge under the terms of the MIT
# License. You are free to redistribute and/or modify it under those
# terms. It is distributed in the hopes that it will be useful, but
# WITHOUT ANY WARRANTY. See the LICENSE file for more details.
#

'''
A Listener that outputs messages to the configured Discord channel.
'''

import logging

from ..listener import Listener

logger = logging.getLogger(__name__)

__all__ = [
    'ICONS',
    'ChannelOutputListener',
]

ICONS = {
    # Logging levels
    'info': '\N{INFORMATION SOURCE}',
    'idea': '\N{ELECTRIC LIGHT BULB}',
    'warning': '\N{WARNING SIGN}',
    'error': '\N{CROSS MARK}',
    'forbidden': '\N{NO ENTRY}',
    'critical': '\N{SQUARED SOS}',
    'ok': '\N{SQUARED OK}',
    'announce': '\N{CHEERING MEGAPHONE}',

    # Moderation
    'ban': '\N{HAMMER}',
    'kick': '\N{WOMANS BOOTS}',
    'muffled': '\N{FACE WITH MEDICAL MASK}',
    'mute': '\N{SPEAK-NO-EVIL MONKEY}',
    'jail': '\N{POLICE CARS REVOLVING LIGHT}',

    # Filter
    'flag': '\N{TRIANGULAR FLAG ON POST}',
    'deleted': '\N{SKULL}',
    'nsfw': '\N{NO ONE UNDER EIGHTEEN SYMBOL}',

    # Mail
    'has-mail': '\N{OPEN MAILBOX WITH RAISED FLAG}',
    'no-mail': '\N{CLOSED MAILBOX WITH LOWERED FLAG}',

    # Watchdog
    'investigate': '\N{SLEUTH OR SPY}',
    'watch': '\N{EYE}',

    # Configuration
    'edit': '\N{MEMO}',
    'save': '\N{FLOPPY DISK}',
    'writing': '\N{WRITING HAND}',
    'settings': '\N{HAMMER AND WRENCH}',

    # Development
    'deploy': '\N{ROCKET}',
    'package': '\N{PACKAGE}',
    'script': '\N{SCROLL}',

    # Security
    'key': '\N{KEY}',
    'lock': '\N{LOCK}',
    'unlock': '\N{OPEN LOCK}',

    # Documents
    'folder': '\N{OPEN FILE FOLDER}',
    'file': '\N{PAGE FACING UP}',
    'book': '\N{NOTEBOOK WITH DECORATIVE COVER}',
    'upload': '\N{OUTBOX TRAY}',
    'download': '\N{INBOX TRAY}',
    'bookmark': '\N{BOOKMARK}',
    'journal': '\N{LEDGER}',
    'attachment': '\N{PAPERCLIP}',
    'clipboard': '\N{CLIPBOARD}',
    'pin': '\N{PUSHPIN}',
    'briefcase': '\N{BRIEFCASE}',
    'cabinet': '\N{CARD FILE BOX}',
    'trash': '\N{WASTEBASKET}',

    # Miscellaneous
    'hourglass': '\N{HOURGLASS WITH FLOWING SAND}',
    'person': '\N{BUST IN SILHOUETTE}',
    'navigate': '\N{COMPASS}',
    'bot': '\N{ROBOT FACE}',
    'news': '\N{NEWSPAPER}',
    'art': '\N{ARTIST PALETTE}',
    'tag': '\N{TICKET}',
    'music': '\N{MUSICAL NOTE}',
    'link': '\N{LINK SYMBOL}',
    'alert': '\N{BELL}',
    'game': '\N{VIDEO GAME}',
    'search': '\N{LEFT-POINTING MAGNIFYING GLASS}',
    'bomb': '\N{BOMB}',
    'gift': '\N{WRAPPED PRESENT}',
    'celebration': '\N{PARTY POPPER}',
    'international': '\N{GLOBE WITH MERIDIANS}',
    'award': '\N{TROPHY}',
    'luck': '\N{FOUR LEAF CLOVER}',
}

class ChannelOutputListener(Listener):
    def __init__(self, router, path, channel, recursive=True, filter=None):
        super().__init__(router, path, recursive, filter)
        self.channel = channel

    def filter(self, path, guild, content, attributes):
        '''
        Ensures that this event is actually meant for this channel output logger.
        '''

        if self.channel not in guild.channels:
            logger.debug("Skipping event, wrong guild!")
            return False

        return True

    async def handle(self, path, guild, content, attributes):
        '''
        Send the message to the given channel, applying the icon if applicable.
        '''

        icon = attributes.get('icon', None)
        if icon is not None:
            content = f'{ICONS[icon]} {content}'

        logger.info("Received journal event on %s: '%s'", path, content)
        await self.channel.send(content=content)
