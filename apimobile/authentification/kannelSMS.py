import requests

def sendSMS(msisdn, text):
    
    # host = "http://127.0.0.1:8007"
    host = "http://10.84.52.4:8007"
    resp = requests.get(host + "/cgi-bin/sendsms?username=mytcell&password=mytcell9&smsc=SMPPSim&to="+str(msisdn)+"&text="+text+"&from=MyTcell&coding=2&charset=UTF-8")
    
    if resp.status_code == 202:
        return True
    else:
        return False