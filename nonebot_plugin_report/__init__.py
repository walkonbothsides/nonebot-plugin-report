from typing import Union, List

from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from nonebot import get_driver, get_bot
from nonebot.log import logger
from nonebot.drivers import ReverseDriver

from .config import Config


driver = get_driver()
config = Config.parse_obj(driver.config)

if not isinstance(driver, ReverseDriver) or not isinstance(driver.server_app, FastAPI):
    raise NotImplementedError('Only FastAPI reverse driver is supported.')


class Report(BaseModel):
    token: Union[str, None]
    title: Union[str, None] = None
    content: str
    send_to: Union[str, List[str], None] = None


app = FastAPI()

@app.post('/', status_code=200)
async def push(r: Report):
    if r.token is not None and r.token != config.token:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    msg = f'[report] {r.title or ""}\n{r.content}'
    if r.send_to is None:
        send_to = config.superusers
    elif isinstance(r.send_to, str):
        send_to = [r.send_to]
    else:
        send_to = r.send_to

    bot = get_bot()
    for id in send_to:
        await bot.send_msg(user_id=id, message=msg)


@driver.on_startup
async def startup():
    if config.token is None and config.environment == 'prod':
        logger.warning('You are running in production env without setting token.')

    driver.server_app.mount('/report', app)
