from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from datetime import datetime

from .models import Item, Category


def store(request):
    items = Item.objects.filter(is_active=True)

    # Get cart from session
    cart = request.session.get("cart", {})
    cart_items = []
    total = 0

    # Create a list of keys to remove (don't modify during iteration)
    keys_to_remove = []

    for item_id, item_data in cart.items():
        try:
            item = Item.objects.get(id=int(item_id))
            cart_items.append({"item": item, "quantity": item_data["quantity"]})
            total += item.current_price * item_data["quantity"]
        except Item.DoesNotExist:
            # Mark invalid items for removal
            keys_to_remove.append(item_id)

    # Remove invalid items after iteration
    if keys_to_remove:
        for key in keys_to_remove:
            if key in cart:
                del cart[key]
        request.session["cart"] = cart
        request.session.modified = True

    context = {
        "items": items,
        "cart_items": cart_items,
        "cart_total": total,
        "cart_count": len(cart_items),
    }
    return render(request, "store.html", context)


def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id, is_active=True)

    # Get related items (same category, excluding current item)
    related_items = Item.objects.filter(category=item.category, is_active=True).exclude(
        id=item.id
    )[:4]

    # Get cart info for display
    cart = request.session.get("cart", {})
    cart_count = sum(item_data["quantity"] for item_data in cart.values())

    context = {"item": item, "cart_count": cart_count, "related_items": related_items}
    return render(request, "item_detail.html", context)


def add_to_cart(request, item_id):
    if request.method == "POST":
        try:
            item = get_object_or_404(Item, id=item_id, is_active=True)

            # Initialize cart in session if not exists
            if "cart" not in request.session:
                request.session["cart"] = {}

            cart = request.session["cart"]
            item_id_str = str(item_id)

            # Add item to cart or update quantity
            if item_id_str in cart:
                cart[item_id_str]["quantity"] += 1
            else:
                cart[item_id_str] = {
                    "quantity": 1,
                    "name": item.title,
                    "price": str(item.current_price),
                }

            request.session.modified = True
            messages.success(request, f"🎉 {item.title} added to your cart!")

        except Exception as e:
            messages.error(request, f"❌ Error adding to cart: {str(e)}")

    # Redirect back to the item detail page
    return redirect("myapp:item_detail", item_id=item_id)


def remove_from_cart(request, item_id):
    if request.method == "POST":
        try:
            item = get_object_or_404(Item, id=item_id)

            cart = request.session.get("cart", {})
            item_id_str = str(item_id)

            if item_id_str in cart:
                del cart[item_id_str]
                request.session["cart"] = cart
                request.session.modified = True
                messages.success(request, f"{item.title} removed from cart")
            else:
                messages.error(request, "Item not in cart")

        except Exception as e:
            messages.error(request, f"Error removing from cart: {str(e)}")

    return redirect("myapp:view_cart")


def view_cart(request):
    cart = request.session.get("cart", {})
    cart_items = []
    total = 0

    # Create a list of keys to remove (don't modify during iteration)
    keys_to_remove = []

    for item_id, item_data in cart.items():
        try:
            item = Item.objects.get(id=int(item_id))
            item_total = item.current_price * item_data["quantity"]
            cart_items.append(
                {
                    "item": item,
                    "quantity": item_data["quantity"],
                    "total": item_total,
                }
            )
            total += item_total
        except Item.DoesNotExist:
            # Mark invalid items for removal
            keys_to_remove.append(item_id)

    # Remove invalid items after iteration
    if keys_to_remove:
        for key in keys_to_remove:
            if key in cart:
                del cart[key]
        request.session["cart"] = cart
        request.session.modified = True

    context = {"cart_items": cart_items, "cart_total": total}
    return render(request, "cart.html", context)


def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect("store")

    cart_items = []
    total = 0

    # Create a list of keys to remove (don't modify during iteration)
    keys_to_remove = []

    for item_id, item_data in cart.items():
        try:
            item = Item.objects.get(id=int(item_id))
            item_total = item.current_price * item_data["quantity"]
            cart_items.append(
                {
                    "item": item,
                    "quantity": item_data["quantity"],
                    "total": item_total,
                }
            )
            total += item_total
        except Item.DoesNotExist:
            # Mark invalid items for removal
            keys_to_remove.append(item_id)

    # Remove invalid items after iteration
    if keys_to_remove:
        for key in keys_to_remove:
            if key in cart:
                del cart[key]
        request.session["cart"] = cart
        request.session.modified = True

    if not cart_items:
        messages.warning(request, "Your cart is empty!")
        return redirect("store")

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        zip_code = request.POST.get("zip_code")

        # Store customer info in session for payment page
        request.session["customer_info"] = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
        }
        request.session.modified = True

        return redirect("myapp:payment")

    context = {"cart_items": cart_items, "cart_total": total}
    return render(request, "checkout.html", context)


def payment(request):
    cart = request.session.get("cart", {})
    customer_info = request.session.get("customer_info", {})

    if not cart:
        messages.warning(request, "Your cart is empty!")
        return redirect("myapp:store")

    if not customer_info:
        messages.warning(request, "Please complete checkout information first.")
        return redirect("myapp:checkout")

    cart_items = []
    total = 0

    # Create a list of keys to remove (don't modify during iteration)
    keys_to_remove = []

    for item_id, item_data in cart.items():
        try:
            item = Item.objects.get(id=int(item_id))
            item_total = item.current_price * item_data["quantity"]
            cart_items.append(
                {
                    "item": item,
                    "quantity": item_data["quantity"],
                    "total": item_total,
                }
            )
            total += item_total
        except Item.DoesNotExist:
            # Mark invalid items for removal
            keys_to_remove.append(item_id)

    # Remove invalid items after iteration
    if keys_to_remove:
        for key in keys_to_remove:
            if key in cart:
                del cart[key]
        request.session["cart"] = cart
        request.session.modified = True

    if not cart_items:
        messages.warning(request, "Your cart is empty!")
        return redirect("myapp:store")

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")

        # Store payment method in session for email template
        request.session["selected_payment_method"] = payment_method
        request.session.modified = True

        # Show payment not available message
        messages.info(
            request,
            f"{payment_method} payment is not available through our online system. Please check your email for instructions to complete your purchase.",
        )

        return redirect("myapp:payment")

    context = {
        "cart_items": cart_items,
        "cart_total": total,
        "customer_info": customer_info,
    }
    return render(request, "payment.html", context)


def homepage(request):
    items = Item.objects.filter(is_active=True)

    context = {"items": items}

    return render(request, "home.html", context)


def contact(request):
    return render(request, "contact.html")


def about(request):
    return render(request, "about.html")


def policy(request):
    return render(request, "policy.html")


def how_it_works(request):
    return render(request, "how-it-works.html")
