# -*- coding: utf-8 -*-
from openerp.tools.func import lazy_property
from openerp.tools import config as openerp_config
from openerp import http
from openerp.http import Root as OdooRoot
from openerp.http import OpenERPSession
from openerp.http import session_gc

from werkzeug.contrib.sessions import SessionStore

import cPickle
import logging
import redis

ONE_WEEK_IN_SECONDS = 60*60*24*7

logger      = logging.getLogger(__name__)


class RedisSessionStore(SessionStore):
    def __init__(self, redis, salt, *args, **kwargs):
        self.redis = redis
        self.generate_salt = salt
        self.key_template = 'session:%s'

        super(RedisSessionStore, self).__init__(*args, **kwargs)

    def new(self):
        return self.session_class({}, self.generate_key(self.generate_salt), True)

    def get_session_key(self, sid):
        if isinstance(sid, unicode):
            sid = sid.encode('utf-8')

        return self.key_template % sid

    def save(self, session):
        data = cPickle.dumps(dict(session))
        key = self.get_session_key(session.sid)
        try:
            return self.redis.setex(key, ONE_WEEK_IN_SECONDS, data)
        except Exception as ex:
            logger.error("Error on setting session data", exc_info = ex)

    def delete(self, session):
        try:
            key = self.get_session_key(session.sid)
            return self.redis.delete(key)
        except Exception as ex:
            logger.error("Error on deleting session data", exc_info = ex)

    def get(self, sid):
        if not self.is_valid_key(sid):
            return self.new()
        
        key = self.get_session_key(sid)
        try:
            saved = self.redis.get(key)
            data = cPickle.loads(saved) if saved else {}
        except Exception as ex:
            logger.error("Error on getting session data", exc_info = ex)
            data = {}
        return self.session_class(data, sid, False)


use_redis   = openerp_config.get('use_redis', False)

logger.debug("Enable Redis : {}".format(use_redis))

if use_redis:
    redis_host  = openerp_config.get('redis_host', 'localhost')
    redis_port  = openerp_config.get('redis_port', 6379)
    redis_salt  = openerp_config.get(
                    'redis_salt',
                    '-RMsSz~]3}4[Bu3_aEFx.5[57O^vH?`{X4R)Y3<Grvq6E:L?6#aoA@|/^^ky@%TI'
                    )

    logger.debug("Connecting Redis at {}:{}".format(redis_host, redis_port))

    # TODO: connection pool option
    redis_instance = redis.StrictRedis(
                        host=redis_host,
                        port=redis_port,
                        db=0
                        )


    class Root(OdooRoot):
        @lazy_property
        def session_store(self):
            return RedisSessionStore(
                    redis_instance,
                    redis_salt,
                    session_class=OpenERPSession)


    http.root = Root()

    # we do nothing for session_gc
    def redis_session_gc(session_store):
        pass

    http.session_gc = redis_session_gc
