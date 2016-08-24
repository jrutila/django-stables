from shop.models.product import BaseProduct, BaseProductManager
from shop.models.cart import BaseCartItem
from shop.models.customer import BaseCustomer
from django.db.models import IntegerField

class ProductManager(BaseProductManager):
  pass

class Product(BaseProduct):
  objects = ProductManager()
  product_name = 'Test'
  lookup_fields = ('product_name', )

class CartItem(BaseCartItem):
  quantity = IntegerField()

class Customer(BaseCustomer):
  pass
