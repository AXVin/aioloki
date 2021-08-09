"""
Copyright (C) 2021-present  AXVin

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import copy
import logging
import asyncio
from typing import Dict, Optional

import aiohttp

from . import types

__all__ = (
    'AioLokiHandler',
)

class AioLokiHandler(logging.Handler):
    def __init__(
        self,
        url: str,
        /, *,
        session: aiohttp.ClientSession,
        tags: Optional[Dict[str, str]]=None,
    ) -> None:
        super().__init__()
        self._queue: asyncio.Queue[logging.LogRecord] = asyncio.Queue()
        self.url = url + '/loki/api/v1/push'
        self.session = session
        self.tags = tags
        self._task = asyncio.create_task(self._queue_worker())

    async def _queue_worker(self):
        try:
            while True:
                log = await self._queue.get()
                payload = self.build_payload(log)
                async with self.session.post(self.url, json=payload) as response:
                    if response.status != 204:
                        self._task.cancel()
                        break
        except asyncio.CancelledError:
            pass

    def build_tags(self, log: logging.LogRecord, /):
        tags = copy.deepcopy(self.tags) or {}
        tags['severity'] = log.levelname
        tags['logger'] = log.name
        try:
            extra_tags = log.tags # type: ignore
        except AttributeError:
            pass
        else:
            tags.update(extra_tags)
        return tags

    def build_payload(self, log: logging.LogRecord, /) -> types.LokiPayload:
        labels = self.build_tags(log)
        return {
            "streams": [{
                "stream": labels,
                "values": [
                    (str(int(log.created * 1e9)), self.format(log))
                ]
            }]
        }

    def emit(self, record: logging.LogRecord) -> None:
        self._queue.put_nowait(record)
