from django.core.management.base import BaseCommand
from catalog.models import Category, Brand, Product, ProductImage, Variant, VariantAttributeValue, AttributeDefinition, Review
from users.models import User
from django.utils.text import slugify
from decimal import Decimal

class Command(BaseCommand):
    help = 'Seed database with demo products'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')

        demo_users = self.create_demo_users()
        categories = self.create_categories()
        brands = self.create_brands()
        attributes = self.create_attributes(categories)
        products = self.create_products(categories, brands, attributes)
        self.create_reviews(products, demo_users)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(products)} demo products with reviews!'))

    def create_categories(self):
        categories_data = [
            {'name': 'Women', 'description': 'Women\'s fashion and clothing'},
            {'name': 'Men', 'description': 'Men\'s fashion and clothing'},
            {'name': 'Shoes', 'description': 'Footwear for all occasions'},
            {'name': 'Accessories', 'description': 'Fashion accessories and more'},
        ]

        categories = {}
        for data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=slugify(data['name']),
                defaults={
                    'name': data['name'],
                    'description': data['description']
                }
            )
            categories[data['name']] = cat
            if created:
                self.stdout.write(f'Created category: {data["name"]}')

        return categories

    def create_demo_users(self):
        users_data = [
            {'email': 'john.doe@example.com', 'username': 'johndoe', 'first_name': 'John', 'last_name': 'Doe'},
            {'email': 'jane.smith@example.com', 'username': 'janesmith', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'email': 'mike.wilson@example.com', 'username': 'mikewilson', 'first_name': 'Mike', 'last_name': 'Wilson'},
            {'email': 'sarah.johnson@example.com', 'username': 'sarahjohnson', 'first_name': 'Sarah', 'last_name': 'Johnson'},
        ]

        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
                self.stdout.write(f'Created demo user: {data["email"]}')
            users.append(user)

        return users

    def create_brands(self):
        brands_data = ['Zara', 'H&M', 'Nike', 'Adidas', 'Gucci', 'Prada']
        brands = {}
        
        for name in brands_data:
            brand, created = Brand.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name}
            )
            brands[name] = brand
            if created:
                self.stdout.write(f'Created brand: {name}')

        return brands

    def create_attributes(self, categories):
        attributes = {}
        
        for cat_name, category in categories.items():
            size_attr, created = AttributeDefinition.objects.get_or_create(
                category=category,
                slug='size',
                defaults={
                    'name': 'Size',
                    'attribute_type': 'select',
                    'is_variant_attribute': True
                }
            )
            if created:
                self.stdout.write(f'Created attribute: Size for {cat_name}')
            
            color_attr, created = AttributeDefinition.objects.get_or_create(
                category=category,
                slug='color',
                defaults={
                    'name': 'Color',
                    'attribute_type': 'select',
                    'is_variant_attribute': True
                }
            )
            if created:
                self.stdout.write(f'Created attribute: Color for {cat_name}')
            
            if cat_name not in attributes:
                attributes[cat_name] = {}
            attributes[cat_name]['size'] = size_attr
            attributes[cat_name]['color'] = color_attr

        return attributes

    def create_products(self, categories, brands, attributes):
        products_data = [
            {
                'name': 'Floral Midi Dress',
                'category': 'Women',
                'brand': 'Zara',
                'base_price': '42.00',
                'description': 'Beautiful floral midi dress perfect for summer occasions. Made with breathable fabric and elegant design.',
                'has_variants': True,
                'variants': [
                    {'size': 'S', 'color': 'Blue', 'price': '42.00', 'stock': 10},
                    {'size': 'M', 'color': 'Blue', 'price': '42.00', 'stock': 15},
                    {'size': 'L', 'color': 'Blue', 'price': '42.00', 'stock': 8},
                    {'size': 'M', 'color': 'Pink', 'price': '44.00', 'stock': 12},
                ]
            },
            {
                'name': 'Casual Denim Jacket',
                'category': 'Women',
                'brand': 'H&M',
                'base_price': '59.99',
                'description': 'Classic denim jacket with a modern fit. Perfect for layering in any season.',
                'has_variants': True,
                'variants': [
                    {'size': 'S', 'color': 'Blue', 'price': '59.99', 'stock': 20},
                    {'size': 'M', 'color': 'Blue', 'price': '59.99', 'stock': 25},
                    {'size': 'L', 'color': 'Blue', 'price': '59.99', 'stock': 15},
                    {'size': 'XL', 'color': 'Blue', 'price': '59.99', 'stock': 10},
                ]
            },
            {
                'name': 'Wireless Headphones',
                'category': 'Accessories',
                'brand': 'Nike',
                'base_price': '79.00',
                'description': 'Premium wireless headphones with noise cancellation and 30-hour battery life.',
                'has_variants': True,
                'variants': [
                    {'color': 'Black', 'price': '79.00', 'stock': 50},
                    {'color': 'White', 'price': '79.00', 'stock': 30},
                    {'color': 'Silver', 'price': '84.00', 'stock': 20},
                ]
            },
            {
                'name': 'Running Shoes Pro',
                'category': 'Shoes',
                'brand': 'Nike',
                'base_price': '89.99',
                'description': 'Professional running shoes with advanced cushioning and breathable mesh.',
                'has_variants': True,
                'variants': [
                    {'size': '8', 'color': 'Black', 'price': '89.99', 'stock': 15},
                    {'size': '9', 'color': 'Black', 'price': '89.99', 'stock': 20},
                    {'size': '10', 'color': 'Black', 'price': '89.99', 'stock': 18},
                    {'size': '9', 'color': 'White', 'price': '89.99', 'stock': 25},
                ]
            },
            {
                'name': 'Leather Backpack',
                'category': 'Accessories',
                'brand': 'Gucci',
                'base_price': '199.00',
                'description': 'Premium leather backpack with multiple compartments. Perfect for daily use.',
                'has_variants': True,
                'variants': [
                    {'color': 'Brown', 'price': '199.00', 'stock': 8},
                    {'color': 'Black', 'price': '199.00', 'stock': 12},
                ]
            },
            {
                'name': 'Slim Fit Shirt',
                'category': 'Men',
                'brand': 'H&M',
                'base_price': '29.99',
                'description': 'Modern slim fit shirt perfect for office or casual wear. Easy care fabric.',
                'has_variants': True,
                'variants': [
                    {'size': 'M', 'color': 'White', 'price': '29.99', 'stock': 30},
                    {'size': 'L', 'color': 'White', 'price': '29.99', 'stock': 25},
                    {'size': 'M', 'color': 'Blue', 'price': '29.99', 'stock': 20},
                    {'size': 'L', 'color': 'Blue', 'price': '29.99', 'stock': 15},
                ]
            },
            {
                'name': 'Sports Sneakers',
                'category': 'Shoes',
                'brand': 'Adidas',
                'base_price': '69.99',
                'description': 'Comfortable sports sneakers for everyday activities. Lightweight and durable.',
                'has_variants': True,
                'variants': [
                    {'size': '8', 'color': 'White', 'price': '69.99', 'stock': 20},
                    {'size': '9', 'color': 'White', 'price': '69.99', 'stock': 25},
                    {'size': '10', 'color': 'White', 'price': '69.99', 'stock': 18},
                ]
            },
            {
                'name': 'Summer Hat',
                'category': 'Accessories',
                'brand': 'Zara',
                'base_price': '24.99',
                'description': 'Stylish summer hat with wide brim. UV protection and breathable material.',
                'has_variants': True,
                'variants': [
                    {'color': 'Beige', 'price': '24.99', 'stock': 40},
                    {'color': 'Black', 'price': '24.99', 'stock': 35},
                ]
            },
        ]

        products = []
        for data in products_data:
            product, created = Product.objects.get_or_create(
                slug=slugify(data['name']),
                defaults={
                    'name': data['name'],
                    'category': categories[data['category']],
                    'brand': brands[data['brand']],
                    'base_price': Decimal(data['base_price']),
                    'description': data['description'],
                    'has_variants': data['has_variants'],
                }
            )

            if created:
                self.stdout.write(f'Created product: {data["name"]}')

                # Add placeholder images (3 images per product)
                for i in range(3):
                    ProductImage.objects.create(
                        product=product,
                        image=f'products/placeholder_{i+1}.jpg',
                        alt_text=f'{product.name} - Image {i+1}',
                        display_order=i
                    )

                if data['has_variants'] and 'variants' in data:
                    category_name = data['category']
                    
                    for var_data in data['variants']:
                        sku_parts = [product.slug[:10]]
                        if 'size' in var_data:
                            sku_parts.append(var_data['size'])
                        if 'color' in var_data:
                            sku_parts.append(var_data['color'][:3].upper())
                        
                        sku = '-'.join(sku_parts)
                        
                        variant = Variant.objects.create(
                            product=product,
                            sku=sku,
                            price=Decimal(var_data['price']),
                            stock_quantity=var_data['stock']
                        )

                        if 'size' in var_data and category_name in attributes:
                            VariantAttributeValue.objects.create(
                                variant=variant,
                                attribute=attributes[category_name]['size'],
                                value=var_data['size']
                            )

                        if 'color' in var_data and category_name in attributes:
                            VariantAttributeValue.objects.create(
                                variant=variant,
                                attribute=attributes[category_name]['color'],
                                value=var_data['color']
                            )

            products.append(product)

        return products

    def create_reviews(self, products, users):
        reviews_data = [
            {
                'rating': 5,
                'title': 'Absolutely love it!',
                'comment': 'This product exceeded my expectations. The quality is amazing and it fits perfectly. Highly recommend!'
            },
            {
                'rating': 4,
                'title': 'Great quality',
                'comment': 'Very happy with this purchase. Good quality and fast delivery. Would buy again.'
            },
            {
                'rating': 5,
                'title': 'Perfect!',
                'comment': 'Exactly what I was looking for. The material is great and the price is reasonable.'
            },
            {
                'rating': 3,
                'title': 'Good but could be better',
                'comment': 'It\'s okay. The quality is decent but I expected a bit more for the price.'
            },
            {
                'rating': 4,
                'title': 'Satisfied',
                'comment': 'Nice product overall. Delivery was quick and packaging was good.'
            },
            {
                'rating': 5,
                'title': 'Excellent purchase',
                'comment': 'Best purchase I\'ve made this year! Quality is top-notch and looks even better in person.'
            },
        ]

        review_count = 0
        for product in products[:4]:
            num_reviews = min(len(users), 3)
            for i in range(num_reviews):
                review_data = reviews_data[review_count % len(reviews_data)]
                review, created = Review.objects.get_or_create(
                    product=product,
                    user=users[i],
                    defaults={
                        'rating': review_data['rating'],
                        'title': review_data['title'],
                        'comment': review_data['comment'],
                        'is_verified_purchase': True,
                        'is_approved': True,
                    }
                )
                if created:
                    review_count += 1

        self.stdout.write(f'Created {review_count} reviews')
