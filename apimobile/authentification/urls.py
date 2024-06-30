from django.contrib.admin.sites import all_sites
from django.urls import path
from .views import OTP, VerifyOTP, Refresh, SendCode, CheckSentCode, Logout, LogOut

urlpatterns = [
    path('send-code/', SendCode.as_view()),
    path('check-sent-code/', CheckSentCode.as_view()),
    path('logoff/', Logout.as_view()),
    path('otp', OTP.as_view()),
    path('verify', VerifyOTP.as_view()),
    path('refresh', Refresh.as_view()),
    path('logout', LogOut.as_view())
]