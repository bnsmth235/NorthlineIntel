from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..models import Vendor, Subcontractor

@login_required(login_url='projectmanagement:login')
def all_vendors(request):
    vendors = Vendor.objects.order_by("name")
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        cname = request.POST.get('cname')
        cphone = request.POST.get('cphone')
        cemail = request.POST.get('cemail')
        w9 = request.POST.get('w9')
        csi = request.POST.get('csi')
        category = request.POST.get('category')

        context = {
            'vendors': vendors,
            'name': name,
            'address': address,
            'cname': cname,
            'cphone': cphone,
            'cemail': cemail,
            'w9': w9,
            'csi': csi,
            'category': category
        }

        #if not w9:
         #   context.update({'error_message': "Please enter the vendor W9."})
          #  return render(request, 'data/all_vendors.html', context)
        if not csi or not category:
            context.update({'error_message': "Please enter the CSI Division and Category"})
            return render(request, 'data/all_vendors.html', context)

        if not name:
            context.update({'error_message': "Please enter the vendor name. (Less than 50 characters)"})
            return render(request, 'data/all_vendors.html', context)

        if not address and not cname and not cphone and not cemail:
            context.update({'error_message': "Please enter at least one form of contact"})
            return render(request, 'data/all_vendors.html', context)

        vendor = Vendor()
        vendor.name = name
        vendor.address = address
        vendor.cname = cname
        vendor.cphone = cphone
        vendor.cemail = cemail
        vendor.w9 = w9
        vendor.csi = csi
        vendor.category =category
        vendor.save()

        return redirect(reverse('projectmanagement:all_vendors'))

    return render(request, 'data/all_vendors.html', {'vendors': vendors})



@login_required(login_url='projectmanagement:login')
def all_subs(request):
    subs = Subcontractor.objects.order_by("name")
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        w9 = request.POST.get('w9')
        csi = request.POST.get('csi')
        category = request.POST.get('category')

        context = {
            'subs': subs,
            'name': name,
            'address': address,
            'phone': phone,
            'email': email,
            'w9': w9,
            'csi': csi,
            'category': category
        }
        if not name:
            context.update({'error_message': "Please enter the subcontractor name. (Less than 50 characters)"})
            return render(request, 'data/all_subs.html', context)

        if not address and not phone and not email:
            context.update({'error_message': "Please enter at least one form of contact"})
            return render(request, 'data/all_subs.html', context)

        sub = Subcontractor()
        sub.name = name
        sub.address = address
        sub.phone = phone
        sub.email = email
        sub.w9 = w9
        sub.csi = csi
        sub.category = category
        sub.save()

        return redirect(reverse('projectmanagement:all_subs'))

    return render(request, 'data/all_subs.html', {'subs': subs})



@login_required(login_url='projectmanagement:login')
def input_data(request):
    return render(request, 'data/input_data.html')


@login_required(login_url='projectmanagement:login')
def edit_sub(request, sub_id):
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        w9 = request.POST.get('w9')
        csi = request.POST.get('csi')
        category = request.POST.get('category')

        context = {
            'sub': sub,
            'name': name,
            'address': address,
            'phone': phone,
            'email': email,
            'w9': w9,
            'csi': csi,
            'category': category,
        }

        if not name:
            context.update({'error_message': "Please enter the subcontractor name. (Less than 50 characters)"})
            return render(request, 'data/edit_sub.html', context)

        if not address and not phone and not email:
            context.update({'error_message': "Please enter at least one form of contact"})
            return render(request, 'data/edit_sub.html', context)

        if not csi:
            context.update({'error_message': "Select a CSI division"})
            return render(request, 'data/edit_sub.html', context)

        if not category:
            context.update({'error_message': "Select a category"})
            return render(request, 'data/edit_sub.html', context)

        sub.name = name
        sub.address = address
        sub.phone = phone
        sub.email = email
        sub.w9 = w9
        sub.csi = csi
        sub.category = category

        sub.save()

        return redirect('projectmanagement:all_subs')

    return render(request, 'data/edit_sub.html', {'sub': sub})

@login_required(login_url='projectmanagement:login')
def delete_sub(request, sub_id):
    if request.method == 'POST':
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            sub = get_object_or_404(Subcontractor, pk=sub_id)
            sub.delete()
            print("Subcontractor deleted")
        else:
            print("Username incorrect")

    return redirect('projectmanagement:all_subs')


@login_required(login_url='projectmanagement:login')
def edit_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        cname = request.POST.get('cname')
        cphone = request.POST.get('cphone')
        cemail = request.POST.get('cemail')
        if not name:
            return render(request, 'data/edit_vendor.html', {'error_message': "Please enter the vendor name. (Less than 50 characters)", 'vendor': vendor})

        if not address and not cphone and not cemail:
            return render(request, 'data/edit_vendor.html', {'error_message': "Please enter at least one form of contact", 'vendor': vendor})

        vendor.name = name
        vendor.addresss = address
        vendor.cname = cname
        vendor.cphone = cphone
        vendor.cemail = cemail

        vendor.save()

        return redirect('projectmanagement:all_vendors')

    return render(request, 'data/edit_vendor.html', {'vendor': vendor})


@login_required(login_url='projectmanagement:login')
def delete_vendor(request, vendor_id):
    if request.method == 'POST':
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            vendor = get_object_or_404(Vendor, pk=vendor_id)
            vendor.delete()
            print("Vendor deleted")
        else:
            print("Username incorrect")

    return redirect('projectmanagement:all_vendors')
