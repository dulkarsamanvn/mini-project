from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Wallet,Transaction
from django.contrib import messages
from decimal import Decimal
# Create your views here.

@login_required
def wallet_detail(request):
    wallet,created=Wallet.objects.get_or_create(user=request.user)
    return render(request,"wallet_detail.html",{'wallet':wallet})



@login_required
def transaction_history(request):
    wallet=get_object_or_404(Wallet,user=request.user)
    transactions = wallet.transactions.all().order_by('-created_at')
    return render(request,'transaction_history.html',{'transactions':transactions})



@login_required
def add_to_wallet(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            print(f"Amount received: {amount}")

            
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0.")
                return redirect('wallet:wallet_detail')

            
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            print(f"Wallet: {wallet}, Created: {created}")
            print(f"User: {request.user}, Email: {request.user.email}")

            # Add amount to the wallet
            wallet.credit(amount, description='Amount added to wallet')
            print(f"Wallet balance after credit: {wallet.balance}")

            messages.success(request, f"₹{amount:.2f} has been added to your wallet.")
        except ValueError as ve:
            print(f"ValueError: {ve}")
            messages.error(request, "Invalid amount.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            messages.error(request, f"Error: {str(e)}")
    return redirect('wallet:wallet_detail')

