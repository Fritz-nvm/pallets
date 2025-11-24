from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    title = models.CharField(max_length=200)
    vendor = models.CharField(max_length=100, default="Amazon")
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    current_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )

    quantity = models.PositiveIntegerField(default=1)

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="items"
    )

    description = models.TextField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - ${self.current_price}"

    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.original_price >= 0:
            discount = (
                (self.original_price - self.current_price) / self.original_price
            ) * 100
            return round(discount, 2)
        return 0

    @property
    def discount_amount(self):
        """Calculate discount amount"""
        return self.original_price - self.current_price


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="item_images/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "is_primary"]

    def __str__(self):
        return f"Image for {self.item.title}"
