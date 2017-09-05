# coding: utf-8

import base64
import datetime
import functools
import pickle
import time
import uuid
from cyclone import web
import D
import random
import requests
from local_settings import BASE_URL


def signed(method):
    @functools.wraps(method)
    def wraps(self, *args, **kwargs):
        sign = self.get_argument("_sign", None)
        if not sign:
            raise web.HTTPError(400, "Sign required")
        else:
            try:
                self.sign = str(sign)
                s = sign[-1] + sign[1:-1] + sign[0]
                self.token = pickle.loads(base64.urlsafe_b64decode(str(s + '=' * (-len(s) % 4))))
                self.uid = int(self.token['uid'])
            except Exception:
                raise web.HTTPError(400, "Sign invalid")
        return method(self, *args, **kwargs)

    return wraps


def token(method):
    @functools.wraps(method)
    def wraps(self, *args, **kwargs):
        access_token = self.get_argument("access_token", None)
        user_id = self.get_argument("user_id", None)
        login_url = BASE_URL + '/user/login/?access_token=%s&user_id=%s' % (access_token, user_id)
        r = requests.get(login_url)
        print r.status_code, r.text
        return method(self, *args, **kwargs)

    return wraps


class E(object):
    class UNKNOWNERROR(Exception):
        pass

    class INVALIDERROR(Exception):
        pass

    class SERVERERROR(Exception):
        pass

    class CLIENTERROR(Exception):
        pass

    class USERNOTFOUND(Exception):
        pass

    class USERABNORMAL(Exception):
        pass

    class USERBEBANKED(Exception):
        pass

    class VALUEINVALID(Exception):
        pass

    class HPNOTENOUGH(Exception):
        pass

    class GOLDNOTENOUGH(Exception):
        pass

    class ROCKNOTENOUGH(Exception):
        pass

    class FEATNOTENOUGH(Exception):
        pass

    class BOOkNOTENOUGH(Exception):
        pass

    class XPNOTENOUGH(Exception):
        pass

    class HXPNOTENOUGH(Exception):
        pass

    class PRODNOTENOUGH(Exception):
        pass

    class OPENTERMDISSATISFY(Exception):
        pass

    class MAXENTRYDISSATISFY(Exception):
        pass

    class COLDDOWNDISSATISFY(Exception):
        pass

    class SEALALREADYGOT(Exception):
        pass

    class TASKNOTFOUND(Exception):
        pass

    class TASKDISSATISFY(Exception):
        pass

    class TASKALREADYGOT(Exception):
        pass

    class WORKNOTFOUND(Exception):
        pass

    class WORKDISSATISFY(Exception):
        pass

    class WORKALREADYGOT(Exception):
        pass

    class ARENACOINNOTENOUGH(Exception):
        pass

    ERR_UNKNOWN = 0
    ERR_INVALID = 1
    ERR_SERVER = 2
    ERR_CLIENT = 3
    ERR_SYNC = 4
    ERR_USER_NOTFOUND = 101
    ERR_USER_ABNORMAL = 102
    ERR_USER_BEBANKED = 103
    ERR_NOTENOUGH_HP = 201
    ERR_NOTENOUGH_GOLD = 202
    ERR_NOTENOUGH_ROCK = 203
    ERR_NOTENOUGH_FEAT = 204
    ERR_NOTENOUGH_BOOK = 205
    ERR_NOTENOUGH_XP = 206
    ERR_NOTENOUGH_HXP = 207
    ERR_NOTENOUGH_PROD = 208
    ERR_DISSATISFY_PLAYTERM = 301
    ERR_DISSATISFY_MAXENTRY = 302
    ERR_DISSATISFY_COLDDOWN = 303
    ERR_SEAL_ALREADYGOT = 401
    ERR_TASK_NOTFOUND = 501
    ERR_TASK_ALREADYGOT = 502
    ERR_TASK_DISSATISFY = 503
    ERR_WORK_NOTFOUND = 601
    ERR_WORK_ALREADYGOT = 602
    ERR_WORK_DISSATISFY = 603
    ERR_MAIL_NOTFOUND = 701
    ERR_MAIL_ALREADYGOT = 702
    ERR_NOTENOUGH_ARENACOIN = 801
    ERR_DISSATISFY_MAXREFRESHES = 802
    ERR_DISSATISFY_MAXRESETS = 803
    ERR_DUPLICATE_BUY = 804
    _errmsg = {
        ERR_UNKNOWN: u'未知错误',
        ERR_INVALID: u'非法请求',
        ERR_SERVER: u'服务器正在维护',
        ERR_CLIENT: u'客户端发生异常',
        ERR_SYNC: u'数据同步错误',
        ERR_USER_NOTFOUND: u'账号不存在',
        ERR_USER_ABNORMAL: u'账户发生异常',
        ERR_USER_BEBANKED: u'账户已被封',
        ERR_NOTENOUGH_HP: u'体力不足',
        ERR_NOTENOUGH_GOLD: u'金币不足',
        ERR_NOTENOUGH_ROCK: u'钻石不足',
        ERR_NOTENOUGH_FEAT: u'功勋不足',
        ERR_NOTENOUGH_BOOK: u'计谋不足',
        ERR_NOTENOUGH_PROD: u'物品不足',
        ERR_NOTENOUGH_XP: u'战队等级不足',
        ERR_NOTENOUGH_HXP: u'英雄等级不足',
        ERR_DISSATISFY_PLAYTERM: u'进入条件不满足',
        ERR_DISSATISFY_MAXENTRY: u'最大进入次数已达到',
        ERR_DISSATISFY_COLDDOWN: u'进入冷却时间未达到',
        ERR_SEAL_ALREADYGOT: u'签到已领取',
        ERR_TASK_NOTFOUND: u'任务不存在',
        ERR_TASK_ALREADYGOT: u'任务奖励已领取',
        ERR_TASK_DISSATISFY: u'任务奖励领取条件不满足',
        ERR_WORK_NOTFOUND: u'每日不存在',
        ERR_WORK_ALREADYGOT: u'每日奖励已领取',
        ERR_WORK_DISSATISFY: u'每日奖励领取条件不满足',
        ERR_MAIL_NOTFOUND: u'邮件不存在',
        ERR_MAIL_ALREADYGOT: u'邮件已领取',
        ERR_NOTENOUGH_ARENACOIN: u'巅峰币不足',
        ERR_DISSATISFY_MAXREFRESHES: u'最大刷新次数已达到',
        ERR_DISSATISFY_MAXRESETS: u'最大重置次数已达到',
        ERR_DUPLICATE_BUY: u'重复购买物品',
    }

    @staticmethod
    def errmsg(code):
        try:
            return E._errmsg[code]
        except KeyError:
            return E._errmsg[0]

    @staticmethod
    def initdata4user():
        user = D.USERINIT
        user['secret'] = ''
        user['name'] = uuid.uuid4().hex[:8]
        user['nickname'] = u'刘健'
        user['timestamp'] = int(time.time())
        return user

    @staticmethod
    def cost4skill(hero, skill, pt):
        try:
            cost = D.HEROSKILL[skill][pt]
        except LookupError:
            cost = {
                "xp": 10000000,
                "gold": 10000000,
                "prods": {}
            }
        return cost

    @staticmethod
    def cost4level(hero, level):
        return {
            "feat": D.LEVELFEAT[level * 2],
            "hxp": D.LEVELFEAT[level * 2 + 1],
        }

    @staticmethod
    def cost4color(hero, color):
        try:
            cost = D.HEROCOLOR[color]
        except LookupError:
            cost = {
                "gold": 10000000
            }
        return cost

    @staticmethod
    def cost4star(hero, star):
        try:
            cost = D.HEROSTAR[hero['hid']][hero['star']]
            # cost = D.HEROSTAR[hero['star']]

        except LookupError:
            cost = {
                "gold": 10000000,
                "prods": {}
            }
        return cost

    @staticmethod
    def cost4recruit(hid):
        try:
            cost = D.HEROSTAR[hid][1]

        except LookupError:
            cost = {
                "gold": 10000000,
                "num": 999
            }
        return cost

    @staticmethod
    def equips4hero(hero):
        try:
            equips = D.HEROEQUIP[hero['hid']][hero['color']]
        except LookupError:
            equips = ('01001', '01002', '01003', '01004', '01005', '01006')
        return equips

    @staticmethod
    def cost4equipcom(prod):
        try:
            cost = D.PRODEQUIPCOM[prod]
        except LookupError:
            cost = {
                "gold": 10000000,
                "prods": {}
            }
        return cost

    @staticmethod
    def cost4sellout(prod):
        try:
            cost = D.PRODSELLOUT[prod]
        except LookupError:
            cost = {
                "gold": 1,
            }
        return cost

    @staticmethod
    def drawseal(user):
        userseals = user['seals']
        if userseals:
            sealnu, sealday = userseals
        else:
            sealnu, sealday = 0, 1
        weekday = datetime.date.today().weekday()
        if sealnu != 0 and sealday - 1 == weekday:
            raise E.SEALALREADYGOT
        seal = D.SEALS[sealnu + 1]
        awards = seal.get('awards')
        if awards:
            user['gold'] += awards.get('gold', 0)
            user['rock'] += awards.get('rock', 0)
            user['feat'] += awards.get('feat', 0)
            for prod, n in awards.get('prods', {}).items():
                if prod in user['prods']:
                    user['prods'][prod] += n
                else:
                    user['prods'][prod] = n
                if user['prods'][prod] > 999:
                    user['prods'][prod] = 999
                elif user['prods'][prod] == 0:
                    del user['prods'][prod]
                else:
                    pass
        userseals[0] += 1
        userseals[1] = weekday + 1

    @staticmethod
    def drawtask(user, tid):
        usertasks = user['tasks']
        if tid not in usertasks:
            raise E.TASKNOTFOUND
        if usertasks[tid]['_'] == 0:
            raise E.TASKDISSATISFY
        elif usertasks[tid]['_'] == 2:
            raise E.TASKALREADYGOT
        task = D.TASK[tid]
        usertask = usertasks[tid]
        awards = task.get('awards')
        if awards:
            user['gold'] += awards.get('gold', 0)
            user['rock'] += awards.get('rock', 0)
            user['feat'] += awards.get('feat', 0)
            for prod, n in awards.get('prods', {}).items():
                if prod in user['prods']:
                    user['prods'][prod] += n
                else:
                    user['prods'][prod] = n
                if user['prods'][prod] > 999:
                    user['prods'][prod] = 999
                elif user['prods'][prod] == 0:
                    del user['prods'][prod]
                else:
                    pass
        usertask['_'] = 2
        nexttids = task.get('revdep', [])
        nexttids.extend(task.get('dep', []))
        try:
            cattids = D.TASKCAT[task['cat']]
            cattid = cattids[cattids.index(tid) + 1]
            cattask = D.TASK[cattid]
            cattaskdeptid = cattask.get('dep', None)
            if not cattaskdeptid:
                nexttids.append(cattid)
            else:
                if cattaskdeptid in usertasks and usertasks[cattaskdeptid]['_'] != 2:
                    nexttids.append(cattid)
            print 'nexttids', nexttids

        except Exception:
            pass

        for t in nexttids:
            tt = D.TASK[t]
            progress = tt['progress'](user)
            if usertasks.has_key(t):
                if usertasks[t]['_'] == 2:
                    continue
            if progress >= tt['tags']['*']:
                progress = tt['tags']['*']
                usertasks[t] = {'_': 1, 'tags': {'*': (progress, progress)}}
            else:
                usertasks[t] = {'_': 0, 'tags': {'*': (tt['tags']['*'], progress)}}
        print usertasks

    @staticmethod
    def pushtasks(user):
        changed = False
        usertasks = user['tasks']
        for tid, usertask in usertasks.iteritems():
            if usertask['_'] == 0:
                task = D.TASK[tid]
                progress = task['progress'](user)
                if progress != usertask['tags']['*'][1]:
                    changed = True
                    if progress >= task['tags']['*']:
                        progress = task['tags']['*']
                        usertask['_'] = 1
                    usertask['tags']['*'][1] = progress
        return changed

    @staticmethod
    def tagworks(user, tags):
        changed = False
        userworks = user['works']
        tagkeys = set(tags.keys())
        for wid, work in D.WORKS.iteritems():
            for tag, target in work['tags'].items():
                if tag in tagkeys:
                    if wid not in userworks:
                        _tags = {_tag: (_target, 0) for _tag, _target in work['tags'].items()}
                        userworks[wid] = {'_': 0, 'tags': _tags}
                    if userworks[wid]['_'] == 0:
                        lastprogress = userworks[wid]['tags'][tag][1]
                        progress = lastprogress + tags[tag]
                        if progress > target:
                            progress = target
                        if lastprogress != progress:
                            changed = True
                        userworks[wid]['tags'][tag] = (target, progress)
        for userwork in userworks.itervalues():
            if userwork['_'] == 0:
                if all([y >= x for x, y in userwork['tags'].values()]):
                    userwork['_'] = 1
        return changed

    @staticmethod
    def drawwork(user, wid):
        userworks = user['works']

        if wid not in userworks:
            raise E.WORKNOTFOUND
        if userworks[wid]['_'] == 0:
            raise E.WORKDISSATISFY
        elif userworks[wid]['_'] == 2:
            raise E.WORKALREADYGOT
        work = D.WORKS[wid]
        userwork = userworks[wid]
        awards = work.get('awards')
        if awards:
            user['gold'] += awards.get('gold', 0)
            user['rock'] += awards.get('rock', 0)
            user['feat'] += awards.get('feat', 0)
            for prod, n in awards.get('prods', {}).items():
                if prod in user['prods']:
                    user['prods'][prod] += n
                else:
                    user['prods'][prod] = n
                if user['prods'][prod] > 999:
                    user['prods'][prod] = 999
                elif user['prods'][prod] == 0:
                    del user['prods'][prod]
                else:
                    pass
        userwork['_'] = 2
        print 'userworks', userworks

    @staticmethod
    def checkmails(user):
        changed = False
        usermails = user['mails']
        for mid in usermails:
            if usermails[mid] == -1:
                usermails[mid] = 0
                changed = True
        return changed

    _entryids = [
        '9101', '9102',  # 英雄试炼，每场景再细分三关：010101, 010102, 010103
    ]

    @staticmethod
    def entryopens(user):
        opens = []
        for eid in E._entryids:
            match = E.match4entry(eid)
            label = match.get('label')
            term = match.get('playterm')
            if term:
                if term(user, label):
                    opens.append(eid)
            else:
                opens.append(eid)
        return opens

    @staticmethod
    def match4entry(eid):
        try:
            MATCH = dict(D.MATCH, **D.TRIAL)
            match = MATCH[eid]
        except KeyError:
            match = {
                'label': eid,
                'playterm': lambda user, label: True,
                'colddown': 1,
                'maxentry': 99,
                'hp': 6,
                'gold': 1,
                'rock': 0,
                'feat': 0,
                'xp': 1,
                'hxp': 1,
                'prods': [('01001', 0.01)],
            }
        return match

    @staticmethod
    def awards4firstbatt(bid):
        try:
            return D.FIRSTBATT[bid]
        except Exception:
            return None

    @staticmethod
    def bornhero(user, hid):
        if hid not in user['heros']:
            hero = D.HERO[hid].copy()
            user['heros'][hid] = hero
        else:
            hero = user['heros'][hid]
        return hero

    @staticmethod
    def addskills(user, hero, skills):
        heroskills = hero['skills']
        costs = {'gold': 0, 'prods': {}}
        for skill, nu in enumerate(skills):
            pt = heroskills[skill]
            for i in range(1, nu + 1):
                cost = E.cost4skill(hero, skill, pt + i)
                xp = cost.get('xp', 0)
                # if user['xp'] < xp:
                if hero['xp'] < xp:
                    raise E.XPNOTENOUGH
                costs['gold'] += cost['gold']
                for k, v in cost['prods'].items():
                    costs['prods'][k] = costs['prods'].get(k, 0) + v
        if user['gold'] < costs['gold']:
            raise E.GOLDNOTENOUGH
        for k, v in costs['prods'].items():
            if k not in user['prods'] or user['prods'][k] < v:
                raise E.PRODNOTENOUGH
        user['gold'] -= costs['gold']
        for k, v in costs['prods'].items():
            user['prods'][k] -= v
        for skill, nu in enumerate(skills):
            heroskills[skill] += nu

    @staticmethod
    def setequips(user, hero, equips):
        heroequips = hero['equips']
        userprods = user['prods']
        prodids = E.equips4hero(hero)
        # print 'heroequips', heroequips
        # print 'userprods', userprods
        # print 'prodids', prodids
        # print 'hero', hero
        for equip, has in enumerate(equips):
            if has > 0 and heroequips[equip] == 0:
                prodid = prodids[equip]
                if prodid in userprods and userprods[prodid] > 0:
                    heroequips[equip] = 100000
                    userprods[prodid] -= 1
                    if userprods[prodid] == 0:
                        del userprods[prodid]
                else:
                    raise E.PRODNOTENOUGH

    @staticmethod
    def steplevel(user, hero):
        hxp = hero['xp']
        lv, lxp = divmod(hxp, 100000)
        cost = E.cost4level(hero, lv + 1)
        if user['feat'] < cost['feat']:
            raise E.FEATNOTENOUGH
        hlvmit, hero['xp'] = E.normhxp(user, hxp + cost['hxp'])
        if not hlvmit:
            user['feat'] -= cost['feat']
            # hero['xp'] = E.normxp(user, hxp + cost['hxp'])

    @staticmethod
    def stepcolor(user, hero):
        if not all(hero['equips']):
            raise E.PRODNOTENOUGH
        cost = E.cost4color(hero, hero['color'] + 1)
        gold = cost['gold']
        if user['gold'] < gold:
            raise E.GOLDNOTENOUGH
        user['gold'] -= gold
        hero['color'] += 1
        hero['equips'] = [0, 0, 0, 0, 0, 0]

    @staticmethod
    def stepstar(user, hero):
        cost = E.cost4star(hero, hero['star'] + 1)
        gold = cost['gold']
        prods = cost['prods']
        if user['gold'] < gold:
            raise E.GOLDNOTENOUGH
        for k, v in prods.items():
            if k not in user['prods'] or user['prods'][k] < v:
                raise E.PRODNOTENOUGH
        user['gold'] -= gold
        for k, v in prods.items():
            user['prods'][k] -= v
        hero['star'] += 1

    @staticmethod
    def recruit(user, hid):
        cost = E.cost4recruit(hid)
        gold = cost['gold']
        prods = cost['prods']
        if user['gold'] < gold:
            raise E.GOLDNOTENOUGH
        for k, v in prods.items():
            if k not in user['prods'] or user['prods'][k] < v:
                raise E.PRODNOTENOUGH
        user['gold'] -= gold
        for k, v in prods.items():
            user['prods'][k] -= v
        user['heros'][hid] = D.HERO[hid]

    @staticmethod
    def normxp(user, xp):
        lv, lxp = divmod(xp, 100000)
        ahp = 0
        while lxp > D.LEVELXP[(lv + 1) * 2 + 1] and lv < 100:
            lv += 1
            lxp = lxp - D.LEVELXP[lv * 2 + 1]
            ahp = D.AWARDHP[lv * 2 + 1]

        if lv == 100:
            lv = 99
            lxp = 99999
        xp = lv * 100000 + lxp
        return xp, ahp

    @staticmethod
    def normhxp(user, hxp):
        lv, lxp = divmod(hxp, 100000)
        # print 'lv, lxp uxp', lv, lxp, user['xp']
        userlv = user['xp'] / 100000
        hlvlimit = False
        while lxp >= D.LEVELHXP[(lv + 1) * 2 + 1] and lv < 100:
            lv += 1
            hlvlimit = True
            if lv > D.LEVELIMIT[userlv * 2 + 1]:
                lv = D.LEVELIMIT[userlv * 2 + 1]
                hxp = lv * 100000 + D.LEVELHXP[(lv + 1) * 2 + 1]
            elif lv == D.LEVELIMIT[userlv * 2 + 1]:
                lv = D.LEVELIMIT[userlv * 2 + 1]
                lxp = lxp - D.LEVELHXP[lv * 2 + 1]
                hxp = lv * 100000 + lxp
            else:
                lxp = lxp - D.LEVELHXP[lv * 2 + 1]
                hxp = lv * 100000 + lxp
            break
        if lv == 100:
            lv = 99
            lxp = 99999
            hxp = lv * 100000 + lxp
        # # if lv >= userlv:
        # if lv >= D.LEVELIMIT[userlv*2+1]:
        #     hlvlimit = True
        #     lv = D.LEVELIMIT[userlv*2+1]
        #     lxp = D.LEVELHXP[(lv+1)*2+1] - 1

        return hlvlimit, hxp

    @staticmethod
    def hpmax(xp):
        lv = int(xp) / 100000
        return D.LEVELHP[lv]

    hpup = 1
    hptick = 15

    @staticmethod
    def cost4lott(lotttype, times):
        try:
            cost = D.LOTT[lotttype][times]
        except LookupError:
            cost = None
        return cost

    lott_by_gold = 1
    lott_by_rock = 2
    limit_by_gold = 5
    limit_by_arena = 5
    timer_by_gold = 600  # 600
    timer_by_rock = 172800  # 172800
    timer_by_arena = 600
    default_formation = 1
    limit_by_refresh = 10
    limit_by_reset = 5
    cost_for_resetcd = 50
    limit_by_hunt = 20

    @staticmethod
    def random_prod(lott, daylotts, times):
        start = daylotts
        end = daylotts + times
        prod_list = []
        if end < 31:
            try:
                for one in xrange(start, end):
                    prods = {}
                    lottypes = D.PRODPROB[lott][str(one)]
                    lottype = random.choice(lottypes)
                    rewardtypes = D.PRODREWARD[lottype]
                    prod = random.choice(rewardtypes.keys())
                    prods[prod] = random.randint(rewardtypes[prod]['min'], rewardtypes[prod]['max'])
                    prod_list.append(prods)
            except LookupError:
                prod_list = None
        else:
            end = 30
            try:
                for one in xrange(0, times):
                    prods = {}
                    lottypes = D.PRODPROB[lott][str(end)]
                    lottype = random.choice(lottypes)
                    rewardtypes = D.PRODREWARD[lottype]
                    prod = random.choice(rewardtypes.keys())
                    prods[prod] = random.randint(rewardtypes[prod]['min'], rewardtypes[prod]['max'])
                    prod_list.append(prods)
            except LookupError:
                prod_list = None
        return prod_list

    @staticmethod
    def cost4arena(pid):
        try:
            cost = D.ARENAPROD[pid]['arena_coin']
        except LookupError:
            cost = None
        return cost

    @staticmethod
    def arenamatch(now_rank, before_rank):
        if now_rank < before_rank:
            history = D.ARENAHISTORY
            b = n = 0
            for i in xrange(0, len(history) / 3):
                if now_rank >= history[i * 3] and now_rank <= history[i * 3 + 1]:
                    n = i
                if before_rank >= history[i * 3] and before_rank <= history[i * 3 + 1]:
                    b = i
            rock = 0
            for i in xrange(n, b + 1):
                rock += history[i * 3 + 2]
            return rock
        else:
            return 0

    @staticmethod
    def cost4search(xp, times):
        lv = xp / 100000
        try:
            huntbase = [D.HUNTBASE[i * 2 + 1] for i in xrange(0, len(D.HUNTBASE) / 2) if lv == D.HUNTBASE[i * 2]]
            huntratio = [D.HUNTRATIO[i * 2 + 1] for i in xrange(0, len(D.HUNTRATIO) / 2) if lv == D.HUNTRATIO[i * 2]]
            hunttimes = [D.HUNTTIMES[i * 3 + 2] for i in xrange(0, len(D.HUNTTIMES) / 3) if
                         lv <= D.HUNTTIMES[i * 3 + 1] and lv >= D.HUNTTIMES[i * 3]]
            cost = huntbase[0] + huntratio[0] * hunttimes[0]
        except LookupError:
            cost = 10000
        return cost

    @staticmethod
    def earn4hunt(csword):
        try:
            gold, feat = [(D.HUNTEARN[i * 4 + 2], D.HUNTEARN[i * 4 + 3]) for i in xrange(0, len(D.HUNTEARN) / 4) if
                          csword <= D.HUNTEARN[i * 4 + 1] and csword >= D.HUNTEARN[i * 4]][0]
            earn = dict(gold=gold, feat=feat)
        except LookupError:
            earn = {'gold': 0, 'feat': 0}
        return earn

    true = 1
    false = 0
    idle = 0  # 闲置
    reclaim = 1  # 开荒
    assart = 2  # 挖矿
    timer_by_reclaim = 10000
    resist = 0  # 反抗
    expire = 1  # 期满
    release = 2  # 释放

    @staticmethod
    def earn4against(user, guards, heros):
        try:
            cword = 0
            for one in guards:
                hero = heros['one']
                cword += (hero['star'] * 5 + hero['color'] * 3) * user['xp'] / 100000 * 100
            gold, feat = \
                [(D.HUNTAGAINST[i * 4 + 2], D.HUNTAGAINST[i * 4 + 3]) for i in xrange(0, len(D.HUNTAGAINST) / 4) if
                 csword <= D.HUNTAGAINST[i * 4 + 1] and csword >= D.HUNTAGAINST[i * 4]][0]
            earn = dict(gold=gold, feat=feat)
        except LookupError:
            earn = {'gold': 0, 'feat': 0}
        return earn

    @staticmethod
    def cost4instant(instanttimes):
        try:
            rock = [D.HUNTINSTANTCOST[i * 2 + 1] for i in xrange(0, len(D.HUNTINSTANTCOST) / 2) if
                    instanttimes == D.HUNTINSTANTCOST[i * 2]][0]
            cost = dict(rock=rock)
        except Exception:
            cost = dict(rock=100)
        return cost

    limit_by_instant = 30  # 立即完成次数
    limit_by_gainst = 30  # 反抗次数
    limit_by_search = 30  # 搜索次数

    @staticmethod
    def earn4reclaim(user, guards, heros):
        try:
            cword = 0
            for one in guards:
                hero = heros['one']
                cword += (hero['star'] * 5 + hero['color'] * 3) * user['xp'] / 100000 * 100

            gold, feat = \
                [(D.HUNTRECLAIM[i * 4 + 2], D.HUNTRECLAIM[i * 4 + 3]) for i in xrange(0, len(D.HUNTRECLAIM) / 4) if
                 csword <= D.HUNTRECLAIM[i * 4 + 1] and csword >= D.HUNTRECLAIM[i * 4]][0]
            earn = dict(gold=gold, feat=feat)
        except Exception:
            earn = {'gold': 0, 'feat': 0}
        return earn

    @staticmethod
    def buy4hp(times):
        try:
            rock, hp = \
                [(D.HPBUY[i * 2 + 1], D.HPBUY[i * 2 + 2]) for i in xrange(0, len(D.HPBUY) / 3) if
                 times == D.HPBUY[i * 2]][
                    0]
            cost = dict(rock=rock, hp=hp)
        except Exception:
            cost = dict(rock=50, hp=120)
        return cost

    rate = 0.3

    @staticmethod
    def buy4gold(start, times):
        buy = []
        for time in xrange(start, start + times):
            rock, gold = [(D.GOLDBUY[i * 3 + 1], D.GOLDBUY[i * 3 + 2]) for i in xrange(0, len(D.GOLDBUY) / 3) if
                          time == D.GOLDBUY[i * 3]][0]
            extra = 0
            if random.random() < E.rate:
                extra = gold
            buy.append(dict(rock=rock, gold=gold, extra=extra))
        return buy

    @staticmethod
    def vip(vrock):
        vip = 0
        for i in xrange(0, len(D.VIP) / 2):
            if i < len(D.VIP) / 2 - 1:
                if vrock >= D.VIP[i * 2 + 1] and vrock < D.VIP[i * 2 + 3] and i < len(D.VIP) / 2 - 1:
                    vip = D.VIP[i * 2]
                    break
            else:
                if vrock >= D.VIP[i * 2 + 1]:
                    vip = D.VIP[i * 2]
        return vip

    @staticmethod
    def hpmaxtimes(vrock):
        vip = E.vip(vrock)
        maxtimes, = [D.HPBUYTIMES[i * 2 + 1] for i in xrange(0, len(D.HPBUYTIMES) / 2) if vip == D.HPBUYTIMES[i * 2]]
        return maxtimes

    @staticmethod
    def goldmaxtimes(vrock):
        vip = E.vip(vrock)
        maxtimes, = [D.GOLDBUYTIMES[i * 2 + 1] for i in xrange(0, len(D.GOLDBUYTIMES) / 2) if
                     vip == D.GOLDBUYTIMES[i * 2]]
        return maxtimes

    @staticmethod
    def arenamaxtimes(vrock):
        vip = E.vip(vrock)
        maxtimes, = [D.ARENARESETTIMES[i * 2 + 1] for i in xrange(0, len(D.ARENARESETTIMES) / 2) if
                     vip == D.ARENARESETTIMES[i * 2]]
        return maxtimes
