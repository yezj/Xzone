# -*- coding: utf-8 -*-

import django_rq
import datetime
from job import syncdb
def syncdb_callback_function(sender, instance, **kwargs):
    # from django.db import transaction
    #
    # if transaction.is_managed():
    #     # transaction is managed, not commited, do not sync
    #     return
    if sender._meta.db_table == "core_user":
        queue = django_rq.get_queue('high')
        queue.enqueue(syncdb, "flushdb/", {"id": instance.pk})
