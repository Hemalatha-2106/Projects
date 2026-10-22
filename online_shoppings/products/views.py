from decimal import Decimal
from .models import OrderItem

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Product,
    CustomerProfile,
    Order,
    OrderItem,
    ProductReview,
    SavedAddress,
)

def signup(request):
    error = ''

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not all([name, email, phone, username, password]):
            error = 'Please fill all fields.'
        elif User.objects.filter(username=username).exists():
            error = 'Username already exists. Choose another username.'
        elif User.objects.filter(email__iexact=email).exists():
            error = 'Email already registered. Please use another email.'
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=name,
                email=email
            )

            CustomerProfile.objects.create(
                user=user,
                phone=phone
            )

            login(request, user)
            return redirect('product_list')

    return render(request, 'products/signup.html', {'error': error})


def user_login(request):
    error = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('product_list')

        error = 'Invalid username or password.'

    return render(request, 'products/login.html', {'error': error})


def user_logout(request):
    logout(request)
    return redirect('user_login')


def product_list(request):
    products = Product.objects.all()

    category = request.GET.get('category')
    search = request.GET.get('search')
    sort = request.GET.get('sort')

    if category:
        products = products.filter(category=category)

    if search:
        products = products.filter(name__icontains=search)

    if sort == 'low':
        products = products.order_by('price')
    elif sort == 'high':
        products = products.order_by('-price')

    for product in products:
        product.discount_price = (
            product.price
            * (Decimal('100') - Decimal(str(product.discount)))
            / Decimal('100')
        ).quantize(Decimal('0.01'))

    return render(request, 'products/product_list.html', {
        'products': products
    })


def add_to_cart(request, id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product = get_object_or_404(Product, id=id)

        product_id = str(id)
        current_quantity = int(cart.get(product_id, 0))

        if current_quantity < product.stock:
            cart[product_id] = current_quantity + 1
        else:
            messages.warning(
                request,
                'Maximum available stock reached.'
            )

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('product_list')


def view_cart(request):
    cart = request.session.get('cart', {})
    products = []
    total = Decimal('0.00')

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id))
            quantity = int(quantity)

            if quantity <= 0:
                continue

            price = (
                product.price
                * (Decimal('100') - Decimal(str(product.discount)))
                / Decimal('100')
            ).quantize(Decimal('0.01'))

            subtotal = (price * quantity).quantize(Decimal('0.01'))

            products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
                'discounted_price': price
            })

            total += subtotal

        except (Product.DoesNotExist, ValueError, TypeError):
            continue

    return render(request, 'products/cart.html', {
        'products': products,
        'total': total.quantize(Decimal('0.01'))
    })


def remove_from_cart(request, id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart.pop(str(id), None)

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('view_cart')


def update_cart(request, id, action):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id = str(id)
        product = Product.objects.filter(id=id).first()

        if product and product_id in cart:
            quantity = int(cart[product_id])

            if action == 'increase':
                if quantity < product.stock:
                    cart[product_id] = quantity + 1
                else:
                    messages.warning(
                        request,
                        'Maximum available stock reached.'
                    )

            elif action == 'decrease':
                quantity -= 1

                if quantity <= 0:
                    cart.pop(product_id, None)
                else:
                    cart[product_id] = quantity

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('view_cart')


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = product.reviews.select_related('user').order_by('-created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to submit a review.')
            return redirect('user_login')

        try:
            rating = int(request.POST.get('rating', ''))
        except (TypeError, ValueError):
            rating = 0

        comment = request.POST.get('comment', '').strip()

        if rating < 1 or rating > 5:
            messages.error(
                request,
                'Please select a rating from 1 to 5.'
            )
        else:
            ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': rating,
                    'comment': comment
                }
            )

            messages.success(request, 'Your review has been saved!')
            return redirect('product_detail', id=product.id)

    average_rating = None

    if reviews.exists():
        average_rating = reviews.aggregate(
            average=Avg('rating')
        )['average']

    # IMPORTANT: Render the product details page here.
    # Checkout variables do not belong in this function.
    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating
    })
@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    products = []
    total = Decimal('0.00')

    # Calculate discounted subtotal
    for product_id, quantity in cart.items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (ValueError, TypeError):
            continue

        if quantity <= 0:
            continue

        product = Product.objects.filter(id=product_id).first()

        if product:
            price = (
                product.price
                * (
                    Decimal('100')
                    - Decimal(str(product.discount))
                )
                / Decimal('100')
            ).quantize(Decimal('0.01'))

            subtotal = (price * quantity).quantize(
                Decimal('0.01')
            )

            products.append({
                'product': product,
                'quantity': quantity,
                'discounted_price': price,
                'subtotal': subtotal,
            })

            total += subtotal

    total = total.quantize(Decimal('0.01'))

    if not products:
        messages.error(request, 'Your cart is empty.')
        return redirect('view_cart')

    # Delivery charge
    if total >= Decimal('500.00'):
        delivery_charge = Decimal('0.00')
    else:
        delivery_charge = Decimal('40.00')

    final_total = (
        total + delivery_charge
    ).quantize(Decimal('0.01'))

    # Saved addresses
    saved_addresses = SavedAddress.objects.filter(
        user=request.user
    ).order_by('id')

    customer_profile = CustomerProfile.objects.filter(
        user=request.user
    ).first()

    if request.method == 'POST':
        full_name = request.POST.get(
            'full_name', ''
        ).strip()
        phone = request.POST.get(
            'phone', ''
        ).strip()
        address = request.POST.get(
            'address', ''
        ).strip()
        city = request.POST.get(
            'city', ''
        ).strip()
        pincode = request.POST.get(
            'pincode', ''
        ).strip()

        if not all([
            full_name, phone, address, city, pincode
        ]):
            messages.error(
                request,
                'Please fill all address fields.'
            )

        else:
            try:
                with transaction.atomic():
                    locked_products = {}

                    # Verify stock
                    for item in products:
                        product_id = item['product'].id

                        product = Product.objects.select_for_update().get(
                            id=product_id
                        )

                        if product.stock < item['quantity']:
                            raise ValueError(
                                f'Not enough stock for {product.name}. '
                                f'Available stock: {product.stock}'
                            )

                        locked_products[product_id] = product

                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        full_name=full_name,
                        phone=phone,
                        address=address,
                        city=city,
                        pincode=pincode,
                        total_amount=final_total,
                        payment_method='Cash on Delivery',
                        status='Order Placed',
                    )

                    # Save order items and reduce stock
                    for item in products:
                        product = locked_products[
                            item['product'].id
                        ]

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=item['quantity'],
                            price=item['discounted_price'],
                        )

                        product.stock -= item['quantity']
                        product.save(
                            update_fields=['stock']
                        )

            except (
                ValueError,
                Product.DoesNotExist
            ) as error:
                messages.error(request, str(error))
                return redirect('checkout')

            # Clear cart after successful order
            request.session['cart'] = {}
            request.session.modified = True

            messages.success(
                request,
                f'Order placed successfully! '
                f'Order Number: #{order.id}'
            )

            return redirect('my_orders')

    return render(
        request,
        'products/checkout.html',
        {
            'products': products,
            'total': total,
            'delivery_charge': delivery_charge,
            'final_total': final_total,
            'profile': customer_profile,
            'saved_name': request.user.first_name,
            'saved_phone': (
                customer_profile.phone
                if customer_profile else ''
            ),
            'saved_addresses': saved_addresses,
            
        }
    )

@login_required
def profile(request):
    customer_profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}
    )

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not all([name, email, phone]):
            messages.error(
                request,
                'Please fill all required fields.'
            )

        elif User.objects.filter(email__iexact=email).exclude(
            id=request.user.id
        ).exists():
            messages.error(request, 'This email is already in use.')

        else:
            request.user.first_name = name
            request.user.email = email
            request.user.save()

            customer_profile.phone = phone
            customer_profile.save()

            messages.success(
                request,
                'Profile updated successfully!'
            )
            return redirect('profile')

    return render(request, 'products/profile.html', {
        'profile': customer_profile
    })


@login_required
def manage_address(request):
    customer_profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={'phone': ''}
    )

    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        pincode = request.POST.get('pincode', '').strip()

        if not all([address, city, pincode]):
            messages.error(
                request,
                'Please fill all address fields.'
            )
        else:
            customer_profile.address = address
            customer_profile.city = city
            customer_profile.pincode = pincode
            customer_profile.save()

            messages.success(
                request,
                'Address saved successfully!'
            )
            return redirect('manage_address')

    return render(request, 'products/address.html', {
        'profile': customer_profile
    })

@login_required
def saved_addresses(request):
    addresses = SavedAddress.objects.filter(
        user=request.user
    ).order_by('id')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        label = request.POST.get('label', 'Home').strip() or 'Home'

        if not all([full_name, phone, address, city, pincode]):
            messages.error(request, 'Please fill all address fields.')
        else:
            SavedAddress.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city,
                pincode=pincode,
                label=label,
            )
            messages.success(request, 'Address saved successfully!')
            return redirect('saved_addresses')

    return render(request, 'products/saved_addresses.html', {
        'addresses': addresses,
    })
@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items__product'
    ).order_by('-order_date')

    return render(
        request,
        'products/my_orders.html',
        {'orders': orders}
    )


@login_required
def cancel_order(request, order_id):
    if request.method != 'POST':
        return redirect('my_orders')

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(
            id=order_id,
            user=request.user
        ).first()

        if order is None:
            messages.error(request, 'Order not found.')
            return redirect('my_orders')

        if order.status != 'Order Placed':
            messages.error(
                request,
                'This order cannot be cancelled.'
            )
            return redirect('my_orders')

        items = list(order.items.all())

        if not items:
            messages.error(
                request,
                'Order items are missing. Please contact support.'
            )
            return redirect('my_orders')

        for item in items:
            product = Product.objects.select_for_update().get(
                id=item.product_id
            )

            product.stock += item.quantity
            product.save(update_fields=['stock'])

        order.status = 'Cancelled'
        order.save(update_fields=['status'])

    messages.success(
        request,
        f'Order #{order.id} cancelled successfully!'
    )

    return redirect('my_orders') 

 
