# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
# from models import Account, User, Mail
from models import Zone, MailLog
from front.utils import E
from front import D
from front.settings import settings
from local_settings import *
import redis, time
import pickle
import json
red = redis.StrictRedis(host=DATA_HOST, port='6379', db=DATA_DBID)

@login_required
def mail(request):
    #print request.user
    if request.GET.has_key('zone'):
        zoneid = request.GET['zone']
        zones = Zone.objects.filter(zoneid=zoneid)
        if zones:
            name = request.GET['name']
            mail = {}
            mail['sender'] = u"倩儿"
            mail['to'] = name
            if request.GET.has_key('title'):
                mail['title'] = request.GET['title']
            if request.GET.has_key('content'):
                mail['content'] = request.GET['content']
            if request.GET.has_key('type'):
                mail['type'] = request.GET['type']
            #{"gold":5000, "rock":100, "feat":100, "prods":{"04001":200}}
            awards = {}
            if request.GET.has_key('gold'):
                awards['gold'] = request.GET['gold']
            if request.GET.has_key('rock'):
                awards['rock'] = request.GET['rock']
            if request.GET.has_key('feat'):
                awards['feat'] = request.GET['feat']
            if request.GET.has_key('hp'):
                awards['hp'] = request.GET['hp']
            if request.GET.has_key('versus_coin'):
                awards['versus_coin'] = request.GET['versus_coin']
            prods = {}
            if request.GET.has_key('prod1'):
                if request.GET['prod1'] in D.PRODS:
                    prods[request.GET['prod1']] = request.GET['prod1_num']
            if request.GET.has_key('prod2'):
                if request.GET['prod2'] in D.PRODS:
                    prods[request.GET['prod2']] = request.GET['prod2_num']
            if request.GET.has_key('prod3'):
                if request.GET['prod3'] in D.PRODS:
                    prods[request.GET['prod3']] = request.GET['prod3_num']
            if request.GET.has_key('prod4'):
                if request.GET['prod4'] in D.PRODS:
                    prods[request.GET['prod4']] = request.GET['prod4_num']
            if request.GET.has_key('prod5'):
                if request.GET['prod5'] in D.PRODS:
                    prods[request.GET['prod5']] = request.GET['prod5_num']
            awards['prods'] = prods
            mail['jawards'] = awards
            red.lpush('mail:%s' % zoneid, pickle.dumps(mail))
            m = MailLog()
            m.user = request.user
            m.mail = mail
            m.zid = '{0}:{1}'.format(zoneid, name)
            m.save()
            message = '{0}{1}'.format(zoneid, '区邮件发送成功')
            return HttpResponse(json.dumps(dict(error=message)), mimetype="application/json", status=200)
        else:
            return HttpResponse(json.dumps(dict(error=u"分区不存在")), mimetype="application/json", status=404)
    return render_to_response('mail.html')