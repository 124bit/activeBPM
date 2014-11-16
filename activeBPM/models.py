from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
import ntpath
import os
from django.conf import settings

#TODO Add a long descriptions, account existence test (all other things is available through BPMS admin)
class BPMSUser(models.Model):
    login = models.CharField(max_length=50,  verbose_name=_("BPMS user login"), unique=True)
    password = models.CharField(max_length=50,  verbose_name=_("BPMS user password"))
    phone = models.CharField(max_length=50,  verbose_name=_("BPMS user phone"), blank=True, null=True)
    web_user = models.OneToOneField(User, blank=True, null=True, on_delete=models.SET_NULL,
                                    verbose_name=_("Web user of BPMS account"))

    def __str__(self):
        return self.login

    class Meta:
        verbose_name = _('BPMS User')
        verbose_name_plural = _('BPMS Users')
        ordering = ['login']


class TaskFile(models.Model):
    file = models.FileField(upload_to='comments_files/%f%d%m%y/')
    key = models.CharField(max_length=200)
    purpose = models.CharField(max_length=200)


from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

@receiver(pre_delete, sender=TaskFile)
def mymodel_delete(sender, instance, **kwargs):
    file_folder = os.path.join(settings.MEDIA_ROOT, ntpath.split(instance.file.name)[0])
    instance.file.delete(False)
    os.rmdir(file_folder)