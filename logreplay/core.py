import asyncio
import aiohttp
import random
import logging
import janus


EVENT_LOOP = asyncio.get_event_loop()
REPLAY_QUEUE = janus.Queue(loop=EVENT_LOOP)  # 回放队列,生产者为中继器,消费者将会生成的异步请求
REPEAT_QUEUE = janus.Queue(loop=EVENT_LOOP)  # 中继队列,消费者为中继器,用于更改请求量
LOGGER = logging.getLogger(__name__)


async def repeater(repeat_q, replay_q, rate):
    """
    中继器
    :param repeat_q:
    :param replay_q:
    :param rate:
    :return:
    """
    while 1:
        parameters = await repeat_q.async_q.get()
        loop = rate
        while loop > 0:
            if loop >= 1:
                replay_q.async_q.put_nowait(parameters.copy())
            else:
                r = random.random()
                if r <= rate:
                    replay_q.async_q.put_nowait(parameters.copy())
            loop -= 1


async def request(client, method, url, **kwargs):
    """
    http请求函数
    :param method:
    :param url:
    :param kwargs:
    :return:
    """
    async with client.request(method, url, **kwargs) as response:
        return await response.read()


async def player(q):
    """
    请求发送器
    :param q:
    :return:
    """
    global EVENT_LOOP
    client = aiohttp.ClientSession(loop=EVENT_LOOP)
    while 1:
        parameters = await q.async_q.get()
        method = parameters.pop('method', 'get')
        url = parameters.pop('url')
        params = parameters.pop('param', None)
        data = parameters.pop('body', None)
        headers = parameters.pop('headers', None)
        await request(client, method, url, params=params, data=data, headers=headers, **parameters)