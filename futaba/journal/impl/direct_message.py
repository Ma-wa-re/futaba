#
# journal/impl/direct_message.py
#
# futaba - A Discord Mod bot for the Programming server
# Copyright (c) 2017-2018 Jake Richardson, Ammon Smith, jackylam5
#
# futaba is available free of charge under the terms of the MIT
# License. You are free to redistribute and/or modify it under those
# terms. It is distributed in the hopes that it will be useful, but
# WITHOUT ANY WARRANTY. See the LICENSE file for more details.
#

"""
A Listener that DMs messages to the configured Discord user.
"""

import logging

from futaba.utils import copy_discord_file
from ..listener import Listener

logger = logging.getLogger(__name__)

__all__ = ["DirectMessageListener"]


class DirectMessageListener(Listener):
    def __init__(self, router, path, user, recursive=True):
        super().__init__(router, path, recursive)
        self.user = user

    async def handle(self, path, guild, content, attributes):
        """
        Send the message to the given channel, applying the icon if applicable.
        """

        if guild is not None:
            content = f"[{guild.name}] {content}"

        kwargs = {"content": content}

        if "embed" in attributes:
            kwargs["embed"] = attributes["embed"]
        if "file" in attributes:
            kwargs["file"] = copy_discord_file(attributes["file"])
        if "files" in attributes:
            kwargs["files"] = list(map(copy_discord_file, attributes["files"]))

        await self.user.send(**kwargs)
