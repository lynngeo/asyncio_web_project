#!/usr/bin/env python3
# -*- coding: utf-8 -*-

' url handlers '

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post
from aiohttp import web
from config import configs

#rom models import Comment, Blog, next_id
#from models.db_op import 
#from models.dbstruct import User,Comment, Blog, next_id
from models.dbstruct import User, Comment, Blog, next_id
from apis import APIValueError,APIError,APIPermissionError

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs['session']['secret']

# @get('/')
# async def index(request):
#     users = await User.findAll()
#     logging.info('index start')
#     return {
#         '__template__': 'test.html',
#         'users': users
#     }

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermi
def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


async def cookie2user(cookie_str):
    '''
    parse cookie and load user if cookie is valid
    '''
    if not cookie_str:
        await None
        return 
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            await None
            return 
        uid, expires, sha1 = L
        if int(expires) < time.time():
            await None           
            return 
        user = await User.find(uid)
        if user is None:
            await None
            return
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            await None
            return 
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@get('/')
def blog(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

@get('/register')
def register():
    return {
        '__template__':'register.html'
    }

@get('/signin')
def signin():
    return {
        '__template__':'signin.html'
    }
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME,'-deleted-',max_age=0,httponly=True)
    logging.info('user signed out.')
    return r

# @get('/api/blogs')
# async def api_get_blogs()


@get('/api/users')
async def api_get_users(*,page='1'):
    # page_index = get_page_index(page)
    # num = yield from User.findNumber('count(id)')
    # p= Page(num,page_index)
    # if num == 0:
    #     return dict(page=p,users=())
    # users = yield from User.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    # for u in users:
    #     u.passwd='******'
    # return dict(page=p,users=users)
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd='******'
    return dict(users=users)



_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\+]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

@post('/api/users')
async def api_register_user(*,email,name,passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?',[email])
    if len(users)>0:
        raise APIError('register:failed','email','Email is already in use')
    uid = next_id()
    sha1_passwd = '%s:%s'%(uid,passwd)
    user = User(id=uid,name=name.strip(),email=email,passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),\
            image='http://www.gravatar.com/avatar/%s?d=mm&s=120'%hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    r=web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.passwd='******'
    r.content_type='application/json'
    r.body = json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r

@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r