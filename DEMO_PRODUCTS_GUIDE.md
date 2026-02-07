# Demo Products Setup Guide

## Quick Start

Add 8 demo products to test the frontend:

```bash
docker compose exec backend python manage.py seed_products
```

Or using the helper script:

```bash
bash manage.sh seed-products
```

## What Gets Created

### 8 Demo Products:

1. **Floral Midi Dress** (Women)
   - Brand: Zara
   - Price: $42.00
   - Variants: S/M/L in Blue, M in Pink
   - Stock: 10-15 units per variant

2. **Casual Denim Jacket** (Women)
   - Brand: H&M
   - Price: $59.99
   - Variants: S/M/L/XL in Blue
   - Stock: 10-25 units

3. **Wireless Headphones** (Accessories)
   - Brand: Nike
   - Price: $79.00
   - Variants: Black/White/Silver
   - Stock: 20-50 units

4. **Running Shoes Pro** (Shoes)
   - Brand: Nike
   - Price: $89.99
   - Variants: Size 8/9/10 in Black/White
   - Stock: 15-25 units

5. **Leather Backpack** (Accessories)
   - Brand: Gucci
   - Price: $199.00
   - Variants: Brown/Black
   - Stock: 8-12 units

6. **Slim Fit Shirt** (Men)
   - Brand: H&M
   - Price: $29.99
   - Variants: M/L in White/Blue
   - Stock: 15-30 units

7. **Sports Sneakers** (Shoes)
   - Brand: Adidas
   - Price: $69.99
   - Variants: Size 8/9/10 in White
   - Stock: 18-25 units

8. **Summer Hat** (Accessories)
   - Brand: Zara
   - Price: $24.99
   - Variants: Beige/Black
   - Stock: 35-40 units

### Also Creates:

- ✅ 4 Categories (Women, Men, Shoes, Accessories)
- ✅ 6 Brands (Zara, H&M, Nike, Adidas, Gucci, Prada)
- ✅ 2 Attributes (Size, Color)
- ✅ All variants with proper stock
- ✅ Proper SKUs for each variant

## After Seeding

### 1. Index Products to Elasticsearch
```bash
docker compose exec backend python manage.py init_search
```

### 2. Test Frontend

**Home Page:**
```
http://localhost:3000
```
- Should show 8 products in "Trending Now"

**Product Listing:**
```
http://localhost:3000/products
```
- Should show all 8 products

**Category Pages:**
```
http://localhost:3000/products?category=women   (2 products)
http://localhost:3000/products?category=men     (1 product)
http://localhost:3000/products?category=shoes   (2 products)
http://localhost:3000/products?category=accessories (3 products)
```

**Product Detail:**
```
http://localhost:3000/products/floral-midi-dress
http://localhost:3000/products/wireless-headphones
http://localhost:3000/products/casual-denim-jacket
```

### 3. Test Features

**Variant Selection:**
- Click size/color buttons
- Price updates if variant has different price
- Stock count updates
- Out-of-stock variants are disabled

**Add to Cart:**
- Must be logged in
- Select quantity
- Click "Add to Cart"
- Success message appears

**Filters:**
- Category filters work
- Size filters work
- Color filters work
- Price range works

**Sorting:**
- Most Popular
- Newest
- Price: Low to High
- Price: High to Low

## Command Reference

```bash
# Seed products
docker compose exec backend python manage.py seed_products

# Index to Elasticsearch
docker compose exec backend python manage.py init_search

# View products in admin
http://localhost/admin/catalog/product/

# View products in Adminer
http://localhost:8080
```

## What If You Already Have Products?

The command uses `get_or_create`, so:
- ✅ Won't duplicate products
- ✅ Safe to run multiple times
- ✅ Only creates missing items

## Cleaning Up

To remove demo products:
```bash
docker compose exec backend python manage.py shell
```

```python
from catalog.models import Product
Product.objects.all().delete()
```

## Summary

✅ 8 demo products with variants
✅ Multiple categories
✅ Multiple brands
✅ Realistic pricing ($24.99 - $199.00)
✅ Various stock levels
✅ Full variant support (size + color)

**Run the command and test all frontend pages!** 🚀
