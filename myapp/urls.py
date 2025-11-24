from django.urls import path
from . import views

app_name = "myapp"

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("item/<int:item_id>/", views.item_detail, name="item_detail"),
    path("add-to-cart/<int:item_id>/", views.add_to_cart, name="add_to_cart"),
    path(
        "remove-from-cart/<int:item_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),
    path("store/", views.store, name="store"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("about/", views.about, name="about"),
    path("policy/", views.policy, name="policy"),
    path("cart/", views.view_cart, name="view_cart"),
    path("contact/", views.contact, name="contact"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/", views.payment, name="payment"),
]
