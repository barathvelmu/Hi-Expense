import json
import threading
from django.views import View
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.contrib import messages, auth
from validate_email import validate_email 
from django.contrib.auth.models import User
from .utils import account_activation_token
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


# Multithreading to send emails faster over the network
class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)
    
    def run(self):
        self.email.send(fail_silently=False)


class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        
        if not validate_email(email):
            return JsonResponse({'email_error':'Email is invalid.'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error':'Email is in use. Please use another one.'}, status=409)
        
        return JsonResponse({'email_valid': True})
    
    
class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        
        if not str(username).isalnum():
            return JsonResponse({'username_error':'Username should only contain alphanumeric characters.'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error':'Username is already in use, please try another choice.'}, status=409)
        
        return JsonResponse({'username_valid': True})
    
    
class RegistrationView(View):
    def get(self, request):
        return render(request, 'authentication/register.html')
    
    def post(self, request):
        # get user data
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        
        context = {
            'fieldValues': request.POST
        }
        
        if not User.objects.filter(username = username).exists():
            if not User.objects.filter(email = email).exists():
                
                if len(password) < 6:
                    messages.error(request, "Password is too short. Please try again.")
                    return render(request, 'authentication/register.html', context)
                
                user = User.objects.create_user(username = username, email = email)
                user.set_password(password)
                user.is_active = False
                user.save()
                   
                # Getting uidb64            
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk)) 
                
                # Constructing domain
                domain = get_current_site(request).domain
                
                # Relative url to verification                              
                link = reverse('activate', kwargs={'uidb64': uidb64, 'token': account_activation_token.make_token(user)}) 
                activate_url = 'http://' + domain + link   
                
                # Constructing email
                email_subject = 'Activate Your Account'                          
                email_body = 'Hi, ' + user.username + '! Please use this link to verify your account:\n' + activate_url
                email = EmailMessage(
                    email_subject,
                    email_body,
                    'noreply@hiexpense.com',
                    [email],
                )
                EmailThread(email).start() # multithreading
                
                messages.success(request, "Your account has been created! Please check your email!")
                return render(request, 'authentication/register.html')
        
        return render(request, 'authentication/register.html')
    
    
class VerificationView(View):
    def get(self, request, uidb64, token):
        try:
            # get id and user
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk = id)
            
            # if user is already activated
            if not account_activation_token.check_token(user, token):
                messages.error(request, 'User already activated!')
                return redirect('login')
            
            # failproof redirect to login
            if user.is_active:
                return redirect('login')
            
            # if user is not active, then (verification link)
            user.is_active = True
            user.save()
            
            messages.success(request, 'Account has been activated successfully!')
            return redirect('login')  
        
        except Exception as ex:
            pass
        
        return redirect('login')   
    
class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')   
    
    def post(self, request):
        # obtain username and password
        username = request.POST['username'] 
        password = request.POST['password'] 
        
        if username and password:
            # returns user
            user = auth.authenticate(username = username, password = password)
            
            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request, 'Welcome, ' + user.username + '! You are now logged in')
                    return redirect('expenses')
            
                messages.error(request, 'Account is not active, please check your email.')
                return render(request, 'authentication/login.html')   
            
            messages.error(request, 'Invalid credentials, please try again.')
            return render(request, 'authentication/login.html')   
        
        messages.error(request, 'Please fill in the username and password.')
        return render(request, 'authentication/login.html')   
    
class LogoutView(View):
    def post(self, request):
        auth.logout(request) # logging the user out
        messages.success(request, 'You have successfully logged out!')
        return redirect('login')
    
class RequestPasswordResetEmail(View):
    def get(self, request):
        return render(request, 'authentication/reset-password.html')
    
    def post(self, request):
        email = request.POST['email']
        
        context = {
            'values': request.POST,
        }
        
        if not validate_email(email):
            messages.error(request, 'Please enter a valid email')
            return render(request, 'authentication/reset-password.html', context)
        
        # Getting user         
        current_site = get_current_site(request) # returns queryset
        user = User.objects.filter(email=email)
        
        if user.exists():
            email_contents = {
                'user': user[0], # [] to select the user as we got a queryset (see above)
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token': PasswordResetTokenGenerator().make_token(user[0]),
            }
            
            # Relative url to verification                              
            link = reverse('reset-user-password', kwargs={'uidb64': email_contents['uid'], 'token': email_contents['token']}) 
            reset_url = 'http://' + current_site.domain + link   
            
            # Constructing email
            email_subject = 'Password Reset Details!'                          
            email_body = 'Hi, there! Please use this link to reset your password:\n' + reset_url
            email = EmailMessage(
                email_subject,
                email_body,
                'noreply@hiexpense.com',
                [email],
            )
            EmailThread(email).start() # multithreading
            messages.success(request, 'We have sent you an email to reset your password!')
        else:
            messages.error(request, 'This email address does not exist. Please try another email.')
        
            
        return render(request, 'authentication/reset-password.html')
    
class CompletePasswordReset(View):
    def get(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token,
        }
        
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk = user_id)            
            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.info(request, 'Password link is invalid. Please request a new link.')  
                return render(request, 'authentication/reset-password.html')
        except Exception as identifier:
            pass
        return render(request, 'authentication/set-new-password.html', context)
    
    def post(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token,
        }
        
        # obtain both password entries
        password = request.POST['password']
        password2 = request.POST['password2']
                
        if len(password) < 6:
            messages.error(request, 'Password is too short. Please use more than 6 characters.')
            return render(request, 'authentication/set-new-password.html', context)
        
        if password != password2:
            messages.error(request, 'Password mismatch. Please try again.')
            return render(request, 'authentication/set-new-password.html', context)  
        
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk = user_id)
            
            user.set_password(password)
            user.save()
            messages.success(request, 'Password was set successfully!')        
            return redirect('login')
        except Exception as identifier:
            messages.info(request, 'Something went wrong. Please try again!') 
            return render(request, 'authentication/set-new-password.html', context)   
        
