from pyexpat import model
from authentification.auth_decorators import auth_required
from .db import *
from .base_auth import generate_otp, generate_txn, get_subs_id
from django.db import models

def sent_code(request, phone, device_token):
    return post_sent_code(phone, device_token)

def check_sent_code(request, txn_id, sms_code):

    return post_check_sent_code(request, txn_id, sms_code)

@auth_required(token_only=True)
def logout(request, msisdn, auth_token):

    return post_logout(request)

# Create your models here.
class AuthenCredentianls(models.Model):
    '''Custom table for authorithation data
    '''
    #otp = generate_otp()
    
    msisdn        = models.CharField(max_length=15)
    subs_id       = models.IntegerField(blank=True, null=True)  
    otp_value     = models.IntegerField(blank=True, null=True)        
    txn_value     = models.IntegerField(default = generate_txn())       
    start_date    = models.DateTimeField(auto_now_add=True,)
    device_model  = models.CharField(max_length=200)
    device_os     = models.CharField(max_length=200)
    device_ip     = models.CharField(max_length=50)
    device_token  = models.CharField(max_length=200)
    end_date      = models.DateTimeField(blank=True, null=True)
    end_reason    = models.CharField(max_length=20, blank=True, null=True)
    
    
    def save(self, *args, **kwargs):
        otp = generate_otp(self.msisdn)
        self.otp_value = otp        
        super(AuthenCredentianls, self).save(*args, **kwargs) # Call the "real" save() method.
        
    # def save(self, *args, **kwargs):
    #     self.subs_id = get_subs_id(self.msisdn)
    #     super(AuthenCredentianls, self).save(*args, **kwargs) # Call the "real" save() method.
        
    def __str__(self):
        return self.msisdn    
class AuthHistory(models.Model):
    phone = models.CharField(max_length=15)
    otp = models.CharField(max_length=5)
    token = models.CharField(max_length=256)
    verified = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    device_model  = models.CharField(max_length=50, blank=True, null=True)
    device_os     = models.CharField(max_length=20, blank=True, null=True)
    device_ip     = models.CharField(max_length=15, blank=True, null=True)
    
    class Meta:
        ordering = ['create_date']
        
    def __str__(self):
        return self.phone