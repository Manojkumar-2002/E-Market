import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from apps.products.models import Category, Product, ProductVariant

class Command(BaseCommand):
    help = "Seeds the database with realistic Categories, Products, and Variants"

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories', 
            type=int, 
            default=5, 
            help='Number of categories to create'
        )
        parser.add_argument(
            '--products-per-cat', 
            type=int, 
            default=10, 
            help='Number of products per category'
        )

    def handle(self, *args, **options):
        fake = Faker()
        
        num_categories = options['categories']
        products_per_cat = options['products_per_cat']

        # Predefined e-commerce catalog names for realistic generation
        category_pool = ["Electronics", "Apparel", "Home & Kitchen", "Fitness", "Books", "Beauty", "Automotive"]
        sizes = ["S", "M", "L", "XL", "256GB", "512GB", "Standard"]
        colors = ["Crimson Red", "Matte Black", "Space Gray", "Navy Blue", "Alpine White", "Olive Green"]

        self.stdout.write(self.style.WARNING("Starting database seed operations..."))

        # Wrap everything in an atomic transaction so we don't end up with partial/broken data
        with transaction.atomic():
            
            # 1. Create Categories
            created_categories = []
            selected_names = random.sample(category_pool, min(num_categories, len(category_pool)))
            
            for name in selected_names:
                # get_or_create prevents duplication crashes if you run the script multiple times
                category, created = Category.objects.get_or_create(
                    name=name,
                    defaults={"is_active": True}
                )
                created_categories.append(category)
                if created:
                    self.stdout.write(f"Created Category: {name}")

            # 2. Create Products
            for category in created_categories:
                for _ in range(products_per_cat):
                    # Generate real looking product names based on category context
                    product_name = f"{fake.company()} {fake.word().capitalize()}"
                    
                    product = Product.objects.create(
                        category=category,
                        name=product_name,
                        description=fake.paragraph(nb_sentences=3),
                        is_active=True
                    )

                    # 3. Create Product Variants (Each product gets 1 to 4 distinct variants)
                    num_variants = random.randint(1, 4)
                    base_price = random.randint(15, 1200) # Base cost calculation

                    for i in range(num_variants):
                        # Generate unique SKUs using company initials + random integers
                        sku = f"{product.name[:3].upper()}-{random.randint(10000, 99999)}-{i}"
                        
                        # Slightly adjust pricing variations across size/color configurations
                        variant_price = Decimal(base_price) + Decimal(random.randint(0, 50)) + Decimal('0.99')

                        ProductVariant.objects.create(
                            product=product,
                            sku=sku,
                            price=variant_price,
                            stock_quantity=random.randint(0, 150),
                            # 👑 THE FIX: Use fake.boolean() from the Faker library instance
                            size=random.choice(sizes) if fake.boolean() else "",
                            color=random.choice(colors) if fake.boolean() else "",
                            is_active=True
                        )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded database with mock store inventory data!"))