from django.shortcuts import render
from django import forms
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import base64
from io import BytesIO
import datetime
from . import arima2
from django.core.mail import send_mail
from yahoo_fin import stock_info as si
import time
import smtplib
import ssl
from email.message import EmailMessage


dic={}
# Create your views here.
class Newalertform(forms.Form):
    Name=forms.CharField(label="New Stock",min_length=2)
    alert=forms.DecimalField(label="Alert price",max_digits=7,decimal_places=2)

class newdetailform(forms.Form):
    Name=forms.CharField(label="New Form",min_length=2)

class SignUp(forms.Form):
    username_user = forms.CharField(max_length=64,label="Username")
    first_name = forms.CharField(max_length=64, min_length=3)
    last_name = forms.CharField(max_length=64, min_length=1,required = False)
    password1_user = forms.CharField(widget=forms.PasswordInput,label="Password",min_length=7)
    password2_user = forms.CharField(widget=forms.PasswordInput,label="Password",min_length=7)
    email_user = forms.EmailField(label="Email")

class NewLoginForm(forms.Form):
    username_user = forms.CharField(max_length=64,label="Username")
    password_user = forms.CharField(widget=forms.PasswordInput,label="Password")  

def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("alerts:login"))
        
    if request.method=="POST" and Newalertform(request.POST).is_valid():
        print(request.POST["Name"],request.POST["alert"])
        try:
            dic[request.POST["Name"]][request.user]=request.POST["alert"]
        except:
            dic[request.POST["Name"]]={}
            dic[request.POST["Name"]][request.user]=request.POST["alert"]
        try:
            users=(Alertgroup.objects.get(user=request.user, name=request.POST["Name"]))
            users.alert=request.POST["alert"]
            users.save()
        except:
            Alertgroup.objects.create(user=request.user,name=request.POST["Name"], alert=request.POST["alert"])
    return render(request,"alerts/index.html",{
        "form": Newalertform()
    })


def get_historical_stock_data(symbol, start_date, end_date):
    ticker = yf.Ticker(symbol)
    print(ticker.info['longName'])
    data = ticker.history(start=start_date, end=end_date)
    return data

def plot_graph(x,y,check):
    plt.clf()
    if check==1:
        plt.title(f"Original data for {x[0].date()} to {datetime.date.today()-datetime.timedelta(days=1)} ")
    if check==0:
        plt.title(f"Predicted Data for {datetime.date.today()} to {datetime.date.today()+datetime.timedelta(days=10)}")
    plt.plot(x,y)
    plt.ylabel("Stock price")
    plt.xlabel("Dates")
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')
    return graphic

def checkdata(request):
    message=None
    if(request.method=="POST"):
        symbol=request.POST["Name"]
        try:
            # Replace with the desired symbol
            ticker = yf.Ticker(symbol)
            
            current_date = datetime.date.today()
            prior_date = current_date - datetime.timedelta(days=500)
            start_date= prior_date.strftime("%Y-%m-%d")
            end_date = current_date - datetime.timedelta(days=1)
            print(end_date)
            end_date=end_date.strftime("%Y-%m-%d")
            
            historical_data = get_historical_stock_data(symbol, start_date, end_date)
            historical_data.reset_index(inplace=True)
            x=historical_data["Date"]
            y=historical_data["Close"]
            print(x,y)
            print(symbol)
            x1=arima2.main(y)
            y1=[]
            for i in range(15):
                y1.append(current_date + datetime.timedelta(days=i))
            
            return render(request, "alerts/checkdata.html", {
                "name": ticker.info['longName'],
                "current":si.get_live_price(symbol),
                "form": newdetailform(),
                "graph1": plot_graph(x,y,1),
                "graph2": plot_graph(y1,x1,0)
            })
        except:
            message="Enter the correct symbol"

    return render(request,"alerts/checkdata.html",{
        "form":newdetailform(),
        "message":message
    })
    
def Logout(request):
    logout(request)
    return HttpResponseRedirect(reverse("alerts:login"))

def Login(request):
    message=None
    if request.method=='POST':
        user=authenticate(username=request.POST["username_user"],password=request.POST["password_user"])
        if user:
            login(request,user)
            return HttpResponseRedirect(reverse("alerts:index"))
        else:
            message='Error Occured please retry'
    return render(request,"alerts/login.html",{
        "message": message,
        "form": NewLoginForm()
    })

def signup(request):
    if request.user.is_authenticated:
        logout(request)
    message=None
    form= SignUp()
    if request.method=="POST":
        try:
            User=get_user_model()
            User.objects.get(username=request.POST["username_user"].lower())
            message= "Username Already exits"
            form=SignUp(request.POST)
        except:
            if SignUp(request.POST,request.FILES).is_valid():
                if request.POST["password1_user"]==request.POST["password2_user"]:
                    User=get_user_model()
                    user=User.objects.create_user(request.POST["username_user"].lower(),request.POST["email_user"],request.POST["password1_user"])
                    user.save()
                    user.first_name=request.POST["first_name"]
                    if request.POST["last_name"]:
                        user.last_name=request.POST["last_name"]
                    user.save()
                    username=request.POST["username_user"].lower()
                    password=request.POST["password1_user"]
                    user=authenticate(username=username,password=password)
                    if user:
                        login(request,user)
                        return HttpResponseRedirect(reverse("alerts:index"))
                    else:
                        message= "Unknown error occured, Please retry. "
                else:
                    message= "Passwords don't match. "
                    form=SignUp(request.POST)
            else:
                message= "Invalid details. "
                form=SignUp(request.POST)
    return render(request,"alerts/signup.html",{
        "form": form,
        "message": message
    })

def callfunc():
    for i in dic:
        symbol=i
        curprice=si.get_live_price(symbol)
        maxim=max(arima2.getdata(symbol))
        for j in dic[i]:
            print(float(dic[i][j]))
            if curprice>=float(dic[i][j]):
                sendmail(j.email,f"The current stock price of {i} is {curprice} and the maximum predicted price in next 15 days is {maxim}")
            elif maxim>=float(dic[i][j]):
                sendmail(j.email,f"The maximum predicted price of {i} for the next 15 days is {maxim}")
            
def sendmail(mail,message):
    email_sender = 'shrishsakthi@gmail.com'
    email_password = 'annpsbafiaxnmxjw'
    email_receiver = mail

    # Set the subject and body of the email
    subject = 'Alert in Stock prediction '
    body = message

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
    
def corun():
    print("1")
    putdata()
    while (True):
        callfunc()
        time.sleep(28800)

def putdata():
    groups=Alertgroup.objects.all()
    for group in groups:
        try:
            dic[group.name][group.user]=group.alert
        except:
            dic[group.name]={}
            dic[group.name][group.user]=group.alert

def alertmail(request):
    putdata()
    callfunc()
    return HttpResponseRedirect(reverse("alerts:index"))