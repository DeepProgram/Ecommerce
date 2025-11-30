
# E-commerce Backend – Search, Product, Media & Infrastructure To-Do

This document summarizes **all decisions finalized so far**, with sections for:

- Alembic migrations  
- Cloudinary for media storage  
- Product image rules + processing  
- Product video upload support  

---

## 1. Core Tech Stack

- [x] **Backend Framework**: FastAPI  
- [x] **Database**: PostgreSQL (source of truth)  
- [x] **Search Engine**: Elasticsearch  
- [x] **ORM**: SQLAlchemy  
- [x] **Schemas**: Pydantic  
- [x] **Image Processing**: Pillow  
- [x] **Video Handling**: Basic validation + Cloudinary transform  
- [x] **Media Storage**: Cloudinary (Images + Videos)  
- [x] **Migrations**: Alembic  
- [x] **Containerization**: Docker / docker-compose  

---

## 2. Database Modeling Decisions

### 2.1 Product & Variants

- [x] **Product** is the main entity with title, brand, category, description.
- [x] **ProductVariant** holds size/color + stock.
- [ ] Add advanced variant fields (later):
  - `barcode`
  - `weight`
  - `dimensions`
  - `is_active`

**Final Variant Fields (current):**

- `id`  
- `product_id` (FK → Product)  
- `size`  
- `color`  
- `sku`  
- `price`  
- `stock`  

---

### 2.2 Product Images (Product-level Only)

- [x] Variants **do NOT** have their own images.  
- [x] All images are attached directly to the **Product**.  

**`ProductImage` model:**

- `id`  
- `product_id` (FK → Product)  
- `url` (Cloudinary URL)  
- `alt_text`  
- `order` (for display sorting)  
- `is_main` (boolean – main image for product)  

- [ ] Enforce rule: **at most one `is_main` image per product** at DB or app level.

---

### 2.3 Product Videos (Product-level Only)

- [x] Videos are also product-level (no variant-specific videos).  
- [x] Each product can have 0..N videos; usually 0–1 main showcase video.

**`ProductVideo` model:**

- `id`  
- `product_id` (FK → Product)  
- `url` (Cloudinary video URL)  
- `thumbnail_url` (Cloudinary-generated)  
- `duration` (seconds, optional)  
- `format` (e.g. mp4)  
- `resolution` (e.g. 1080p, optional)  
- `order` (for sorting in gallery)  
- `is_main` (optional – highlights primary video)

---

## 3. Alembic Setup & Migrations

We will manage schema changes with **Alembic**.

- [x] Add Alembic to project dependencies.
- [x] Generate initial migration from SQLAlchemy models.
- [x] Configure Alembic to use env-based database URL.
- [x] Ensure autogenerate picks up changes from models.

**Tasks:**

- [ ] Initialize Alembic:

  ```bash
  alembic init migrations
  ```

- [ ] Configure `alembic.ini` to use the app's DB URL (via env var or config).  
- [ ] Update `migrations/env.py` to import SQLAlchemy `Base` from the app.  
- [ ] Create the first migration:

  ```bash
  alembic revision --autogenerate -m "initial tables"
  ```

- [ ] Apply migrations:

  ```bash
  alembic upgrade head
  ```

- [ ] For future schema changes:
  - Update models
  - Run `alembic revision --autogenerate -m "..."`  
  - Run `alembic upgrade head`

---

## 4. Cloudinary Integration (Images & Videos)

We are using **Cloudinary** as the single source for media storage (CDN + transforms).

### 4.1 Setup

- [x] Add dependency:

  ```bash
  pip install cloudinary
  ```

- [x] Configure credentials via environment variables:

  ```text
  CLOUDINARY_CLOUD_NAME=
  CLOUDINARY_API_KEY=
  CLOUDINARY_API_SECRET=
  ```

- [ ] In app startup, configure Cloudinary:

  ```python
  import cloudinary

  cloudinary.config(
      cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
      api_key=os.getenv("CLOUDINARY_API_KEY"),
      api_secret=os.getenv("CLOUDINARY_API_SECRET"),
      secure=True,
  )
  ```

### 4.2 Responsibilities

**Cloudinary will handle:**

- Storing images + videos  
- Generating optimized delivery URLs  
- On-the-fly transforms (resize, format, quality)  
- Auto thumbnails for videos  
- CDN & caching for fast global delivery  

The backend will:

- Pre-process images where needed (ratio, size, format)  
- Validate uploads (MIME, size)  
- Store final Cloudinary URLs in the DB  
- Include these URLs in Elasticsearch documents  

---

## 5. Media Processing

### 5.1 Image Rules & Processing

**Final decisions:**

- ✅ All product images must share:
  - **Ratio:** `1:1` (square)  
  - **Base size:** `800 x 800` pixels (can be configurable)  
  - **Format:** prefer `WebP` for web use  

- ✅ Even if the uploaded image has a different ratio/size, the system will:
  - Read image bytes  
  - Convert to RGB  
  - Resize and/or pad to enforce a **1:1** ratio  
  - Resize to `800 x 800`  
  - Convert to `WebP` (or JPEG fallback if needed)  
  - Upload the processed version to Cloudinary  
  - Never serve raw/original uploads to the frontend  

**Upload flow (images):**

1. FastAPI endpoint receives `UploadFile`.  
2. Read bytes and send to a `process_product_image()` utility (Pillow).  
3. Utility enforces required ratio/size/format.  
4. Processed image bytes are uploaded to Cloudinary using the image API.  
5. Cloudinary returns the final URL.  
6. Backend saves `ProductImage` row with that URL.  
7. Product is re-indexed in Elasticsearch including `images` and `main_image`.

### 5.2 Video Handling

**Decisions:**

- ✅ Videos are uploaded as-is (no heavy processing in FastAPI).  
- ✅ Cloudinary handles transcoding, streaming, and thumbnails.  
- ✅ Backend is responsible for:
  - Validating the incoming file (MIME, max size).  
  - Calling Cloudinary video upload (`upload_large` if needed).  
  - Persisting returned metadata in `ProductVideo`.  
  - Exposing URLs to frontend (video URL + thumbnail).  
  - Indexing video metadata into Elasticsearch.

**Upload flow (videos):**

1. FastAPI receives `UploadFile`.  
2. Validate size and MIME type (e.g., `video/mp4`, `video/webm`).  
3. Use `cloudinary.uploader.upload` or `upload_large` with `resource_type="video"`.  
4. Extract from response:
   - `secure_url` → `url`  
   - `duration`  
   - `format`  
   - any thumbnail URL (`eager` or `thumbnail` options)  
5. Save `ProductVideo` row.  
6. Re-index product in Elasticsearch with video info.

---

## 6. Elasticsearch Design

We index **one document per Product** that includes variants, images, and videos.

### 6.1 Indexed Product Document

Fields (conceptual):

- `id`  
- `title`  
- `description`  
- `brand`  
- `category`  

**Variants (array):**

- `variants`:  
  - `color`  
  - `size`  
  - `price`  
  - `stock`  

**Images:**

- `images`: array of:
  - `url`
  - `order`
  - `is_main`
- `main_image`: single URL (for fast list views)

**Videos:**

- `videos`: array of:
  - `url`
  - `thumbnail_url`
  - `order`
  - `is_main` (optional)
- `main_video`: single URL (if any)

### 6.2 Search Features

- [x] Full-text search (title + description):
  - `multi_match`, boosting `title`
  - fuzzy search enabled

- [x] Filters:
  - brand  
  - category  
  - color (from variants)  
  - size (from variants)  
  - price range (from variants)  
  - in-stock only (variant `stock > 0`)

- [x] Aggregations (facets):
  - brands  
  - categories  
  - colors  

- [x] Autocomplete:
  - `completion` field on product title (`title_suggest`)  
  - Endpoint: `/autocomplete?q=...`

---

## 7. FastAPI Endpoints

### 7.1 Product & Variant

- [x] `POST /products/`
  - Create a product (base data).
  - Optionally accept variants or create them via a separate endpoint.
  - Index in Elasticsearch after commit.

- [x] `GET /products/{id}`
  - Return product + variants + media from DB.

- [x] `GET /products/`
  - Paginated product list from DB.

- [ ] `PUT /products/{id}`
  - Update product info, then re-index in Elasticsearch.

- [ ] `DELETE /products/{id}`
  - Soft/hard delete product.
  - Remove from Elasticsearch index.

- [x] `POST /products/{product_id}/variants`
  - Create one or more variants for a product.

- [ ] `PATCH /variants/{variant_id}`
  - Update variant data (color, size, price, etc.).

- [ ] `PATCH /variants/{variant_id}/stock`
  - Safely update stock counts.

- [ ] `DELETE /variants/{variant_id}`
  - Remove variant, then re-index product in Elasticsearch.

---

### 7.2 Image Endpoints

- [x] `POST /products/{product_id}/upload-image`
  - Accept `UploadFile`.
  - Run through `process_product_image()` (Pillow).
  - Upload result to Cloudinary.
  - Create `ProductImage` row.
  - If first image, set `is_main = True`.
  - Re-index product in Elasticsearch.

- [ ] `DELETE /products/{product_id}/images/{image_id}`
  - Delete image row.
  - (Optional) request deletion from Cloudinary.
  - Re-index product.

- [ ] `PATCH /products/{product_id}/images/{image_id}/set-main`
  - Set one image as `is_main = True`, unset others.
  - Update `main_image` field in Elasticsearch via re-index.

---

### 7.3 Video Endpoints

- [x] `POST /products/{product_id}/upload-video`
  - Accept `UploadFile` (video).
  - Validate MIME & size.
  - Upload to Cloudinary with `resource_type="video"`.
  - Store `ProductVideo` row with URL & metadata.
  - Re-index product in Elasticsearch.

- [ ] `DELETE /products/{product_id}/videos/{video_id}`
  - Delete DB record.
  - (Optional) delete from Cloudinary.
  - Re-index product.

- [ ] `PATCH /products/{product_id}/videos/{video_id}/set-main`
  - Mark a video as main; update ES `main_video`.

---

### 7.4 Search Endpoints

- [x] `GET /search`
  - Query parameters:
    - `q`
    - `brand`
    - `category`
    - `color`
    - `size`
    - `min_price`
    - `max_price`
    - `page`, `page_size`
  - Returns:
    - documents with `main_image`
    - relevant media fields
    - aggregations

- [x] `GET /autocomplete`
  - Uses ES `completion` suggester on `title_suggest`.

---

## 8. Infrastructure & Dev Setup

### 8.1 Docker Compose

- [x] Services:
  - `db` (PostgreSQL)  
  - `elasticsearch`  
  - `kibana`  
  - `app` (FastAPI + uvicorn)  

- [ ] Add Cloudinary config via environment variables in `app` service.

### 8.2 Python Dependencies

Current set to include:

```text
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
alembic
pydantic
pydantic-settings
elasticsearch[async]
python-dotenv
pillow
cloudinary
```

(plus test libraries later, e.g. `pytest`.)

---

## 9. Next Steps (Action Items)

### Models & Migrations

- [ ] Implement `Product`, `ProductVariant`, `ProductImage`, `ProductVideo` models.  
- [ ] Initialize Alembic and create/verify initial migration.  
- [ ] Add migrations whenever fields are added/changed.

### Cloudinary Integration

- [ ] Implement `cloudinary.config` setup.  
- [ ] Implement `upload_image_to_cloudinary(bytes, public_id)` helper.  
- [ ] Implement `upload_video_to_cloudinary(file, public_id)` helper.  

### Media Endpoints

- [ ] Implement image upload endpoint using the Pillow-based processing flow.  
- [ ] Implement video upload endpoint with size/type validation.  
- [ ] Implement delete and set-main logic for both images and videos.

### Elasticsearch

- [ ] Finalize ES index mapping including:
  - product fields
  - variant nested fields
  - `images` + `main_image`
  - `videos` + `main_video`
  - `title_suggest` for autocomplete

- [ ] Implement indexing helpers:
  - `index_product(product_id)`
  - `delete_product_from_index(product_id)`

- [ ] Add tests for:
  - Search relevance
  - Filters (size, color, brand)
  - In-stock filtering

### Optional Improvements

- [ ] Background tasks for heavy media operations (Celery/RQ).  
- [ ] Rate limiting on upload endpoints.  
- [ ] Simple admin UI for media management and product catalog.  

---

## 10. Summary

This architecture now supports:

- Clean Product + Variant modeling  
- Product-level images and videos  
- Automatic normalization of image ratio, size, and format  
- Cloudinary-based storage and CDN delivery  
- Elasticsearch-based full-text search and faceted filtering  
- Alembic for safe, versioned schema changes  
- A clear roadmap of endpoints and features to implement next  
