
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import pre_save
from django.utils.text import slugify
from decimal import Decimal
from transliterate import translit



class SubCategory(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(blank=True)
	
	
	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('subcategory_view', kwargs={'subcategory_slug': self.slug})	

def pre_save_subcategory_slug(sender, instance, *args, **kwargs):
	if not instance.slug:
		slug = slugify(translit(str(instance.name), reversed=True))
		instance.slug = slug

pre_save.connect(pre_save_subcategory_slug, sender=SubCategory)


class Category(models.Model):
	
	name = models.CharField(max_length=100)
	slug = models.SlugField(blank=True)
	subcategory = models.ManyToManyField('SubCategory')

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('category_view', kwargs={'category_slug': self.slug})

def pre_save_category_slug(sender, instance, *args, **kwargs):
	if not instance.slug:
		slug = slugify(translit(str(instance.name), reversed=True))
		instance.slug = slug

pre_save.connect(pre_save_category_slug, sender=Category)





class Brand(models.Model):

	name = models.CharField(max_length=100)

	def __str__(self):
		return self.name
		

def image_folder(instance, filename):
	filename = instance.slug + '.' + filename.split('.')[1]
	return "{0}/{1}".format(instance.slug, filename)


class ProductManager(models.Manager):

	def all(self, *args, **kwargs):
		return super(ProductManager, self).get_queryset().filter(available=True)


class Product_images(models.Model):

	image_folder = models.ImageField(upload_to="image_folder")

class Description_info(models.Model):

	description_type = models.CharField(max_length=200)
	description_info = models.TextField()
	product_description = models.ForeignKey('ProductDescription', on_delete=models.CASCADE)
	
class ProductDescription(models.Model):

	description_title = models.CharField(max_length=200)
	product = models.ForeignKey('Product', on_delete=models.CASCADE)

class Product(models.Model):

	category = models.ForeignKey('Category', on_delete=models.CASCADE)
	subcategory = models.ForeignKey('SubCategory', on_delete=models.CASCADE)
	brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
	title = models.CharField(max_length=200)
	slug = models.SlugField() 
	video = models.URLField()
	description = models.TextField()
	price = models.DecimalField(max_digits=9, decimal_places=2)
	image = models.ImageField(upload_to="image_folder")
	other_image = models.ManyToManyField(Product_images, blank=True)
	available = models.BooleanField(default=True)
	objects = ProductManager()

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		return reverse('product_view', kwargs={'product_slug': self.slug})

class Hit(models.Model):

	product_list = models.ForeignKey('Product', on_delete=models.CASCADE)

class Recomendations(models.Model):

	product_list = models.ForeignKey('Product', on_delete=models.CASCADE)

class CartItem(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	qty = models.PositiveIntegerField(default=1)
	item_total = models.DecimalField(max_digits=9, decimal_places=2,default=0.00)

	def __str__(self):
		return "Cart item for product {0}".format(self.product.title)


class Cart(models.Model):

	items = models.ManyToManyField(CartItem, blank=True)
	cart_total = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)

	def __str__(self):
		return str(self.id)

	def add_to_cart(self, product_slug):
		cart = self
		product = Product.objects.get(slug=product_slug)
		new_item, _ = CartItem.objects.get_or_create(product=product, item_total=product.price)
		if new_item not in cart.items.all():
			cart.items.add(new_item)
			cart.save()

	def remove_form_cart(self, product_slug):
		cart = self
		product = Product.objects.get(slug=product_slug)
		for cart_item in cart.items.all():
			if cart_item.product == product:
				cart.items.remove(cart_item)
				cart.save()

	def change_qty(self, qty, item_id):
		cart = self
		cart_item = CartItem.objects.get(id=int(item_id))
		cart_item.qty = int(qty)
		cart_item.item_total = int(qty) * Decimal(cart_item.product.price)
		cart_item.save()
		new_cart_total = 0.00
		for item in cart.items.all():
			new_cart_total += float(item.item_total)
		cart.cart_total = new_cart_total
		cart.save()


ORDER_STATUS_CHOICES = (
	('Прийняте в обробку', 'Прийняте в обробку'),
	('Виконується','Виконується'),
	('Оплачено', 'Оплачено')
)

class Order(models.Model):

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
	items = models.ManyToManyField(Cart)
	total = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
	first_name = models.CharField(max_length=200)
	last_name = models.CharField(max_length=200)
	phone = models.CharField(max_length=20)
	address = models.CharField(max_length=255)
	buying_type = models.CharField(max_length=40, choices=(('Самовивіз', 'Самовивіз'), ('Доставка', 'Доставка')))
	date = models.DateTimeField(auto_now_add=True)
	comments = models.TextField() 
	status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES)

	def __str__(self):
		return 'Замовлення №{0}'.format(str(self.id))