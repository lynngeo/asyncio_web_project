from models.db_op import create_pool
from models.dbstruct import User,Blog,Comment
import asyncio
from logall import *


async def test(loop):
    await create_pool(loop=loop,user='www-data',password='www-data',db='awesome')
    logging.info("create_pool finished")
    u = User(email="test@example.com",passwd='123456',admin=1,name='mytest',image='about:blank',created_at='0419')
    await u.update()

    # logging.info("user add finished")
    # b= Blog(user_id="111",user_name="bob",user_image="8937298",name="bob",summary="the test",\
    #     content="this is a small test")
    # await b.save()



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test(loop)) 