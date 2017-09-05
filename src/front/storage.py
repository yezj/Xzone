# coding: utf-8

import collections
import functools

import cyclone.redis
from cyclone import web, escape
from twisted.enterprise import adbapi
from twisted.internet import defer, reactor
from twisted.python import log
from apscheduler.schedulers.twisted import TwistedScheduler
import psycopg2
import datetime
import D
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

IntegrityError = psycopg2.IntegrityError


def databaseSafe(method):
    """This decorator function makes all database calls safe from connection
     errors. It returns an HTTP 503 when either redis or sql are temporarily
     disconnected.

     @databaseSafe
     def get(self):
        now = yield self.sql.runQuery("select now()")
        print now
    """
    @defer.inlineCallbacks
    @functools.wraps(method)
    def run(self, *args, **kwargs):
        try:
            r = yield defer.maybeDeferred(method, self, *args, **kwargs)
        except cyclone.redis.ConnectionError, e:
            m = "redis.Error: %s" % e
            log.msg(m)
            raise cyclone.web.HTTPError(503, m)  # Service Unavailable
        except (psycopg2.InterfaceError, psycopg2.OperationalError), e:
            m = "sql.Error: %s" % e
            log.msg(m)
            raise cyclone.web.HTTPError(503, m)  # Service Unavailable
        else:
            defer.returnValue(r)

    return run


class DatabaseMixin(object):
    sql = None
    redis = None
    pubsub = None
    sched = None
    channels = collections.defaultdict(lambda: [])

    @classmethod
    def setup(cls, conf):
        if "sql" in conf:
            DatabaseMixin.sql = \
            adbapi.ConnectionPool("psycopg2",
                                  host=conf["sql"]['host'],
                                  database=conf["sql"]['database'],
                                  user=conf["sql"]['username'],
                                  password=conf["sql"]['password'],
                                  cp_min=1,
                                  cp_max=10,
                                  cp_reconnect=True,
                                  cp_noisy=conf["debug"])

        if "redis" in conf:
            DatabaseMixin.redis = \
            cyclone.redis.lazyConnectionPool(
                          host=conf["redis"]['host'],
                          dbid=conf["redis"]['dbid'],
                          poolsize=10,
                          reconnect=True)

            if conf["redis"].get("pubsub", False):
                pubsub = cyclone.redis.SubscriberFactory()
                pubsub.maxDelay = 20
                pubsub.continueTrying = True
                pubsub.protocol = PubSubProtocol
                reactor.connectTCP(conf["redis"]['host'], 6379, pubsub)

        DatabaseMixin.sched = TwistedScheduler()
        DatabaseMixin.build()
        DatabaseMixin.sched.start()


    @classmethod
    def build(cls):
        sched = cls.sched



    def subscribe(self, channel):
        if not DatabaseMixin.pubsub:
            raise cyclone.web.HTTPError(503, "Pubsub not available")
        if channel not in DatabaseMixin.channels:
            log.msg("Subscribing entire server to %s" % channel)
            if "*" in channel:
                DatabaseMixin.pubsub.psubscribe(channel)
            else:
                DatabaseMixin.pubsub.subscribe(channel)
        DatabaseMixin.channels[channel].append(self)
        log.msg("Client %s subscribed to %s" %
                (hasattr(self, 'request') and self.request.remote_ip or '*', channel))

    def unsubscribe(self, channel):
        peers = DatabaseMixin.channels.get(channel, [])
        if peers:
            try:
                peers.pop(peers.index(self))
                log.msg("Client %s unsubscribed from %s" %
                        (hasattr(self, 'request') and self.request.remote_ip or '*', channel))
            except Exception:
                return
        if not len(peers) and DatabaseMixin.pubsub:
            log.msg("Unsubscribing entire server from %s" % channel)
            if "*" in channel:
                DatabaseMixin.pubsub.punsubscribe(channel)
            else:
                DatabaseMixin.pubsub.unsubscribe(channel)
            try:
                del DatabaseMixin.channels[channel]
            except Exception:
                pass

    def unsubscribe_all(self):
        # Unsubscribe peer from all channels
        for channel, peers in DatabaseMixin.channels.items():
            try:
                peers.pop(peers.index(self))
                log.msg("Client %s unsubscribed from %s" %
                        (hasattr(self, 'request') and self.request.remote_ip or '*', channel))
            except Exception:
                continue
            # Unsubscribe from channel if no peers are listening
            if not len(peers) and DatabaseMixin.pubsub:
                log.msg("Unsubscribing entire server from %s" % channel)
                if "*" in channel:
                    DatabaseMixin.pubsub.punsubscribe(channel)
                else:
                    DatabaseMixin.pubsub.unsubscribe(channel)
                try:
                    del DatabaseMixin.channels[channel]
                except Exception:
                    pass

    def broadcast(self, pattern, channel, message):
        peers = DatabaseMixin.channels.get(pattern or channel)
        if not peers:
            return
        # Broadcast the message to all peers in channel
        for peer in peers:
            peer.pubsubReceived(pattern or channel, message)


class PubSubProtocol(cyclone.redis.SubscriberProtocol, DatabaseMixin):
    def messageReceived(self, pattern, channel, message):
        # When new messages are published to Redis channels or patterns,
        # they are broadcasted to all HTTP clients subscribed to those
        # channels.
        DatabaseMixin.broadcast(self, pattern, channel, message)

    def connectionMade(self):
        DatabaseMixin.pubsub = self
        # If we lost connection with Redis during operation, we
        # re-subscribe to all channels once the connection is re-established.
        for channel in DatabaseMixin.channels:
            if "*" in channel:
                self.psubscribe(channel)
            else:
                self.subscribe(channel)

    def connectionLost(self, why):
        DatabaseMixin.pubsub = None
