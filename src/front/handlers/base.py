# -*- coding: utf-8 -*-

import base64
import pickle
import time
import uuid
import json
import datetime
import random
from cyclone import web, escape
from django.db.models.query import QuerySet
from django.core.serializers.json import DjangoJSONEncoder
from twisted.internet import defer
from twisted.python import log
from front import storage, D
from front.utils import E


class BaseHandler(web.RequestHandler, storage.DatabaseMixin):

    def get_current_user(self):
        return None

    # def generate_token(self, **kwargs):
    #     token = base64.urlsafe_b64encode(pickle.dumps(kwargs))
    #     return token

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_inpour(self, user, rock):
        event = yield self.sql.runQuery("SELECT DISTINCT ON (a.bid)a.bid, a.created_at, a.ended_at, b.rid FROM core_bigevent AS a,\
          core_inpour AS b, core_inpour_bigevent AS c WHERE b.id=c.inpour_id AND a.id=c.bigevent_id ORDER BY a.bid")
        for e in event:
            bid, created_at, ended_at, rid = e
            created_at = int(time.mktime(created_at.timetuple()))
            ended_at = int(time.mktime(ended_at.timetuple()))
            now = int(time.mktime(datetime.datetime.now().timetuple()))
            if now >= created_at and now <= ended_at:
                query = "INSERT INTO core_userinpour (user_id, bid, rock) VALUES (%s, %s, %s) RETURNING id"
                params = (user['uid'], bid, rock)
                for i in range(5):
                    try:
                        yield self.sql.runQuery(query, params)
                        break
                    except storage.IntegrityError:
                        log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                        continue
        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_inpour(self, user):
        event = yield self.sql.runQuery("SELECT DISTINCT ON (a.bid)a.bid, a.created_at, a.ended_at, b.rid FROM core_bigevent AS a,\
          core_inpour AS b, core_inpour_bigevent AS c WHERE b.id=c.inpour_id AND a.id=c.bigevent_id ORDER BY a.bid")
        inpour = {}
        for e in event:
            bid, created_at, ended_at, rid = e
            created_at = int(time.mktime(created_at.timetuple()))
            ended_at = int(time.mktime(ended_at.timetuple()))
            now = int(time.mktime(datetime.datetime.now().timetuple()))
            if now >= created_at and now <= ended_at:
                res = yield self.sql.runQuery("SELECT SUM(rock) FROM core_userinpour WHERE user_id=%s AND bid=%s LIMIT 1", \
                                              (user['uid'], bid))
                if res:
                    rock, = res[0]
                    if not rock:
                        rock = 0
                else:
                    rock = 0
                inpour[bid] = int(rock)
        defer.returnValue(inpour)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def generate_sign(self, idcard, zone):
        ahex, aid = idcard.split('h', 1)
        res = yield self.sql.runQuery("SELECT state, user_id FROM core_account WHERE id=%s AND hex=%s LIMIT 1",
                                      (aid, ahex))
        if not res:
            raise E.USERNOTFOUND
        state, uid = res[0]
        if not uid and state == 0:
            uid = yield self.create_user()
            query = "UPDATE core_account SET user_id=%s WHERE id=%s"
            params = (uid, aid)
            for i in range(5):
                try:
                    yield self.sql.runOperation(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        if state != 0:
            if state == 2:
                raise E.USERABNORMAL
            elif state == 3:
                raise E.USERBEBANKED
            else:
                raise E.UNKNOWNERROR
        token = dict(uid=str(uid))
        s = base64.urlsafe_b64encode(pickle.dumps(token)).rstrip('=')
        sign = s[-1] + s[1:-1] + s[0]

        defer.returnValue(sign)

    def ping_server(self):
        return dict(domain=self.settings['domain'], notice='')

    @storage.databaseSafe
    @defer.inlineCallbacks
    def refresh_idcard(self, idcard, model, serial):
        if idcard:
            ahex, aid = idcard.split('h', 1)
            query = "UPDATE core_account SET model=%s, serial=%s, timestamp=%s WHERE id=%s AND hex=%s RETURNING id"
            params = (model, serial, int(time.time()), aid, ahex)
            for i in range(5):
                try:
                    res = yield self.sql.runQuery(query, params)
                    if not res:
                        idcard = None
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        if not idcard:

            ahex = uuid.uuid4().hex
            query = "INSERT INTO core_account(hex, state, user_id, model, serial, authmode, authstring, created, " \
                    "timestamp, accountid) VALUES (%s, 0, NULL, %s, %s, '', '', %s, %s, '') RETURNING id"
            params = (ahex, model, serial, int(time.time()), int(time.time()))
            for i in range(5):
                try:
                    res = yield self.sql.runQuery(query, params)
                    aid = res[0][0]
                    idcard = '%sh%s' % (ahex, aid)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        defer.returnValue(idcard)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def create_user(self):
        nuser = E.initdata4user()
        query = "INSERT INTO core_user(secret, name, nickname, avat, xp, gold, rock, feat, book, vrock, jextra, " \
                "jheros, jprods, jbatts, jseals, jtasks, jworks, jmails, jdoors, timestamp) VALUES " \
                "(%(secret)s, %(name)s, %(nickname)s, %(avat)s, %(xp)s, %(gold)s, %(rock)s, %(feat)s, %(book)s, %(vrock)s, %(jextra)s, " \
                "%(jheros)s, %(jprods)s, %(jbatts)s, %(jseals)s, %(jtasks)s, %(jworks)s, %(jmails)s, %(jdoors)s, " \
                "%(timestamp)s) RETURNING id"
        params = nuser
        params['name'] = str(uuid.uuid4().hex)[:20]
        params['secret'] = str(uuid.uuid4().hex)[:20]
        for i in range(5):
            try:
                res = yield self.sql.runQuery(query, params)
                uid = res[0][0]
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        for lot in D.LOTT.keys():
            query = "INSERT INTO core_freelott(user_id, lotttype, times, timestamp, free) VALUES (%s, %s, %s, %s, %s) RETURNING id"
            params = (uid, lot, 0, int(time.time()), True)
            for i in range(5):
                try:
                    yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue

        query = "INSERT INTO core_arena(user_id, arena_coin, before_rank, now_rank, last_rank, jguards, formation, timestamp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
        params = (uid, 0, uid, uid, uid, nuser['jheros'], E.default_formation, int(time.time()))
        for i in range(5):
            try:
                yield self.sql.runQuery(query, params)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        sender = D.ARENAMAIL['10004']['sender']
        title = D.ARENAMAIL['10004']['title']
        content = D.ARENAMAIL['10004']['content'] 
        awards = D.ARENAMAIL['10004']['jawards'] 
        yield self.send_mails(sender, uid, title, content, awards)
        yield self.set_arena(uid)
        yield self.redis.set('arenatimes:%s' % uid, 0)
        yield self.redis.set('arenatime:%s' % uid, int(time.time()))
        defer.returnValue(uid)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_user(self, uid):
        user = yield self.get_cache("user:%s" % uid)
        if not user:
            res = yield self.sql.runQuery("SELECT name, nickname, avat, xp, gold, rock, feat, book, jextra, jheros, jprods, "
                                          "jbatts, jseals, jtasks, jworks, jmails, jdoors, vrock FROM core_user WHERE id=%s "
                                          "LIMIT 1", (uid,))
            if not res:
                user = None
            else:
                r = res[0]
                try:
                    user = dict(uid=uid, name=r[0], nickname=r[1], avat=r[2], xp=r[3], gold=r[4], rock=r[5], feat=r[6], book=r[7], vrock=r[17])
                    user['extra'] = r[8] and escape.json_decode(r[8]) or {}
                    user['heros'] = r[9] and escape.json_decode(r[9]) or {}
                    user['prods'] = r[10] and escape.json_decode(r[10]) or {}
                    user['batts'] = r[11] and escape.json_decode(r[11]) or {}
                    user['seals'] = r[12] and escape.json_decode(r[12]) or {}
                    user['tasks'] = r[13] and escape.json_decode(r[13]) or {}
                    user['works'] = r[14] and escape.json_decode(r[14]) or {}
                    user['mails'] = r[15] and escape.json_decode(r[15]) or {}
                    user['doors'] = r[16] and escape.json_decode(r[16]) or {}
                    yield self.set_cache("user:%s" % uid, user)
                except Exception:
                    user = None
        defer.returnValue(user)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_user(self, uid, name=None, nickname=None, avat=None, xp=None, gold=None, rock=None, feat=None, book=None, extra=None,
                 heros=None, prods=None, batts=None, seals=None, tasks=None, works=None, mails=None, doors=None, vrock=None):
        suser = {'uid': uid}
        subqueries = []
        if name is not None:
            suser['name'] = name
            subqueries.append("name=%(name)s")
        if nickname is not None:
            suser['nickname'] = nickname
            subqueries.append("nickname=%(nickname)s")
        if avat is not None:
            suser['avat'] = avat
            subqueries.append("avat=%(avat)s")
        if xp is not None:
            suser['xp'] = xp
            subqueries.append("xp=%(xp)s")
        if gold is not None:
            suser['gold'] = gold
            subqueries.append("gold=%(gold)s")
        if rock is not None:
            suser['rock'] = rock
            subqueries.append("rock=%(rock)s")
        if feat is not None:
            suser['feat'] = feat
            subqueries.append("feat=%(feat)s")
        if book is not None:
            suser['book'] = book
            subqueries.append("book=%(book)s")
        if vrock is not None:
            suser['vrock'] = vrock
            subqueries.append("vrock=%(vrock)s")
        if extra is not None:
            suser['jextra'] = escape.json_encode(extra)
            subqueries.append("jextra=%(jextra)s")
        if heros is not None:
            suser['jheros'] = escape.json_encode(heros)
            subqueries.append("jheros=%(jheros)s")
        if prods is not None:
            suser['jprods'] = escape.json_encode(prods)
            subqueries.append("jprods=%(jprods)s")
        if batts is not None:
            suser['jbatts'] = escape.json_encode(batts)
            subqueries.append("jbatts=%(jbatts)s")
        if seals is not None:
            suser['jseals'] = escape.json_encode(seals)
            subqueries.append("jseals=%(jseals)s")
        if tasks is not None:
            suser['jtasks'] = escape.json_encode(tasks)
            subqueries.append("jtasks=%(jtasks)s")
        if works is not None:
            suser['jworks'] = escape.json_encode(works)
            subqueries.append("jworks=%(jworks)s")
        if mails is not None:
            suser['jmails'] = escape.json_encode(mails)
            subqueries.append("jmails=%(jmails)s")
        if doors is not None:
            suser['jdoors'] = escape.json_encode(doors)
            subqueries.append("jdoors=%(jdoors)s")
        suser['timestamp'] = str(int(time.time()))
        subqueries.append("timestamp=%(timestamp)s")
        # SQL UPDATE START
        query = "UPDATE core_user SET " + ",".join(subqueries) + " WHERE id=%(uid)s RETURNING name, nickname, avat, xp, gold, rock, feat, book, jextra," \
                                          "jheros, jprods, jbatts, jseals, jtasks, jworks, jmails, jdoors, vrock"
        params = suser
        user = None
        for i in range(5):
            try:
                res = yield self.sql.runQuery(query, params)
                if not res:
                    user = None
                    yield self.del_cache("user:%s" % uid)
                else:
                    r = res[0]
                    user = dict(uid=uid, name=r[0], nickname=r[1], avat=r[2], xp=r[3], gold=r[4], rock=r[5], feat=r[6], book=r[7], vrock=r[17])
                    user['extra'] = r[8] and escape.json_decode(r[8]) or {}
                    user['heros'] = r[9] and escape.json_decode(r[9]) or {}
                    user['prods'] = r[10] and escape.json_decode(r[10]) or {}
                    user['batts'] = r[11] and escape.json_decode(r[11]) or {}
                    user['seals'] = r[12] and escape.json_decode(r[12]) or {}
                    user['tasks'] = r[13] and escape.json_decode(r[13]) or {}
                    user['works'] = r[14] and escape.json_decode(r[14]) or {}
                    user['mails'] = r[15] and escape.json_decode(r[15]) or {}
                    user['doors'] = r[16] and escape.json_decode(r[16]) or {}
                    yield self.set_cache("user:%s" % uid, user)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        # SQL UPDATE END
        defer.returnValue(user)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_hp(self, user):
        uid = user['uid']
        hpmax = E.hpmax(user['xp'])
        hpup = E.hpup
        hptick = E.hptick
        hp = yield self.redis.hget("hp", uid)
        tick = 0
        if not hp:
            hpcur = hpmax
        else:
            timestamp, hpsnap = divmod(hp, 1000)
            if hpsnap >= hpmax:
                hpcur = hpsnap
            else:
                timenow = int(time.time()) - self.settings["timepoch"]
                n, r = divmod((timenow - timestamp), hptick)
                hpuped = hpsnap + n * hpup
                if hpuped < hpmax:
                    hpcur = hpuped
                    if r != 0:
                        tick = hptick - r
                    else:
                        tick = hptick
                else:
                    hpcur = hpmax
        defer.returnValue((hpcur, tick))

    @storage.databaseSafe
    @defer.inlineCallbacks
    def add_hp(self, user, value):
        uid = user['uid']
        hpmax = E.hpmax(user['xp']) + value
        hpup = E.hpup
        hptick = E.hptick
        hp = yield self.redis.hget("hp", uid)
        tick = 0
        timenow = int(time.time()) - self.settings["timepoch"]
        if not hp:
            #hpcur = hpmax
            hpcur, stick = yield self.get_hp(user)
            #print 'hpmax', hpmax
        else:
            timestamp, hpsnap = divmod(hp, 1000)
            if hpsnap >= hpmax:
                hpcur = hpsnap
            else:
                n, r = divmod((timenow - timestamp), hptick)
                hpuped = hpsnap + n * hpup
                if hpuped < hpmax:
                    hpcur = hpuped
                    if r != 0:
                        tick = hptick - r
                    else:
                        tick = hptick
                else:
                    hpcur = hpmax
        hpcur = hpcur + value
        if hpcur < hpmax:
            if hpcur < 0:
                hpcur = 0
            if 0 < tick < hptick:
                timetick = timenow - (hptick - tick)
            else:
                tick = hptick
                timetick = timenow
        else:
            #hpcur = hpmax
            timetick = timenow
        yield self.redis.hset("hp", uid, timetick * 1000 + hpcur)
        defer.returnValue((hpcur, tick))

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_prop(self, uid, label):
        prop = yield self.get_cache("prop:%s:%s" % (uid, label))
        if not prop:
            res = yield self.sql.runQuery("SELECT num,txt FROM core_prop WHERE user_id=%s AND label=%s LIMIT 1", (uid, label))
            if not res:
                prop = dict(uid=uid, label=label, num=None, txt=None)
                # SQL UPDATE START
                query = "INSERT INTO core_prop(user_id, label, num, txt, timestamp) VALUES (%(uid)s, %(label)s, %(num)s, %(txt)s," \
                        + str(int(time.time())) + ") RETURNING id"
                params = prop
                for i in range(5):
                    try:
                        yield self.sql.runQuery(query, params)
                        break
                    except storage.IntegrityError:
                        log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                        continue
                # SQL UPDATE END
            else:
                r = res[0]
                prop = dict(uid=uid, label=label, num=r[0], txt=r[1])
            yield self.set_cache(("prop:%s:%s" % (uid, label)), prop)
        defer.returnValue(prop)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_prop(self, uid, label, num=None, txt=None):
        prop = yield self.get_prop(uid, label)
        if prop:
            if num is not None:
                prop['num'] = num
            if txt is not None:
                prop['txt'] = txt
            yield self.set_cache(("prop:%s:%s" % (uid, label)), prop)
            # SQL UPDATE START
            query = "UPDATE core_prop SET num=%(num)s, txt=%(txt)s, timestamp=" \
                    + str(int(time.time())) + "WHERE user_id=%(uid)s AND label=%(label)s RETURNING id"
            params = prop
            for i in range(5):
                try:
                    res = yield self.sql.runQuery(query, params)
                    if not res:
                        query2 = "INSERT INTO core_prop(user_id, label, num, txt, timestamp) VALUES (%(uid)s, %(label)s, %(num)s, %(txt)s, " \
                                 + str(int(time.time())) + ") RETURNING id"
                        params2 = prop
                        for ii in range(5):
                            try:
                                yield self.sql.runQuery(query2, params2)
                                break
                            except storage.IntegrityError:
                                log.msg("SQL integrity error, retry(%i): %s" % (ii, (query2 % params2)))
                                continue
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
            # SQL UPDATE END
        defer.returnValue(prop)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_mails(self, user, mids):
        mails = [key for key in user['mails'] if user['mails'][key] == 0]
        print 'mails', mails
        ballmails = yield self.redis.get("allmails:%s" % user['uid'])
        if not ballmails:
            allmails = {}
            if mails:
                res = yield self.sql.runQuery("SELECT id, sender, title, content, jawards, created_at FROM core_mail WHERE to_id=%s AND id in %s ORDER BY created_at DESC", (user['uid'], tuple(mails)))
                if res:
                    for r in res:
                        mid = str(r[0])
                        mail = dict(mid=mid, sender=r[1], title=r[2], content=r[3], timestamp=time.mktime(r[5].timetuple()))
                        mail['awards'] = r[4] and escape.json_decode(r[4]) or {}
                        allmails[mid] = mail
            yield self.redis.set("allmails:%s" % user['uid'], pickle.dumps(allmails))
        else:
            allmails = pickle.loads(ballmails)
        mails = []
        for mid in mids:
            if mid in allmails:
                mails.append(allmails[mid])
        defer.returnValue(mails)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_mails(self, user):
        print 'mails', user['mails']
        uid = user['uid']
        res = yield self.sql.runQuery("SELECT id, sender, title, content, jawards, created_at FROM core_mail WHERE to_id=%s ORDER BY created_at DESC", (uid, ))
        for r in res:
            if str(r[0]) not in user['mails']:
                user['mails'][r[0]] = 0

        cuser = dict(mails=user['mails'])
        yield self.set_user(uid, **cuser)
        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_mails(self, user):
        mails = [key for key in user['mails'] if user['mails'][key] == 0]
        allmails = {}
        if mails:
            res = yield self.sql.runQuery("SELECT id, sender, title, content, jawards, created_at FROM core_mail WHERE to_id=%s AND id in %s ORDER BY created_at DESC", (user['uid'], tuple(mails)))
            if res:
                for r in res:
                    mid = str(r[0])
                    mail = dict(mid=mid, sender=r[1], title=r[2], content=r[3], timestamp=time.mktime(r[5].timetuple()))
                    mail['awards'] = r[4] and escape.json_decode(r[4]) or {}
                    allmails[mid] = mail
        yield self.redis.set("allmails:%s" % user['uid'], pickle.dumps(allmails))
        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def send_mails(self, sender, to_id, title, content, awards):
        query = "INSERT INTO core_mail(sender, to_id, title, content, jawards, comment, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"
        params = (sender, to_id, title, content, escape.json_encode(awards), '', datetime.datetime.now())
        for i in range(5):
            try:
                yield self.sql.runQuery(query, params)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue

        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_firstlott(self, user):
        res = yield self.sql.runQuery("SELECT user_id FROM core_firstlott WHERE user_id=%s AND first=True LIMIT 1",
                                      (user['uid'], ))
        firstlott = False
        if not res:
            query = "INSERT INTO core_firstlott(user_id, first, created_at) VALUES (%s, %s, %s) RETURNING id"
            params = (user['uid'], True, int(time.time()))
            for i in range(5):
                try:
                    yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue

            firstlott = True
        defer.returnValue(firstlott)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_daylott(self, user):
        res = yield self.sql.runQuery("select updated_at::date from core_daylott where updated_at::date=current_date")
        times = None
        if not res:
            query = "INSERT INTO core_daylott(user_id, times, updated_at) VALUES (%s, %s, %s) RETURNING times"
            params = (user['uid'], 1, datetime.datetime.now())
            for i in range(5):
                try:
                    times = yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        else:
            query = "UPDATE core_daylott SET times=times+1, updated_at=%s WHERE user_id=%s RETURNING times"
            params = (datetime.datetime.now(), user['uid'])
            for i in range(5):
                try:
                    times = yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        defer.returnValue(times)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_freelott(self, is_free, user, ltype):
        query = "UPDATE core_freelott SET times=times+1, free=%s, timestamp=%s WHERE user_id=%s AND lotttype=%s RETURNING times"
        params = (is_free, int(time.time()), user['uid'], ltype )
        for i in range(5):
            try:
                yield self.sql.runQuery(query, params)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_arenaresult(self, user, cid, result):
        uid = user['uid']
        now_rank = before_rank = 0
        res = yield self.sql.runQuery("SELECT a.now_rank, b.now_rank, a.before_rank, a.last_rank FROM (SELECT user_id, now_rank, before_rank, last_rank FROM core_arena WHERE user_id=%s) AS a, "
                                      "(SELECT user_id, now_rank, before_rank FROM core_arena WHERE user_id=%s) AS b", (uid, cid))
        if res:
            for r in res:
                now_rank = r[0]
                before_rank = r[2]
                last_rank = r[3]
                if r[0] > r[1]:
                    now_rank = r[1]
                    last_rank = r[0]
                    query = "UPDATE core_arena SET now_rank=%s, last_rank=%s WHERE user_id=%s  RETURNING id"
                    params = (now_rank, last_rank, uid)
                    for i in range(5):
                        try:
                            yield self.sql.runQuery(query, params)
                            break
                        except storage.IntegrityError:
                            log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                            continue
                    query = "UPDATE core_arena SET now_rank=%s WHERE user_id=%s RETURNING id"
                    params = (r[0], cid)
                    for i in range(5):
                        try:
                            yield self.sql.runQuery(query, params)
                            break
                        except storage.IntegrityError:
                            log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                            continue

        query = "INSERT INTO core_arenaresult(user_id, competitor_id, result, ascend, timestamp) VALUES (%s, %s, %s, %s, %s) RETURNING id"
        params = (uid, cid, result, last_rank-now_rank, int(time.time()))
        for i in range(5):
            try:
                yield self.sql.runQuery(query, params)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        yield self.set_arena(uid)
        yield self.set_arena(cid)
        defer.returnValue((now_rank, before_rank, last_rank))

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_arenarank(self, user, now_rank, before_rank, last_rank):
        now_rank, before_rank, last_rank = now_rank, before_rank, last_rank
        if now_rank < before_rank:
            query = "UPDATE core_arena SET before_rank=%s WHERE user_id=%s RETURNING id"
            params = (now_rank, user['uid'])
            for i in range(5):
                try:
                    yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
            awards = dict(rock=E.arenamatch(now_rank, before_rank))
            yield self.set_mails(user)
            now_rank, before_rank = now_rank, now_rank
        defer.returnValue((now_rank, before_rank, last_rank, awards))

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_arenaguard(self, uid, heros, formation):
        res = yield self.sql.runQuery("SELECT a.id, b.arena_coin, b.now_rank, a.jheros, b.jguards, b.formation, a.xp,"
                                      " a.nickname, a.avat FROM core_user AS a, core_arena AS b WHERE a.id=b.user_id AND a.id=%s" % uid)
        if res:
            for r in res:
                jheros = r[3] and escape.json_decode(r[3]) or {}
                jguards = {}
                jguards_list = filter(lambda j:j in jheros, heros)
                for j in jguards_list:
                    jguards[j] = jheros[j]
                query = "UPDATE core_arena SET jguards=%s, formation=%s WHERE user_id=%s RETURNING id"
                params = (escape.json_encode(jguards), formation, uid)
                for i in range(5):
                    try:
                        yield self.sql.runQuery(query, params)
                        break
                    except storage.IntegrityError:
                        log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                        continue
        yield self.set_arena(uid)
        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_arena(self, uid):
        res = yield self.sql.runQuery("SELECT a.id, b.arena_coin, b.now_rank, a.jheros, b.jguards, b.formation, a.xp,"
                                      " a.nickname, a.avat, b.before_rank, b.last_rank FROM core_user AS a, core_arena AS b WHERE a.id=b.user_id AND a.id=%s", (uid, ))
        if res:
            arenas = {r[0]: dict(uid=r[0],
                                 arena_coin=r[1],
                                 now_rank=r[2],
                                 heros=r[3] and escape.json_decode(r[3]) or {},
                                 guards=r[4] and escape.json_decode(r[4]) or {},
                                 win_times = 0,
                                 formation = r[5],
                                 xp=r[6],
                                 nickname=r[7],
                                 avat=r[8],
                                 before_rank=r[9],
                                 last_rank=r[10]
            ) for r in res}
            for k, v in arenas.iteritems():
                yield self.redis.set('arenas:%s' % k, pickle.dumps(v))
        defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_arena(self, uid):
        arenas = yield self.redis.get('arenas:%s' % uid)
        if arenas:
            arenas = pickle.loads(arenas)
            yield self.set_arena(uid)
        else:
            res = yield self.sql.runQuery("SELECT a.id, b.arena_coin, b.now_rank, a.jheros, b.jguards, b.formation, a.xp,"
                                          " a.nickname, a.avat, b.before_rank, b.last_rank FROM core_user AS a, core_arena AS b WHERE a.id=b.user_id AND a.id=%s LIMIT 1", (uid, ))
            if res:
                for r in res:
                    arenas = dict(uid=r[0],
                                  arena_coin=r[1],
                                  now_rank=r[2],
                                  heros=r[3] and escape.json_decode(r[3]) or {},
                                  guards=r[4] and escape.json_decode(r[4]) or {},
                                  win_times = 0,
                                  formation = r[5],
                                  xp=r[6],
                                  nickname=r[7],
                                  avat=r[8],
                                  before_rank=r[9],
                                  last_rank=r[10]
                    )
            else:
                arenas = None
        defer.returnValue(arenas)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def random_competitor(self, arenas, uid, num):
        arena_rule = []
        for i in xrange(0, len(D.ARENARULE)/8):
            if arenas['now_rank'] >= D.ARENARULE[i*8] and arenas['now_rank'] <= D.ARENARULE[i*8+1]:
                arena_rule.extend([D.ARENARULE[i*8+2], D.ARENARULE[i*8+3], D.ARENARULE[i*8+4], D.ARENARULE[i*8+5], \
                                   D.ARENARULE[i*8+6], D.ARENARULE[i*8+7]])
                break
        left = {}
        res = yield self.sql.runQuery("SELECT user_id, now_rank FROM core_arena WHERE user_id<>%s AND now_rank>=%s AND now_rank<=%s AND now_rank<%s ORDER BY now_rank limit %s", (uid, arena_rule[0], arena_rule[1], arenas['now_rank'], num))
        for r in res:
            arenas = yield self.get_arena(r[0])
            if arenas:
                left[r[0]] = dict(uid=arenas['uid'], guards=arenas['guards'], now_rank=arenas['now_rank'], nickname=arenas['nickname'], \
                                  xp=arenas['xp'], avat=arenas['avat'], win_times=arenas['win_times'], formation=arenas['formation'])
        middle = {}
        res = yield self.sql.runQuery("SELECT user_id, now_rank FROM core_arena WHERE user_id<>%s AND now_rank>=%s AND now_rank<=%s AND now_rank<%s ORDER BY now_rank limit %s", (uid, arena_rule[2], arena_rule[3], arenas['now_rank'], num))
        for r in res:
            arenas = yield self.get_arena(r[0])
            if arenas:
                arenas = pickle.loads(arenas)
                middle[r[0]] = dict(uid=arenas['uid'], guards=arenas['guards'], now_rank=arenas['now_rank'], nickname=arenas['nickname'], \
                                    xp=arenas['xp'], avat=arenas['avat'], win_times=arenas['win_times'], formation=arenas['formation'])
        right = {}
        res = yield self.sql.runQuery("SELECT user_id, now_rank FROM core_arena WHERE user_id<>%s AND now_rank>=%s AND now_rank<=%s AND now_rank<%s ORDER BY now_rank limit %s", (uid, arena_rule[4], arena_rule[5], arenas['now_rank'], num))
        for r in res:
            arenas = yield self.get_arena(r[0])
            if arenas:
                arenas = pickle.loads(arenas)
                right[r[0]] = dict(uid=arenas['uid'], guards=arenas['guards'], now_rank=arenas['now_rank'], nickname=arenas['nickname'], \
                                   xp=arenas['xp'], avat=arenas['avat'], win_times=arenas['win_times'], formation=arenas['formation'])

        competitor = dict(left=left, middle=middle, right=right)
        defer.returnValue(competitor)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_hunt(self, uid):
        hunts = yield self.redis.get('hunts:%s' % uid)
        if hunts:
            hunts = pickle.loads(hunts)
            # yield self.set_arena(uid)
        else:
            res = yield self.sql.runQuery("SELECT a.id, a.jheros, b.jguards, b.formation, a.xp,"
                                          " a.nickname, a.avat FROM core_user AS a, core_hunt AS b WHERE a.id=b.user_id AND a.id=%s LIMIT 1", (uid, ))
            if res:
                for r in res:
                    hunts = dict(uid=r[0],
                                  heros=r[1] and escape.json_decode(r[1]) or {},
                                  guards=r[2] and escape.json_decode(r[2]) or {},
                                  formation = r[3],
                                  xp=r[4],
                                  nickname=r[5],
                                  avat=r[6],
                    )
            else:
                arenas = None
        defer.returnValue(hunts)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def update_huntguard(self, uid, heros, formation):
        res = yield self.sql.runQuery("SELECT a.id, a.jheros, b.jguards, b.formation, a.xp, a.nickname, \
         a.avat FROM core_user AS a, core_hunt AS b WHERE a.id=b.user_id AND a.id=%s" % uid)
        if res:
            for r in res:
                jheros = r[1] and escape.json_decode(r[1]) or {}
                jguards = {}
                jguards_list = filter(lambda j:j in jheros, heros)
                for j in jguards_list:
                    jguards[j] = jheros[j]
                query = "UPDATE core_hunt SET jguards=%s, formation=%s WHERE user_id=%s RETURNING id"
                params = (escape.json_encode(jguards), formation, uid)
                for i in range(5):
                    try:
                        yield self.sql.runQuery(query, params)
                        break
                    except storage.IntegrityError:
                        log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                        continue
        #yield self.set_arena(uid)
        defer.returnValue(jguards.keys())

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_prison(self, user):
        res = yield self.sql.runQuery("SELECT prisoner_id, status, created_at, ended_at FROM core_prison WHERE user_id=%s", (user['uid'], ))
        wardens = {}
        if res:
            for r in res:
                if r[1]:
                    if int(time.time()) - r[2] > E.timer_by_reclaim:
                        interval = 0
                    else:
                        interval = E.timer_by_reclaim - (int(time.time()) - r[2])
                    if interval < 0:
                        interval = 0
                else:
                    interval = 0
                prisoner = yield self.get_user(r[0])
                wardens[r[0]] = dict(status=r[1], created_at=r[2], interval=interval, xp=prisoner['xp'], avat=prisoner['avat'], nickname=prisoner['nickname'])
        defer.returnValue(wardens)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_prison(self, user, cid, status, start=0):
        xp = user['xp']
        #根据等级开放监狱数量
        res = yield self.sql.runQuery("SELECT status, created_at FROM core_prison WHERE user_id=%s AND prisoner_id=%s LIMIT 1", (user['uid'], cid))
        if res:
            if not start:
                query = "UPDATE core_prison SET status=%s, created_at=%s, ended_at=%s WHERE user_id=%s AND prisoner_id=%s RETURNING id"
                params = (status, int(time.time()), int(time.time()), user['uid'], cid)
            else:
                query = "UPDATE core_prison SET status=%s, created_at=%s, ended_at=%s WHERE user_id=%s AND prisoner_id=%s RETURNING id"
                params = (E.idle, int(time.time()), int(time.time()), user['uid'], cid)

            for i in range(5):
                try:
                    yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        else:
            query = "INSERT INTO core_prison(user_id, prisoner_id, status, created_at, ended_at) VALUES (%s, %s, %s, %s, %s) RETURNING id"
            params = (user['uid'], cid, status, int(time.time()), int(time.time()))
            for i in range(5):
                try:
                    yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        res = yield self.sql.runQuery("SELECT prisoner_id, status, created_at, ended_at FROM core_prison WHERE user_id=%s", (user['uid'], ))
        if res:
            wardens = {r[0]:dict(status=r[1], created_at=r[2], ended_at=r[3]) for r in res}
            yield self.redis.set('wardens:%s' % user['uid'], pickle.dumps(wardens))
        defer.returnValue(wardens)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_release(self, user, cid, status):
        query = "INSERT INTO core_release(user_id, prisoner_id, status, created_at) VALUES (%s, %s, %s, %s) RETURNING id"
        params = (user['uid'], cid, status, int(time.time()))
        for i in range(5):
            try:
                pid = yield self.sql.runQuery(query, params)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        defer.returnValue(pid)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_card(self, user):
        t = datetime.datetime.today().date()
        timestamp = int(time.mktime(t.timetuple()))
        res = yield self.sql.runQuery("SELECT created_at, ended_at FROM core_card WHERE user_id=%s LIMIT 1", (user['uid'], ))
        lefttime = 0
        if res:
            created_at, ended_at = res[0]
            lefttime = (ended_at - timestamp)/24/3600
        defer.returnValue(lefttime)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_card(self, user, gid):
        is_first = 0
        t = datetime.datetime.today().date()
        timestamp = int(time.mktime(t.timetuple()))
        res = yield self.sql.runQuery("SELECT created_at, ended_at FROM core_card WHERE user_id=%s AND gid=%s LIMIT 1", (user['uid'], gid))
        if res:
            created_at, ended_at = res[0]
            if timestamp >= created_at and timestamp < ended_at:
                created_at = created_at
                ended_at = ended_at + 30*24*3600
            if timestamp >= ended_at:
                created_at = timestamp
                ended_at = timestamp + 30*24*3600

            query = "UPDATE core_card SET created_at=%s, ended_at=%s WHERE user_id=%s AND gid=%s RETURNING id"
            params = (created_at, ended_at, user['uid'], gid)
            lefttime = (ended_at - timestamp)/24/3600
            for i in range(5):
                try:
                    cid = yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        else:
            is_first = 1
            query = "INSERT INTO core_card(user_id, gid, created_at, ended_at) VALUES (%s, %s, %s, %s) RETURNING id"
            created_at = timestamp
            ended_at = created_at + 30*24*3600
            lefttime = (ended_at - timestamp)/24/3600
            params = (user['uid'], gid, created_at, ended_at)
            for i in range(5):
                try:
                    yield self.sql.runQuery(query, params)
                    break
                except storage.IntegrityError:
                    log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                    continue
        defer.returnValue([lefttime, is_first])

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_buyrecord(self, user, gid):
        res = yield self.sql.runQuery("SELECT * FROM core_buyrecord WHERE user_id=%s LIMIT 1", (user['uid'], ))
        if not res:
            sender = D.ARENAMAIL['10003']['sender']
            title = D.ARENAMAIL['10003']['title']
            content = D.ARENAMAIL['10003']['content'] 
            awards = D.ARENAMAIL['10003']['jawards'] 
            yield self.send_mails(sender, user['uid'], title, content, awards)

        query = "INSERT INTO core_buyrecord(user_id, gid, created_at) VALUES (%s, %s, %s) RETURNING id"
        params = (user['uid'], gid, int(time.time()))
        for i in range(5):
            try:
                rid = yield self.sql.runQuery(query, params)
                break
            except storage.IntegrityError:
                log.msg("SQL integrity error, retry(%i): %s" % (i, (query % params)))
                continue
        defer.returnValue(rid)



    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_cache(self, key, value, timeout=2592000):  # default 30 days
        yield self.redis.setex("cache:%s" % key, timeout, pickle.dumps(value))

    @storage.databaseSafe
    @defer.inlineCallbacks
    def del_cache(self, key):
        yield self.redis.delete("cache:%s" % key)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_cache(self, key):
        value = yield self.redis.get("cache:%s" % key)
        if value:
            defer.returnValue(pickle.loads(value))
        else:
            defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_flush(self, key, value):
        yield self.redis.setex("flush:%s" % key, 3600, pickle.dumps(value))

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_flush(self, key):
        value = yield self.redis.get("flush:%s" % key)
        if value:
            yield self.redis.delete("flush:%s" % key)
            defer.returnValue(pickle.loads(value))
        else:
            defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def set_uu(self, key, value):
        if key:
            yield self.redis.setex("uu:%s" % key, 60, pickle.dumps(value))
        else:
            defer.returnValue(None)

    @storage.databaseSafe
    @defer.inlineCallbacks
    def get_uu(self, key):
        if key:
            value = yield self.redis.get("uu:%s" % key)
            if value:
                defer.returnValue(pickle.loads(value))
            else:
                defer.returnValue(None)
        else:
            defer.returnValue(None)



class ApiHandler(BaseHandler):

    def _(self, message, plural_message=None, count=None):
        return self.locale.translate(message, plural_message, count)

    def auth_login(self, user):
        self.user_key = self.create_signed_value("user_id", str(user.id))
        self.set_cookie("user_id", self.user_key, expires_days=1)
        self._current_user = user

    def auth_logout(self):
        self.clear_cookie("user_id")
        self._current_user = None

    def has_arg(self, name):
        return self.request.arguments.has_key(name)

    def arg(self, name, default=web.RequestHandler._ARG_DEFAULT, strip=True):
        return self.get_argument(name, default, strip)

    def arg_bool(self, name):
        return self.arg(name, 'false') == 'true'

    def args(self, name, default=[], separator=','):
        value = self.get_argument(name, None)
        if value:
            return value.split(',')
        else:
            return ''

    def keyword_filte(self, content):
        return checkword.mark_filte(content)

    def out_content(self, content):
        return checkword.output(content)

    def static_media_url(self, url):
        return self.settings.get('static_url', '') + (url[0] == '/' and url[1:] or url)

    def file_url(self, f, tag='phone'):
        if f is None:
            return ''
        try:
            if hasattr(f, 'extra_thumbnails'):
                dpi = 1
                if dpi > 1 and f.extra_thumbnails.has_key('%dx%s' % (dpi, tag)):
                    f = f.extra_thumbnails['%dx%s' % (dpi, tag)]
                elif f.extra_thumbnails.has_key(tag):
                    f = f.extra_thumbnails[tag]

            if hasattr(f, 'url'):
                url = f.url
            else:
                url = unicode(f)
            return self.static_media_url(url)
        except Exception, e:
            print e
            return

    def get_cookie(self, name, default=None):
        if name == 'user_id' and self.has_arg('session_key'):
            return self.arg('session_key')
        return super(ApiHandler, self).get_cookie(name, default)

    @property
    def user(self):
        return self.current_user

    def send_error(self, status_code=403, **kwargs):
        if self.settings.get("debug", False):
            print kwargs
        if self._headers_written:
            print "Cannot send error response after headers written"
            if not self._finished:
                self.finish()
            return
        self.clear()
        self.set_status(status_code)
        if status_code < 500:
            if kwargs.has_key('exception') and not kwargs.has_key('msg'):
                kwargs['msg'] = str(kwargs['exception'])
                del kwargs['exception']

            self.write(kwargs)
        self.finish()

    def write(self, chunk):
        assert not self._finished

        if type(chunk) in (QuerySet, ):
            chunk = self.ps(chunk)

        if type(chunk) in (dict, list):
            chunk = json.dumps(chunk, cls=ApiJSONEncoder, ensure_ascii=False, indent=4)
            if self.arg('cb', False):
                chunk = '%s(%s)' % (self.arg('cb'), chunk)
            self.set_header("Content-Type", "text/javascript; charset=UTF-8")
            #chunk = web._utf8(chunk)
            chunk = web.utf8(chunk)
            self._write_buffer.append(chunk)
        else:
            super(ApiHandler, self).write(chunk)

    def ps(self, qs, convert_func=None, **kwargs):
        start = int(self.get_argument('start', 0))
        count = int(self.get_argument('count', 25))
        if (type(qs) in (list, set)):
            total_count = len(qs)
        else:
            total_count = qs.count()
            if type(qs) not in (QuerySet, ):
                qs = qs.all()

        if total_count > start:
            if start == -1:
                import math
                start = (math.ceil(float(total_count)/count) - 1) * count
            items = convert_func is None and qs[start:start+count] or [convert_func(item, **kwargs) for item in qs[start:start+count]]
        else:
            items = []
        return {'total_count': total_count, 'items': items}

    def format_params(self, params, urlencode):   
        slist = sorted(params)  
        buff = []  
        for k in slist:  
            v = quote(params[k]) if urlencode else params[k]  
            buff.append("{0}={1}".format(k, v))  

        return "&".join(buff) 
        
class ApiJSONEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return str(o)
        #	return dt2ut(o)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            try:
                return super(ApiJSONEncoder, self).default(o)
            except Exception:
                return smart_unicode(o)