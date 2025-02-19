import time
import os
from json.decoder import JSONDecodeError
import json
import aiohttp
import asyncio



class Sender(object):
    """Sends requests to Genius."""
    # Create a persistent requests connection
    API_ROOT = 'https://api.genius.com/'
    PUBLIC_API_ROOT = 'https://genius.com/api/'
    WEB_ROOT = 'https://genius.com/'

    def __init__(
        self,
        access_token=None,
        response_format='plain',
        timeout=5,
        sleep_time=0.2,
        retries=0,
        public_api_constructor=False,
    ):
        self._session = aiohttp.ClientSession(loop=asyncio.get_event_loop())
 
        if access_token is None:
            access_token = os.environ.get('GENIUS_ACCESS_TOKEN')

        if public_api_constructor:
            self.authorization_header = {}
        else:
            if not access_token or not isinstance(access_token, str):
                raise TypeError('Invalid token')
            self.access_token = 'Bearer ' + access_token
            self.authorization_header = {'authorization': self.access_token, 'application': 'LyricsGenius',
            'User-Agent': 'https://github.com/johnwmillr/LyricsGenius'}

        self.response_format = response_format.lower()
        self.timeout = timeout
        self.sleep_time = sleep_time
        self.retries = retries

    async def _make_request(
        self,
        path,
        method='GET',
        params_=None,
        public_api=False,
        web=False,
        **kwargs
    ):
        """Makes a request to Genius."""
        if public_api:
            uri = self.PUBLIC_API_ROOT
            header = None
        elif web:
            uri = self.WEB_ROOT
            header = None
        else:
            uri = self.API_ROOT
            header = self.authorization_header
        uri += path

        params_ = params_ if params_ else {}

        # Make the request
        response = None
        tries = 0
        while response is None and tries <= self.retries:
            tries += 1
            try:
                response = await self._session.get(url=uri,
                                                 timeout=self.timeout,
                                                 params=params_,
                                                 headers=header)
                response.raise_for_status()
            except asyncio.TimeoutError as e:
                error = "Request timed out:\n{e}".format(e=e)
                if tries > self.retries:
                    raise asyncio.TimeoutError(error)
            except aiohttp.ClientConnectorError as e:
              
                if response.status < 500 or tries > self.retries:
                    raise ClientConnectionError(response.status, e)

            # Enforce rate limiting
            await asyncio.sleep(self.sleep_time)

        if web:
            return await response.text()
        elif response.status == 200:
            res = await response.json()
            return res.get("response", res)
        elif response.status == 204:
            return 204
        else:
            raise AssertionError("Response status code was neither 200, nor 204! "
                                 "It was {}".format(response.status))


