#!/bin/bash

echo "Clearing existing products..."
docker compose exec backend python manage.py shell << 'EOF'
from catalog.models import Product, Category, Brand, AttributeDefinition, Variant, VariantAttributeValue, ProductImage
ProductImage.objects.all().delete()
Variant.objects.all().delete()
VariantAttributeValue.objects.all().delete()
Product.objects.all().delete()
print("✓ Cleared all products and related data")
EOF

echo ""
echo "Seeding fresh products with images..."
docker compose exec backend python manage.py seed_products

echo ""
echo "Indexing to Elasticsearch..."
docker compose exec backend python manage.py init_search

echo ""
echo "✓ Done! Products with images are ready."
echo "Visit: http://localhost:3000/products"
