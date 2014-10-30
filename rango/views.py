from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from bing_search import run_query


def decode_url(url):
    return url.replace('_', ' ')


def encode_url(url):
    return url.replace(' ', '_')


def get_category_list(total_view=5):
    category_list = Category.objects.order_by('-likes')[:total_view]
    for category in category_list:
        category.url = encode_url(category.name)
    return category_list


def get_page_list(total_view=5):
    page_list = Page.objects.order_by('-views')[:total_view]
    return page_list


@login_required
def index(request):
    request.session.set_test_cookie()
    context = RequestContext(request)
    category_list = get_category_list(total_view=5)
    page_list = get_page_list(total_view=4)

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    if request.session.get('visits'):
        count = str(request.session.get('visits'))
    else:
        count = str(0)

    context_dict = dict(categories=category_list, pages=page_list, visits=count)

    return render_to_response('rango/index.html', context_dict, context)


def about(request):
    context = RequestContext(request)
    categories = get_category_list(total_view=5)
    return render_to_response('rango/about.html', dict(categories=categories), context)


@login_required
def restricted(request):
    context = RequestContext(request)
    categories = get_category_list(total_view=5)
    return render_to_response('rango/restricted.html', dict(categories=categories), context)


@login_required
def category(request, category_name_url):
    context = RequestContext(request)
    category_name = decode_url(category_name_url)
    categories = get_category_list()
    context_dict = dict(category_name=category_name, categories=categories, category_name_url=category_name_url)
    try:
        category = Category.objects.get(name=category_name)
        pages = Page.objects.filter(category=category)
        context_dict.update(pages=pages, category=category)
    except Exception as e:
        return HttpResponse(e.message)

    return render_to_response('rango/category.html', context_dict, context)


@login_required
def add_category(request):
    context = RequestContext(request)
    categories = get_category_list()
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            form.errors
    else:
        form = CategoryForm()

    return render_to_response('rango/add_category.html', dict(form=form, categories=categories), context)


@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)
    category_name = decode_url(category_name_url)
    categories = get_category_list()
    if request.method == "POST":
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExist:
                return render_to_response('/rango/add_category.html', {}, context)
            page.views = 0
            page.save()
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    return render_to_response('rango/add_page.html',
                              {'category_name_url': category_name_url, 'category_name': category_name, 'form': form, 'categories': categories},
                              context)


def register(request):
    if request.session.test_cookie_worked():
        print ">>>Test cookie worked!"
        request.session.delete_test_cookie()

    context = RequestContext(request)
    categories = get_category_list()
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True
        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response('rango/register.html',
                              dict(user_form=user_form, profile_form=profile_form, registered=registered,
                              categories=categories),
                              context)


def user_login(request):
    context = RequestContext(request)
    categories = get_category_list()
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("your rango accoutn is temporarily disabled.")

        else:
            print "Invalid login details. {0}, {1}".format(username, password)
            return render_to_response('rango/login.html', dict(invalid=True), context)
    else:
        return render_to_response('rango/login.html', dict(invalid=False, categories=categories), context)


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')


def search(request):
    context = RequestContext(request)
    categories = get_category_list()
    result_list = []

    if request.method == "POST":
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)
            print result_list
    return render_to_response('rango/search.html', dict(result_list=result_list, categories=categories), context)


@login_required
def profile(request):
    context = RequestContext(request)
    categories = get_category_list()
    return render_to_response('rango/profile.html', dict(categories=categories), context)