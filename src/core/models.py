# -*- coding: utf-8 -*-
import datetime
import hashlib
from django.db import models
from django.utils.text import ugettext_lazy as _
from cyclone import escape
from positions import PositionField
from signals import *
from django.db.models.signals import post_save, post_delete
from django.core.exceptions import ValidationError
from filebrowser.fields import FileBrowseField, FileObject
from django.contrib.auth.models import User


class Zone(models.Model):
    FULL = 0
    NEWAREA = 1
    KEEP = 2
    STATUS = (
        (FULL, _('Full')),
        (NEWAREA, _('NewArea')),
        (KEEP, _('Keep')),
    )
    zoneid = models.PositiveIntegerField(_('Zoneid'), default=0)
    index = models.CharField(_('Index'), max_length=10)
    domain = models.CharField(_('Domain'), max_length=100, blank=True)
    maxnum = models.PositiveIntegerField(_('Maxnum'), default=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    channels = models.ManyToManyField('Channel', blank=True)
    # notices = models.ManyToManyField('Notice', blank=True)
    notices = models.ManyToManyField('Notice', through='Noticeship', blank=True)
    status = models.PositiveSmallIntegerField(
        _('Status'), choices=STATUS, default=KEEP)

    class Meta:
        verbose_name = _('Zone')
        verbose_name_plural = _('Zones')

    def __unicode__(self):
        return ':'.join([self.domain, str(self.zoneid)])

class Channel(models.Model):
    title = models.CharField(_('Title'), max_length=20, unique=True)
    slug = models.SlugField(_('Slug'))
    version = models.CharField(_('Max_version1'), max_length=64, editable=True)
    version2 = models.CharField(_('Max_version2'), max_length=64, editable=True)
    version3 = models.CharField(_('Max_version3'), max_length=64, editable=True)

    class Meta:
        verbose_name = _('Channel')
        verbose_name_plural = _('Channels')
        ordering = ('slug',)

    def __unicode__(self):
        return self.title

class Notice(models.Model):
    title = models.CharField(_('Title'), max_length=20, unique=True)
    content = models.TextField(blank=True)
    screenshot = FileBrowseField(_('Screenshot'), max_length=200, directory='img/screenshot', format='image', extensions=[".jpg"], blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    sign = models.CharField(_('Sign'), max_length=20, blank=True)

    class Meta:
        verbose_name = _('Notice')
        verbose_name_plural = _('Notices')

    def __unicode__(self):
        return self.title

    # def clean_fields(self, exclude=None):
    #     super(Notice, self).clean_fields()
    #
    #     if self.screenshot and not self.screenshot.exists():
    #         raise ValidationError({'file': [_('File Not Exists')]})
    #     else:
    #         path = self.screenshot.site.storage.path(self.screenshot)
    #         m = hashlib.md5()
    #         a_file = open(path, 'rb')
    #         m.update(a_file.read())
    #         self.sign = m.hexdigest()

class Noticeship(models.Model):
    zone = models.ForeignKey(Zone)
    notice = models.ForeignKey(Notice)
    position = PositionField(_('Position'), collection='zone')

    class Meta:
        verbose_name = 'Noticeship'
        verbose_name_plural = _('Noticeships')
        ordering = ('position', )

    def __unicode__(self):
        return self.notice.title

class Update(models.Model):
    channel = models.ForeignKey(Channel)
    cversion = models.CharField(_('Cur_version'), max_length=64, editable=True)
    tversion = models.CharField(_('Tar_version'), max_length=64, editable=True)
    url = models.URLField()
    # file = FileBrowseField(
    #     _('File'), max_length=200, directory='update', extensions=[".zip"],
    #     blank=True
    # )
    sign = models.CharField(_('Md5'), max_length=64, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Update')
        verbose_name_plural = _('Updates')

    def __unicode__(self):
        return 'version %s to %s' % (self.cversion, self.tversion)

class Upgrade(models.Model):
    channel = models.ForeignKey(Channel)
    version = models.CharField(_('Version'), max_length=64, editable=True)
    url = models.URLField()
    md5 = models.CharField(_('Md5'), max_length=64, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Upgrade')
        verbose_name_plural = _('Upgrades')

    def __unicode__(self):
        return 'version %s' % self.version

class BindToken(models.Model):
    channel = models.ForeignKey(Channel)
    thirdparty_token = models.CharField(_('Thirdparty_token'), max_length=128, editable=True)
    access_token = models.CharField(_('Access_token'), max_length=128, editable=True)
    timestamp = models.PositiveIntegerField(_('Timestamp'), default=0, blank=True)
    
    class Meta:
        verbose_name = _('BindToken')
        verbose_name_plural = _('BindTokens')
        unique_together = (('channel', 'thirdparty_token'),)

    def __unicode__(self):
        return 'token %s' % self.access_token

class Code(models.Model):
    code = models.CharField(_('Code'), max_length=64, unique=True)
    created_at = models.DateTimeField(_('Created_at'), default=datetime.datetime.now)
    ended_at = models.DateTimeField(_('Ended_at'), default=datetime.datetime.now)
    gold = models.PositiveIntegerField(_('Gold'), default=0)
    rock = models.PositiveIntegerField(_('Rock'), default=0)
    feat = models.PositiveIntegerField(_('Feat'), default=0)
    hp = models.PositiveIntegerField(_('Hp'), default=0)
    prods = models.TextField(_('Prods'), blank=True)
    nums = models.TextField(_('Nums'), blank=True)
    channels = models.ManyToManyField('Channel', blank=True)

    class Meta:
        verbose_name = _('Code')
        verbose_name_plural = _('Codes')

    def __unicode__(self):
        return self.code

class UserCode(models.Model):
    user_id = models.PositiveIntegerField(_('User id'), default=0)
    code = models.CharField(_('Code'), max_length=64)
    zone_id = models.PositiveIntegerField(_('Zone id'), default=0)
    channel = models.ForeignKey(Channel)
    timestamp = models.PositiveIntegerField(_('Timestamp'), default=0)

    class Meta:
        verbose_name = _('UserCode')
        verbose_name_plural = _('UserCodes')
        unique_together = ('user_id', 'code', 'zone_id')

    def __unicode__(self):
        return '{0}:{1}:{2}'.format(self.zone_id, self.user_id, self.code)

# class BigEvent(models.Model):
#     bid = models.CharField(_('Bid'), max_length=64)
#     name = models.CharField(_('Name'), max_length=64)
#     index = models.CharField(_('Index'), max_length=10)
#     type = models.CharField(_('Type'), max_length=12, blank=True)
#     channels = models.ManyToManyField('Channel', blank=True)
#     #zones = models.ManyToManyField('Zone', through='Zoneship', blank=True)
#     created_at = models.DateTimeField(_('Created_at'), default=datetime.datetime.now)
#     ended_at = models.DateTimeField(_('Ended_at'), default=datetime.datetime.now)
#
#     class Meta:
#         verbose_name = _('BigEvent')
#         verbose_name_plural = _('BigEvents')
#
#     def __unicode__(self):
#         return self.bid

# class Inpour(models.Model):
#     INPOUR = 1
#     TYPE = (
#         (INPOUR, _('Inpour')),
#     )
#     bigevent = models.ManyToManyField('BigEvent', blank=True, null=True)
#     rid = models.CharField(_('Rid'), max_length=10)
#     name = models.CharField(_('Name'), max_length=20)
#     gold = models.PositiveIntegerField(_('Gold'), default=0)
#     rock = models.PositiveIntegerField(_('Rock'), default=0)
#     feat = models.PositiveIntegerField(_('Feat'), default=0)
#     hp = models.PositiveIntegerField(_('Hp'), default=0)
#     prods = models.TextField(_('Prods'), blank=True)
#     nums = models.TextField(_('Nums'), blank=True)
#     total = models.PositiveIntegerField(_('Total'), default=0, blank=True)
#     type = models.PositiveIntegerField(_('Type'), choices=TYPE, default=INPOUR)
#
#     class Meta:
#         verbose_name = _('Inpour')
#         verbose_name_plural = _('Inpours')
#
#     def __unicode__(self):
#         return self.name

# class Zoneship(models.Model):
#     zone = models.ForeignKey(Zone)
#     bigevent = models.ForeignKey(BigEvent)
#     position = PositionField(_('Position'), collection='zone')
#
#     class Meta:
#         verbose_name = 'Zoneship'
#         verbose_name_plural = _('Zoneships')
#         ordering = ('position', )
#
#     def __unicode__(self):
#         return self.bigevent

class MailLog(models.Model):
    user = models.ForeignKey(User)
    zid = models.CharField(_('Zid'), max_length=10)
    mail = models.TextField(blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        verbose_name = _('MailLog')
        verbose_name_plural = _('MailLogs')

    def __unicode__(self):
        return self.user