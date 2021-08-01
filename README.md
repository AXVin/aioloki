# aioloki
An asynchronous python logging handler to stream logs to Grafana Loki

## Installation
```
pip install aioloki
```

## Usage
```py
import asyncio
import logging
import aiohttp
import aioloki

async def main():
    session = aiohttp.ClientSession()
    handler = aioloki.AioLokiHandler(
        'http://localhost:3100',
        tags={'cluser': '1'},
        session=session
    )
    log = logging.getLogger('test-logging')
    log.addHandler(handler)
    log.info(
        'Setup aioloki successfully',
        extra={'tags': {'function': 'main'}}
    )
    await session.close()

asyncio.run(main())
```
