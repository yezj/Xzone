# -*- coding: utf-8 -*-

import random
import time
import zlib
import uuid
import json
import datetime
import pickle
import base64
import requests
import urllib
import urlparse
import hashlib  
from xml.dom.minidom import parse, parseString
from urllib import unquote
from twisted.internet import defer
from cyclone import escape, web, httpclient, httputil
from twisted.python import log
from front import storage
from front import utils
from front.utils import E
from front.wiapi import *
from front import D
from front.handlers.base import ApiHandler, ApiJSONEncoder

@handler
class XmNotifyHandler(ApiHandler):

    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('pay notify', '/xmpay/notify/', [
        Param('appId', True, str, '2882303761517239138', '2882303761517239138', 'appId'), 
        Param('cpOrderId', True, str, '9786bffc-996d-4553-aa33-f7e92c0b29d5', '9786bffc-996d-4553-aa33-f7e92c0b29d5', 'cpOrderId'), 
        Param('orderId', True, str, '21140990160359583390', '21140990160359583390', 'orderId'), 
        Param('orderStatus', True, str, 'TRADE_SUCCESS', 'TRADE_SUCCESS', 'orderStatus'), 
        Param('payFee', True, int, 1, 1, 'payFee'),   
        Param('payTime', True, str, '2014-09-05', '2014-09-05', 'payTime'),  
        Param('productCode', False, str, '0', '0', 'productCode'), 
        Param('productCount', False, int, 1, 1, 'productCount'), 
        Param('productName', False, str, '0', '0', 'productName'), 
        Param('signature', True, str, '121aaac22a222bbaaa2222aaaa', '121aaac22a222bbaaa2222aaaa', 'signature'),   
        ], filters=[ps_filter], description="pay notify")
    def get(self):
        try:
            cpOrderId = self.get_argument("cpOrderId")
            orderStatus = self.get_argument("orderStatus")
            payFee = self.get_argument("payFee")
            payTime = self.get_argument("payTime")
            signature = self.get_argument("signature")  
            cpUserInfo = self.get_argument("cpUserInfo")             
        except Exception:
            raise web.HTTPError(400, "Argument error")
        params = self.request.arguments.copy()
        params.pop('signature')
        for x, y in params.items():
            params[x] = y[0]
        params = yield self.format_params(params, False)
        m = hashlib.md5()   
        m.update(params) 
        _sign = m.hexdigest()  
        if signature != _sign:
            url = "%s/xmpay/notify/" % cpUserInfo
            params = dict(cpOrderId=cpOrderId, orderStatus=orderStatus, payFee=payFee, payTime=payTime)
            yield httpclient.fetch(httputil.url_concat(url, params))

            ret = dict(error_code=200)
        else:
            ret = dict(error_code=1525, errMsg=E.errmsg(E.ERR_SIGN))
        reb = zlib.compress(escape.json_encode(ret))
        self.write(ret)

@handler
class CmNotifyHandler(ApiHandler):

    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('pay notify', '/cmpay/notify/', [  
        ], filters=[ps_filter], description="pay notify")
    def post(self):
        dom = parseString(self.request.body)  
        root = dom.firstChild 
        childs = root.childNodes
        for child in childs: 
            if child.nodeType == child.TEXT_NODE:
                pass
            else:
                if child.nodeName == 'contentId':
                    contentId = child.childNodes[0].data
                elif child.nodeName == 'consumeCode':
                    consumeCode = child.childNodes[0].data
                elif child.nodeName == 'cpid':
                    cpid = child.childNodes[0].data
                elif child.nodeName == 'hRet':
                    hRet = child.childNodes[0].data                   
                elif child.nodeName == 'cpparam':
                    print child.childNodes[0].data.encode("utf-8")
                    orderId, zoneid = child.childNodes[0].data.split('%2C')
                else:pass
        res = yield self.sql.runQuery("SELECT domain FROM core_zone WHERE zoneid=%s", (zoneid, ))
        if res:
            domain, = res[0] 
        url = "%s/cmpay/notify/" % domain
        params = dict(orderId=orderId, contentId=contentId, consumeCode=consumeCode, cpid=cpid, hRet=hRet)
        yield httpclient.fetch(httputil.url_concat(url, params))
        self.write('''<?xml version="1.0" encoding="UTF-8"?> <request><hRet>0</hRet><message>Successful</message> </request>''')


@handler
class DbNotifyHandler(ApiHandler):
    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('Dangbei pay notify', '/dangbei/notify/', [
        Param('datastr', True, str, example='', description='datastr'),
        Param('sign', True, str, example='', description='sign')],
        description="Dangbei payment notify")
    def post(self):
        try:
            signature = self.get_argument("sign")
            datastr = json.loads(unquote(self.get_argument("datastr")))
            extra1 = datastr["extra"].split("&")[1]
        except Exception:
            raise web.HTTPError(400, "Argument error")

        url = "%s/dangbei/notify/" % extra1
        params = dict(datastr=self.get_argument('datastr'), sign=signature)
        respose = yield httpclient.fetch(httputil.url_concat(url, params))
        if respose.code != 200:
            raise web.HTTPError(reponse.code)
        self.write("success")


@handler
class LgNotifyHandler(ApiHandler):

    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('pay notify', '/lgpay/notify/', [
        Param('serial_no', True, str, '2882303761517239138', '2882303761517239138', 'serial_no'), 
        Param('transaction_id', True, str, '9786bffc-996d-4553-aa33-f7e92c0b29d5', '9786bffc-996d-4553-aa33-f7e92c0b29d5', 'transaction_id'), 
        Param('result_code', True, int, 120, 120, 'result_code'), 
        Param('fee', True, int, 1, 1, 'fee'),   
        ], filters=[ps_filter], description="pay notify")
    def get(self):
        try:
            serial_no = self.get_argument("serial_no")
            transaction_id = self.get_argument("transaction_id")
            result_code = self.get_argument("result_code")
            fee = self.get_argument("fee")           
        except Exception:
            raise web.HTTPError(400, "Argument error")
        res = yield self.sql.runQuery("SELECT domain FROM core_zone WHERE zoneid=%s", (serial_no[10:], ))
        if res:
            domain, = res[0] 
        if int(result_code) == 120:
            url = "%s/lgpay/notify/" % domain
            params = dict(serial_no=serial_no, transaction_id=transaction_id, fee=fee)
            yield httpclient.fetch(httputil.url_concat(url, params))
            ret = dict(serial_no=serial_no)
            reb = zlib.compress(escape.json_encode(ret))
            self.write(ret)    

@handler
class LetvNotifyHandler(ApiHandler):

    @storage.databaseSafe
    @defer.inlineCallbacks
    @api('pay notify', '/letvpay/notify/', [
        Param('appKey', True, str, '2882303761517239138', '2882303761517239138', 'appKey'), 
        Param('params', True, str, '9786bffc-996d-4553-aa33-f7e92c0b29d5', '9786bffc-996d-4553-aa33-f7e92c0b29d5', 'params'), 
        Param('pxNumber', True, str, '21140990160359583390', '21140990160359583390', 'pxNumber'), 
        Param('price', True, int, 1, 1, 'price'), 
        Param('userName', True, str, 1, 1, 'userName'),   
        Param('currencyCode', True, str, '0', '0', 'currencyCode'), 
        Param('products', True, str, '0', '0', 'products'), 
        Param('sign', True, str, '121aaac22a222bbaaa2222aaaa', '121aaac22a222bbaaa2222aaaa', 'sign'),   
        ], filters=[ps_filter], description="pay notify")
    def get(self):
        try:
            appKey = self.get_argument("appKey")
            params = self.get_argument("params")
            pxNumber = self.get_argument("pxNumber")
            price = self.get_argument("price")
            userName = self.get_argument("userName")
            currencyCode = self.get_argument("currencyCode")
            products = self.get_argument("products")
            sign = self.get_argument("sign")               
        except Exception:
            raise web.HTTPError(400, "Argument error")

        app_order_id, url, externalProductId = params.split(',')
        url = "%s/letvpay/notify/" % url
        params = dict(appKey=appKey, params=params, pxNumber=pxNumber, price=price, userName=userName, currencyCode=currencyCode,\
         products=products, sign=sign)
        yield httpclient.fetch(httputil.url_concat(url, params))
        self.write("SUCCESS")

