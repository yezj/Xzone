# -*- coding: utf-8 -*-

import time
import zlib
import random
import pickle
import datetime
from twisted.internet import defer
from cyclone import escape, web
from front import storage
from front import utils
from front.utils import E
from front import D
# from front.handlers.base import BaseHandler
from front.wiapi import *
from front.handlers.base import ApiHandler, ApiJSONEncoder
# os.environ['DJANGO_SETTINGS_MODULE'] = 'back.settings'
from filebrowser.base import FileObject


class HomeHandler(ApiHandler):
    def get(self):
        self.render('index.html')


class CrossdomainHandler(ApiHandler):
    def get(self):
        self.render('crossdomain.xml')


@handler
class IndexHandler(ApiHandler):
    @utils.token
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Index', '/', [
        Param('channel', True, str, 'test1', 'test1', 'channel'),
        Param('user_id', False, str, '1', '1', 'user_id'),
        Param('access_token', False, str, '55526fcb39ad4e0323d32837021655300f957edc',
              '55526fcb39ad4e0323d32837021655300f957edc', 'access_token'),
    ], filters=[ps_filter], description="Index")
    def get(self):
        if self.has_arg('channel'):
            channels = yield self.sql.runQuery("SELECT id FROM core_channel WHERE slug=%s LIMIT 1",
                                               (self.arg("channel"),))
            if channels:
                channel, = channels[0]
            else:
                self.write(dict(err=E.ERR_CHANNEL, msg=E.errmsg(E.ERR_CHANNEL)))
                return

        else:
            self.write(dict(err=E.ERR_ARGUMENT, msg=E.errmsg(E.ERR_ARGUMENT)))
            return
        if channel:
            res = yield self.sql.runQuery("SELECT a.id, a.zoneid, a.domain, a.maxnum, a.status, a.index FROM"
                                          " core_zone AS a, core_zone_channels AS b WHERE a.id=b.zone_id AND"
                                          " b.channel_id=%s", (channel, ))
            zone_dict = {}
            record = {}
            if res:
                for r in res:
                    zid, zoneid, domain, maxnum, status, index = r
                    notice_dict = {}
                    notices = yield self.sql.runQuery(
                        "SELECT notice_id, position FROM core_noticeship WHERE zone_id=%s", (zid,))
                    if notices:
                        for n in notices:
                            notices = yield self.sql.runQuery("SELECT id, title, content, screenshot, sign,\
                              created_at FROM core_notice WHERE id=%s", (n[0],))
                            nid, title, content, screenshot, sign, create_at = notices[0]
                            if screenshot and FileObject(screenshot).exists():
                                url = FileObject(screenshot).url
                            else:
                                url = ''
                            create_at = time.mktime(create_at.timetuple())
                            position = n[1]
                            notice_dict[nid] = dict(title=title, content=content, url=url, sign=sign,
                                                    create_at=create_at, \
                                                    position=position)

                    try:
                        nownum = yield self.redis.get(
                            'zone:%s:%s' % (zoneid, datetime.datetime.now().strftime('%Y%m%d')))
                        if not nownum:
                            nownum = 0
                    except Exception:
                        nownum = 0

                    zone_dict[zoneid] = dict(domain=domain, maxnum=maxnum, nownum=nownum, status=status, index=index, \
                                             notices=notice_dict, title=D.ZONENAME.get(str(zoneid), ''))

                    if self.user_id:
                        idcard = yield self.redis.get('zone:%s:%s' % (zoneid, self.user_id))
                        if idcard:
                            record[zoneid] = idcard
                            # if rec:
                            #     rec = pickle.loads(rec)
                            #     record = rec
                        else:pass
                    #record[1] = '7he74dbd44fe7b43ef932ddc9ba612b0a7'
            ret = dict(zone=zone_dict, record=record, timestamp=int(time.time()))
            reb = zlib.compress(escape.json_encode(ret))
            self.write(ret)
        else:
            raise web.HTTPError(404)



class UpdateHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Update', '/update/', [
        Param('channel', True, str, 'test1', 'test1', 'channel'),
        Param('version', True, str, 'v1.1', 'v1.1', 'version'),
    ], filters=[ps_filter], description="Update")
    def get(self):
        try:
            channel = self.get_argument('channel', 'test1')
            version = str(self.get_argument('version'))
        except Exception:
            raise web.HTTPError(400, 'Argument error')

        channels = yield self.sql.runQuery(
            "SELECT id, version, version2, version3 FROM core_channel WHERE slug=%s LIMIT 1", (channel,))
        if channels:
            channel, nversion, mversion, uversion = channels[0]
        else:
            raise web.HTTPError(404)
        if version.split('.')[0] == nversion.split('.')[0]:
            max_version = nversion
        elif version.split('.')[0] == mversion.split('.')[0]:
            max_version = mversion
        else:
            max_version = uversion
        # try:
        #     assert version.split('.')[0] == nversion.split('.')[0]
        #     max_version = nversion
        # except Exception:
        #     max_version = mversion
        if cmp(version, max_version) == 0:
            ret = dict(code=0, timestamp=int(time.time()))
            reb = zlib.compress(escape.json_encode(ret))
            self.write(ret)
            return
        FIND = False
        res = yield self.sql.runQuery("SELECT cversion, tversion, url, sign FROM core_update WHERE channel_id=%s",
                                      (channel,))
        if res:
            for r in res:
                if version == str(r[0]) and max_version == str(r[1]):
                    FIND = True
                    code, target, url, md5 = 1, r[1], r[2], r[3]
                    ret = dict(code=code, msg='', targetVersion=target, upgrade=url, md5=md5,
                               timestamp=int(time.time()))
                    reb = zlib.compress(escape.json_encode(ret))
                    self.write(ret)
                    return
                else:
                    continue
        if not FIND:
            res = yield self.sql.runQuery(
                "SELECT version, url, md5 FROM core_upgrade WHERE channel_id=%s ORDER BY version DESC LIMIT 1",
                (channel,))
            if res:
                for r in res:
                    code, target, url, md5 = -1, r[0], r[1] or '', r[2] or ''
                    ret = dict(code=code, msg='', targetVersion=target, upgrade=url, md5=md5,
                               timestamp=int(time.time()))
                    reb = zlib.compress(escape.json_encode(ret))
                    self.write(ret)
                    return
            else:
                ret = dict(code=0, timestamp=int(time.time()))
                reb = zlib.compress(escape.json_encode(ret))
                self.write(ret)
                return

    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Update', '/update/', [
        Param('channel', True, str, 'test1', 'test1', 'channel'),
        Param('version', True, str, 'v1.1', 'v1.1', 'version'),
    ], filters=[ps_filter], description="Update")
    def post(self):
        try:
            channel = self.get_argument('channel', 'test1')
            version = str(self.get_argument('version'))
        except Exception:
            raise web.HTTPError(400, 'Argument error')

        channels = yield self.sql.runQuery("SELECT id, version FROM core_channel WHERE slug=%s LIMIT 1", (channel,))
        if channels:
            channel, max_version = channels[0]

        else:
            raise web.HTTPError(404)

        if cmp(version, max_version) == 0:
            ret = dict(code=0, timestamp=int(time.time()))
            reb = zlib.compress(escape.json_encode(ret))
            self.write(ret)
            return
        FIND = False
        res = yield self.sql.runQuery("SELECT cversion, tversion, url, sign FROM core_update WHERE channel_id=%s",
                                      (channel,))
        if res:
            for r in res:
                if version == str(r[0]) and max_version == str(r[1]):
                    FIND = True
                    code, target, url, md5 = 1, r[1], r[2], r[3]
                    ret = dict(code=code, msg='', targetVersion=target, upgrade=url, md5=md5,
                               timestamp=int(time.time()))
                    reb = zlib.compress(escape.json_encode(ret))
                    self.write(ret)
                    return
                else:
                    continue
        if not FIND:
            res = yield self.sql.runQuery(
                "SELECT version, url, md5 FROM core_upgrade WHERE channel_id=%s ORDER BY version DESC LIMIT 1",
                (channel,))
            if res:
                for r in res:
                    code, target, url, md5 = -1, r[0], r[1] or '', r[2] or ''
                    ret = dict(code=code, msg='', targetVersion=target, upgrade=url, md5=md5,
                               timestamp=int(time.time()))
                    reb = zlib.compress(escape.json_encode(ret))
                    self.write(ret)
                    return
            else:
                ret = dict(code=0, timestamp=int(time.time()))
                reb = zlib.compress(escape.json_encode(ret))
                self.write(ret)
                return



class BindHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Bind Token', '/bind/token/', [
        Param('channel', True, str, 'putaogame', 'putaogame', 'channel'),
        Param('thirdparty_token', True, str, '55526fcb3', '55526fcb3', 'thirdparty_token'),
        Param('access_token', True, str, '55526fcb39ad4e0323d32837021655300f957edc',
              '55526fcb39ad4e0323d32837021655300f957edc', 'access_token'),
    ], filters=[ps_filter], description="Bind Token")
    def post(self):
        try:
            channel = str(self.get_argument('realChannel'))
            thirdparty_token = str(self.get_argument('thirdparty_token'))
            access_token = str(self.get_argument('access_token'))
        except Exception:
            raise web.HTTPError(400, 'Argument error')
        channels = yield self.sql.runQuery("SELECT id FROM core_channel WHERE slug=%s LIMIT 1", (channel,))
        if channels:
            channel, = channels[0]
        else:
            raise web.HTTPError(404)
        try:
            res = yield self.sql.runQuery(
                "SELECT * FROM core_bindtoken WHERE channel_id=%s AND thirdparty_token=%s AND access_token=%s", \
                (channel, thirdparty_token, access_token))
            if not res:
                query = "INSERT INTO core_bindtoken(channel_id, thirdparty_token, access_token, timestamp) VALUES (%s, %s, %s, %s) RETURNING id"
                params = (channel, thirdparty_token, access_token, int(time.time()))
                for i in range(5):
                    try:
                        yield self.sql.runQuery(query, params)
                        break
                    except storage.IntegrityError:
                        log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                        continue
                yield self.redis.hset("bindtoken:%s" % channel, thirdparty_token, access_token)
        except Exception, e:
            print e

        ret = dict(timestamp=int(time.time()))
        reb = zlib.compress(escape.json_encode(ret))
        self.write(ret)


class GetHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Get Token', '/get/token/', [
        Param('channel', True, str, 'putaogame', 'putaogame', 'channel'),
        Param('realChannel', True, str, 'putaogame', 'putaogame', 'realChannel'),
        Param('thirdparty_token', True, str, '55526fcb3', '55526fcb3', 'thirdparty_token'),
    ], filters=[ps_filter], description="Get Token")
    def post(self):
        try:
            channel = str(self.get_argument('realChannel'))
            thirdparty_token = str(self.get_argument('thirdparty_token'))
        except Exception:
            raise web.HTTPError(400, 'Argument error')
        channels = yield self.sql.runQuery("SELECT id FROM core_channel WHERE slug=%s LIMIT 1", (channel,))
        if channels:
            channel, = channels[0]
        else:
            raise web.HTTPError(400, 'Argument error')
        try:
            res = yield self.sql.runQuery(
                "SELECT access_token FROM core_bindtoken WHERE channel_id=%s AND thirdparty_token=%s LIMIT 1", \
                (channel, thirdparty_token))
            if res:
                access_token, = res[0]
            else:
                access_token = yield self.redis.hget("bindtoken:%s" % channel, thirdparty_token)
                if not access_token:
                    access_token = ""
        except Exception:
            access_token = ""
        # access_token = yield self.redis.hget("bindtoken:%s" % channel, thirdparty_token)
        # if not access_token:
        #     access_token = ''
        ret = dict(access_token=access_token, timestamp=int(time.time()))
        reb = zlib.compress(escape.json_encode(ret))
        self.write(ret)


class IdcardHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Set idcard', '/set/idcard/', [
        Param('zoneid', True, str, '200', '200', 'zoneid'),
        Param('access_token', True, str, '05ba985f2cac3ec082353ebc1712a7c7fe5fe15d',
              '05ba985f2cac3ec082353ebc1712a7c7fe5fe15d', 'access_token'),
        Param('idcard', True, str, '69bc4774d14a4c28b14f255723cb8f99h1174', '69bc4774d14a4c28b14f255723cb8f99h1174',
              'idcard'),
    ], filters=[ps_filter], description="Set idcard")
    def post(self):
        try:
            zoneid = str(self.get_argument('zoneid'))
            access_token = str(self.get_argument('access_token'))
            idcard = str(self.get_argument('idcard'))
        except Exception:
            raise web.HTTPError(400, 'Argument error')
        yield self.redis.set('zone:%s:%s' % (zoneid, access_token), idcard)
        self.write('ok')


class FlushdbHandler(ApiHandler):
    @storage.databaseSafe
    # @defer.inlineCallbacks
    @api('Flushdb', '/flushdb/', [
    ], filters=[ps_filter], description="Flushdb")
    def post(self):
        self.write("START...\r\n")
        self.redis.flushdb()
        self.write("FLUSHDB SUCCESS")
