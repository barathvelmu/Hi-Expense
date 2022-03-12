import json
from django.contrib import messages
from django.http import JsonResponse
from .models import Source, UserIncome
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from userpreferences.models import UserPreference
from django.contrib.auth.decorators import login_required


def search_income(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        
        income = UserIncome.objects.filter(
                   amount__istartswith = search_str, owner = request.user) | UserIncome.objects.filter(
                   date__istartswith = search_str, owner = request.user) | UserIncome.objects.filter(
                   description__icontains = search_str, owner = request.user) | UserIncome.objects.filter(
                   source__icontains = search_str, owner = request.user) 
        
        data = income.values()
        return JsonResponse(list(data), safe = False)


@login_required(login_url = '/authentication/login')
def index(request):
    categories = Source.objects.all()
    income = UserIncome.objects.filter(owner = request.user)
    paginator = Paginator(income, 10)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    if UserPreference.objects.filter(user = request.user).exists():
        currency = UserPreference.objects.get(user = request.user).currency
    else:
        currency = 'United States Dollar'
    context = {
        'income': income,
        'page_obj': page_obj,
        'currency': currency,
    }
    return render(request, 'income/index.html', context)


@login_required(login_url = '/authentication/login')
def add_income(request):
    sources = Source.objects.all()
    context = {
        'sources': sources,
        'values': request.POST
    }
    
    if request.method == 'GET':
        return render(request, 'income/add_income.html', context)
        
    if request.method == 'POST':
        # obtain the amount
        amount = request.POST['amount']        
        
        if not amount:
            messages.error(request, 'Please enter an amount.')
            return render(request, 'income/add_income.html', context)
        
        # obtain the description
        description = request.POST['description']        
        
        if not description:
            messages.error(request, 'Please enter a description.')
            return render(request, 'income/add_income.html', context)
        
        # obtain the date
        date = request.POST['income_date']        
                
        # obtain the source
        source = request.POST['source']
        
        UserIncome.objects.create(owner = request.user, amount = amount, date = date, source = source, description = description)
        messages.success(request, 'Record has been created successfully!')
        return redirect('income')


@login_required(login_url = '/authentication/login')
def income_edit(request, id):
    income = UserIncome.objects.get(pk = id)
    sources = Source.objects.all()
    context = {
        'income': income,
        'values': income,
        'sources': sources,
    }
    if request.method == 'GET':
        return render(request, 'income/edit_income.html', context)
    if request.method == 'POST':        
        # obtain the amount
        amount = request.POST['amount']        
        
        if not amount:
            messages.error(request, 'Please enter an amount.')
            return render(request, 'income/edit_income.html', context)
        
        # obtain the description
        description = request.POST['description']        
        
        if not description:
            messages.error(request, 'Please enter a description.')
            return render(request, 'income/edit_income.html', context)
        
        # obtain the date
        date = request.POST['income_date']        
                
        # obtain the category
        source = request.POST['source']
        
        # Updating expense
        income.owner = request.user
        income.amount = amount
        income.date = date
        income.source = source
        income.description = description
        income.save()
        messages.success(request, 'Record has been updated successfully!')
        return redirect('income')
    
    
def delete_income(request, id):
    income = UserIncome.objects.get(pk = id)
    income.delete()
    messages.success(request, 'Record deleted!')
    return redirect('income')