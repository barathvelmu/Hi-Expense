import json
import tempfile
import datetime
import csv, xlwt
from weasyprint import HTML
from django.db.models import Sum
from django.contrib import messages
from .models import Category, Expense
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from userpreferences.models import UserPreference
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required


def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        
        expenses = Expense.objects.filter(
                   amount__istartswith = search_str, owner = request.user) | Expense.objects.filter(
                   date__istartswith = search_str, owner = request.user) | Expense.objects.filter(
                   description__icontains = search_str, owner = request.user) | Expense.objects.filter(
                   category__icontains = search_str, owner = request.user) 
        
        data = expenses.values()
        
        return JsonResponse(list(data), safe = False)


@login_required(login_url = '/authentication/login')
def index(request):
    expenses = Expense.objects.filter(owner = request.user)
    paginator = Paginator(expenses, 10)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    
    if UserPreference.objects.filter(user = request.user).exists():
        currency = UserPreference.objects.get(user = request.user).currency
    else:
        currency = 'United States Dollar'
        
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
    }
    
    return render(request, 'expenses/index.html', context)


@login_required(login_url = '/authentication/login')
def add_expense(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': request.POST
    }
    
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)
        
    if request.method == 'POST':
        # obtain the amount
        amount = request.POST['amount']        
        
        if not amount:
            messages.error(request, 'Please enter an amount.')
            return render(request, 'expenses/add_expense.html', context)
        
        # obtain the description
        description = request.POST['description']        
        
        if not description:
            messages.error(request, 'Please enter a description.')
            return render(request, 'expenses/add_expense.html', context)
        
        # obtain the date
        date = request.POST['expense_date']        
                
        # obtain the category
        category = request.POST['category']
        
        Expense.objects.create(owner = request.user, amount = amount, date = date, category = category, description = description)
        messages.success(request, 'Expense has been created successfully!')
        
        return redirect('expenses')
    
    
@login_required(login_url = '/authentication/login')
def expense_edit(request, id):
    expense = Expense.objects.get(pk = id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories,
    }
    
    if request.method == 'GET':
        return render(request, 'expenses/edit-expense.html', context)
    
    if request.method == 'POST':        
        # obtain the amount
        amount = request.POST['amount']        
        
        if not amount:
            messages.error(request, 'Please enter an amount.')
            return render(request, 'expenses/edit_expense.html', context)
        
        # obtain the description
        description = request.POST['description']        
        
        if not description:
            messages.error(request, 'Please enter a description.')
            return render(request, 'expenses/edit_expense.html', context)
        
        # # obtain the date
        date = request.POST['expense_date']        
                
        # # obtain the category
        category = request.POST['category']
        
        # Updating expense
        expense.owner = request.user
        expense.amount = amount
        expense.date = date
        expense.category = category
        expense.description = description
        expense.save()
        messages.success(request, 'Expense has been updated successfully!')
        
        return redirect('expenses')
    
    
def delete_expense(request, id):
    expense = Expense.objects.get(pk = id)
    expense.delete()
    messages.success(request, 'Expense deleted!')
    
    return redirect('expenses')

def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days = 30 * 6)
    expenses = Expense.objects.filter(owner = request.user, date__gte = six_months_ago, date__lte = todays_date)
    finalrep = {}
    
    def get_category(expense):
        return expense.category
    
    # obtaining all categories without duplicates using "set"
    category_list = list(set(map(get_category, expenses)))
    
    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category = category)
        
        # total amount of the specific category
        for item in filtered_by_category:
            amount += item.amount
            
        return amount
    
    for x in expenses:
        for y in category_list:
            finalrep[y] = get_expense_category_amount(y)
    
    return JsonResponse({'expense_category_data': finalrep}, safe = False)


def stats_view(request):
    return render(request, 'expenses/stats.html')


def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename = Expenses' + str(datetime.datetime.now()) + '.csv'
    
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])
    
    expenses = Expense.objects.filter(owner = request.user)
    
    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.category, expense.date])
        
    return response


def export_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename = Expenses' + str(datetime.datetime.now()) + '.xls'
    
    # wb is workbook. That is nothing but the excel file itself.
    wb = xlwt.Workbook(encoding='utf-8')
    # ws is worksheet.
    ws = wb.add_sheet('Expenses')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    columns= ['Amount', 'Description', 'Category', 'Date']
    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
        
    font_style = xlwt.XFStyle()
    
    # dynamic rows
    rows = Expense.objects.filter(owner = request.user).values_list('amount', 'description', 'category', 'date')
    
    for row in rows:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, str(row[col_num]), font_style)
    
    wb.save(response)
    return response
    
    
def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename = Expenses' + str(datetime.datetime.now()) + '.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    
    expenses = Expense.objects.filter(owner = request.user)
    sum = expenses.aggregate(Sum('amount'))
    
    html_string = render_to_string('expenses/pdf-output.html', {'expenses': expenses, 'total': sum['amount__sum']})
    html = HTML(string = html_string)
    result = html.write_pdf()
    
    with tempfile.NamedTemporaryFile(delete = True) as output:
        output.write(result)
        output.flush()
        
        # rb is read in binary
        output = open(output.name, 'rb')
        response.write(output.read())
        
    return response