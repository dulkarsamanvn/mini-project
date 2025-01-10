from django.http import JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from accounts.models import CustomUser
from django.contrib import messages
from .forms import ChangePasswordForm,EditProfileForm
from django.contrib.auth import update_session_auth_hash,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from . models import Address
from .forms import AddressForm
from django.urls import reverse


# Create your views here.
@login_required(login_url= 'login')
def profile_overview(request):
    user=CustomUser.objects.get(id=request.user.id)
    context={
        'user':{
            'name':user.full_name,
            'email':user.email
        }
    }
    return render(request,'profile_overview.html',context)


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, instance=user)
        password_form = ChangePasswordForm(request.POST)

        # Handle profile update
        if 'update_profile' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect('profile_management:edit_profile')
        
        # Handle password change
        if 'change_password' in request.POST:
            if password_form.is_valid():
                old_password = password_form.cleaned_data['old_password']
                new_password = password_form.cleaned_data['new_password']
                confirm_password = password_form.cleaned_data['confirm_password']

                # Ensure old password is valid
                if not user.check_password(old_password):
                    messages.error(request, "Current password is incorrect.")
                    return redirect('profile_management:edit_profile')

                # Ensure passwords match
                if new_password != confirm_password:
                    messages.error(request, "Passwords do not match.")
                    return redirect('profile_management:edit_profile')

                # Validate the new password using Django's built-in validator
                try:
                    validate_password(new_password)
                except Exception as e:
                    messages.error(request, f"Password error: {e}")
                    return redirect('profile_management:edit_profile')

                # Set and save the new password
                user.set_password(new_password)
                user.save()

                # Keep the user logged in after password change
                update_session_auth_hash(request, user)  # Prevents logging the user out

                messages.success(request, "Password changed successfully.")
                return redirect('profile_management:edit_profile')
            else:
                messages.error(request, "Invalid form submission. Please try again.")
    else:
        profile_form = EditProfileForm(instance=user)
        password_form = ChangePasswordForm()

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'email': user.email,
    }
    return render(request, 'edit_profile.html', context)


@login_required
def profile_details(request):
    user=CustomUser.objects.get(id=request.user.id)
    context={
        'user':{
            'name':user.full_name,
            'email':user.email,
            'phone':user.phone,
            'gender':user.gender,
            'alternate_number':user.alternate_number,
            'birthday':user.birthday

        }
    }
    return render(request,'profile_details.html',context)

@login_required
def address_list(request):
    # addresses=request.user.addresses.all()
    addresses = Address.objects.filter(user=request.user, is_active=True)
    return render(request,'address_list.html',{'addresses':addresses})

@login_required
def add_address(request):
    if request.method=='POST':
        form=AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user=request.user
            address.save()
            messages.success(request,"address added successfully")
            return redirect(reverse('profile_management:address_list'))
    else:
        form=AddressForm()
    return render(request,'address_form.html',{'form':form})


# @login_required
# def add_address(request):
#     if request.method == 'POST':
#         form = AddressForm(request.POST)
#         if form.is_valid():
#             address = form.save(commit=False)
#             address.user = request.user
#             address.save()
            
#             # Get the redirect URL, either from the 'next' parameter or default to address list
#             next_page = request.POST.get('next', reverse('profile_management:address_list'))

#             # Handle AJAX request for modal behavior
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({'message': 'Address added successfully.', 'redirect_url': next_page})

#             messages.success(request, "Address added successfully")
#             return redirect(next_page)
#         else:
#             if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                 return JsonResponse({'error': 'Invalid form submission', 'errors': form.errors}, status=400)

#     return render(request, 'address_form.html', {'form': form})




@login_required
def edit_address(request,pk):
    address=get_object_or_404(Address,pk=pk,user=request.user)
    if request.method=='POST':
        form=AddressForm(request.POST,instance=address)
        if form.is_valid():
            form.save()
            messages.success(request,'address updated successfully')
            return redirect(reverse('profile_management:address_list'))
    else:
        form=AddressForm(instance=address)
    return render(request,'address_form.html',{'form':form})


@login_required
def delete_address(request,pk):
    address=get_object_or_404(Address,pk=pk,user=request.user)
    # address.delete()
    address.is_active=False
    address.save()
    messages.success(request,'address deleted successfully')
    return redirect(reverse('profile_management:address_list'))


@login_required
def set_default_address(request,pk):
    address=get_object_or_404(Address,pk=pk,user=request.user)
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default=True
    address.save()
    messages.success(request,'default address updated successfully')
    return redirect(reverse('profile_management:address_list'))

from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect
from .forms import AddressForm
from django.urls import reverse


@login_required
def add_address_modal(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        
        if form.is_valid():
            print("Form is valid.")
            address = form.save(commit=False)
            address.user = request.user
            old_address=Address.objects.filter(user=request.user,is_default=True).first()
            if old_address:
                old_address.is_default=False
                old_address.save()
            address.is_default=True
            address.save()
            messages.success(request,"address added successfully")

            # For AJAX requests, return a JSON response with the redirect URL
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                print("AJAX request detected.")
                # messages.success(request,"address added")
                return JsonResponse({
                    # 'message': 'Address added successfully.',
                    'redirect_url': reverse('orders:checkout')  # Redirect to checkout after saving
                })
            else:
                return redirect('profile_management:address_list')
        else:
            # If the form is invalid, return errors to the modal
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Invalid form submission',
                    'errors': form.errors
                }, status=400)

    # If GET request or no form submission, just return an empty form
    form = AddressForm()
    return render(request, 'address_form.html', {'form': form})
