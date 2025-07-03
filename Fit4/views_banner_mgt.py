from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from Fit4.forms import *
from django.contrib import messages
import traceback
from user_visit.models import *

def banner_list(request):
    try:
        banner_formset=[]
        bannerForm = BannerForm(request.POST)
        banners = Banner.objects.filter().order_by('-uploaded_at')
        for o in banners:
            banner_formset.append(BannerForm(instance=o))

        Zipformsets = zip(banners, banner_formset)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/upload_banner.html', {'form': bannerForm, 'bannerFormset':Zipformsets})

def add_banner(request):
    try:
        #banners = Banner.objects.filter().order_by('-uploaded_at')
        if request.method == 'POST':
            form = BannerForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('/en/banners/')
        else:
            form = BannerForm()
    except Exception as e:
        print(traceback.format_exc())
    return render(request, 'Fit4/upload_banner.html', {'form': form})

def update_banner(request, id):
    try:  
        banner = Banner.objects.filter(id=id).first()
        if request.method == "POST":
            formBanner = BannerForm(data=request.POST, files=request.FILES, instance=banner)
            if formBanner.is_valid():
                formBanner.save()
                # o = form.save(commit=False)
                # o = form.save()
                return redirect('/en/banners/')
        else:
            formBanner = BannerForm(instance=banner)
    except Exception as e:
        print(traceback.format_exc())
    return render(request, "Fit4/upload_banner.html", {'formBanner': formBanner, 'banners':banner})

def delete_banner(request, id):
    banner = Banner.objects.filter(id=id).first()
    try:
        banner.delete()
        messages.success(request, '<b>'+ banner.title + '</b> successfully deleted.')
        return redirect('/en/banners/')
    except Exception as e:
        print(traceback.format_exc())
    return redirect('/en/banners/')