'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { catalogService } from '@/services/catalogService';
import { cartService } from '@/services/cartService';
import { ProductDetailSkeleton } from '@/components/Skeletons';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';

interface ProductDetailPageProps {
  params: {
    slug: string;
  };
}

export default function ProductDetailPage({ params }: ProductDetailPageProps) {
  const [product, setProduct] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState(0);
  const [selectedVariant, setSelectedVariant] = useState<any>(null);
  const [quantity, setQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);
  const [openAccordion, setOpenAccordion] = useState<string | null>('description');
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    loadProduct();
  }, [params.slug]);

  const loadProduct = async () => {
    setLoading(true);
    setImageErrors(new Set());
    try {
      const data = await catalogService.getProduct(params.slug);
      setProduct(data);
      if (data.variants && data.variants.length > 0) {
        setSelectedVariant(data.variants[0]);
      }
    } catch (error) {
      console.error('Error loading product:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleImageError = (index: number) => {
    setImageErrors(prev => new Set(prev).add(index));
  };

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    setAddingToCart(true);
    try {
      await cartService.addToCart(
        product.id,
        selectedVariant?.id,
        quantity
      );
      alert('Added to cart!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('Failed to add to cart');
    } finally {
      setAddingToCart(false);
    }
  };

  const getSelectedPrice = () => {
    if (selectedVariant) {
      return parseFloat(selectedVariant.effective_price || selectedVariant.price);
    }
    return parseFloat(product.base_price);
  };

  const getSelectedStock = () => {
    if (selectedVariant) {
      return selectedVariant.stock_quantity;
    }
    return 0;
  };

  if (loading) {
    return <ProductDetailSkeleton />;
  }

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-[20px] font-bold text-gray-900 mb-12">Product Not Found</h2>
          <Link href="/products" className="text-brand-600 hover:text-brand-700">
            Back to Products
          </Link>
        </div>
      </div>
    );
  }

  const images = product.images && product.images.length > 0 
    ? product.images 
    : product.primary_image 
    ? [product.primary_image] 
    : [];

  return (
    <div className="min-h-screen bg-white">
      {/* Breadcrumb */}
      <div className="hidden md:block bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24 py-12">
          <div className="flex items-center gap-8 text-[13px] text-gray-500">
            <Link href="/" className="hover:text-brand-600">Home</Link>
            <span>›</span>
            <Link href="/products" className="hover:text-brand-600">Products</Link>
            {product.category && (
              <>
                <span>›</span>
                <Link href={`/products?category=${product.category.slug}`} className="hover:text-brand-600">
                  {product.category.name}
                </Link>
              </>
            )}
            <span>›</span>
            <span className="text-gray-900 font-medium truncate">{product.name}</span>
          </div>
        </div>
      </div>

      <div className="max-w-[1280px] mx-auto">
        <div className="md:flex md:gap-32 lg:gap-40">
          {/* Left: Images */}
          <div className="md:flex-1 md:px-24 md:py-32">
            {/* Mobile Breadcrumb - Above Image */}
            <div className="md:hidden px-16 pt-12 pb-12 flex items-center gap-6 text-[12px] text-gray-500">
              <Link href="/" className="hover:text-brand-600">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
              </Link>
              <span>›</span>
              <Link href="/products" className="hover:text-brand-600">Products</Link>
              {product.category && (
                <>
                  <span>›</span>
                  <Link href={`/products?category=${product.category.slug}`} className="hover:text-brand-600 truncate">
                    {product.category.name}
                  </Link>
                </>
              )}
            </div>

            {/* Main Image */}
            <div className="h-[300px] md:h-auto md:aspect-square bg-gray-100 relative overflow-hidden md:rounded-xl">
              {images.length > 0 && !imageErrors.has(selectedImage) ? (
                <Image
                  src={images[selectedImage].image.startsWith('http') ? images[selectedImage].image : `http://localhost${images[selectedImage].image}`}
                  alt={images[selectedImage].alt_text || product.name}
                  fill
                  className="object-cover"
                  priority
                  onError={() => handleImageError(selectedImage)}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <svg width="80" height="80" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="120" height="120" fill="#F3F4F6"/>
                    <path d="M60 40C54.4772 40 50 44.4772 50 50C50 55.5228 54.4772 60 60 60C65.5228 60 70 55.5228 70 50C70 44.4772 65.5228 40 60 40Z" fill="#D1D5DB"/>
                    <path d="M35 75L45 65L55 75L70 60L85 75V85H35V75Z" fill="#D1D5DB"/>
                  </svg>
                </div>
              )}
            </div>

            {/* Thumbnail Gallery */}
            {images.length > 1 && (
              <div className="px-16 md:px-0 mt-8 md:mt-12">
                <div className="flex gap-6 overflow-x-auto pb-2 pt-2 scrollbar-hide">
                  {images.map((img: any, index: number) => (
                    <button
                      key={img.id}
                      onClick={() => setSelectedImage(index)}
                      className={`w-48 h-48 md:w-52 md:h-52 flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all ${
                        selectedImage === index
                          ? 'border-brand-600 ring-2 ring-brand-200'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="relative w-full h-full bg-gray-100">
                        {!imageErrors.has(index) ? (
                          <Image
                            src={img.image.startsWith('http') ? img.image : `http://localhost${img.image}`}
                            alt={img.alt_text || product.name}
                            fill
                            className="object-cover"
                            onError={() => handleImageError(index)}
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <svg width="24" height="24" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <rect width="120" height="120" fill="#F3F4F6"/>
                              <path d="M60 40C54.4772 40 50 44.4772 50 50C50 55.5228 54.4772 60 60 60C65.5228 60 70 55.5228 70 50C70 44.4772 65.5228 40 60 40Z" fill="#D1D5DB"/>
                              <path d="M35 75L45 65L55 75L70 60L85 75V85H35V75Z" fill="#D1D5DB"/>
                            </svg>
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Product Info */}
          <div className="md:flex-1 px-16 md:px-0 md:pr-24 pt-16 pb-16 md:py-32">
            {/* Brand */}
            {product.brand && (
              <p className="text-[13px] text-gray-500 mb-8">{product.brand.name}</p>
            )}

            {/* Product Name */}
            <h1 className="text-[24px] leading-[32px] md:text-[28px] md:leading-[36px] font-bold text-gray-900 mb-12">
              {product.name}
            </h1>

            {/* Rating & Reviews */}
            <div className="flex items-center gap-12 mb-16">
              <div className="flex items-center gap-4">
                {[...Array(5)].map((_, i) => (
                  <span
                    key={i}
                    className={`text-[16px] ${
                      i < Math.round(product.average_rating || 0)
                        ? 'text-rating'
                        : 'text-gray-300'
                    }`}
                  >
                    ★
                  </span>
                ))}
              </div>
              <span className="text-[14px] text-gray-600">
                {product.average_rating?.toFixed(1) || '0.0'} ({product.review_count || 0} reviews)
              </span>
            </div>

            {/* Price */}
            <div className="mb-24">
              <p className="text-[32px] leading-[40px] font-bold text-brand-600">
                ${getSelectedPrice().toFixed(2)}
              </p>
              {getSelectedStock() > 0 ? (
                <p className="text-[13px] text-success mt-4">In Stock ({getSelectedStock()} available)</p>
              ) : (
                <p className="text-[13px] text-danger mt-4">Out of Stock</p>
              )}
            </div>

            {/* Variant Selection */}
            {product.has_variants && product.variants && product.variants.length > 0 && (
              <div className="mb-24 space-y-20">
                {/* Get unique attribute types */}
                {(() => {
                  const attributeTypes = new Set<string>();
                  product.variants.forEach((v: any) => {
                    v.attribute_values?.forEach((attr: any) => {
                      attributeTypes.add(attr.attribute_slug);
                    });
                  });

                  return Array.from(attributeTypes).map((attrSlug) => {
                    const attrName = product.variants[0].attribute_values?.find(
                      (a: any) => a.attribute_slug === attrSlug
                    )?.attribute_name || attrSlug;

                    const values = new Set<string>();
                    product.variants.forEach((v: any) => {
                      const attrValue = v.attribute_values?.find(
                        (a: any) => a.attribute_slug === attrSlug
                      );
                      if (attrValue) values.add(attrValue.value);
                    });

                    const selectedValue = selectedVariant?.attribute_values?.find(
                      (a: any) => a.attribute_slug === attrSlug
                    )?.value;

                    return (
                      <div key={attrSlug}>
                        <h3 className="text-[14px] font-semibold text-gray-900 mb-12">
                          {attrName}: <span className="text-brand-600">{selectedValue}</span>
                        </h3>
                        <div className="flex flex-wrap gap-8">
                          {Array.from(values).map((value) => {
                            const variant = product.variants.find((v: any) =>
                              v.attribute_values?.some(
                                (a: any) => a.attribute_slug === attrSlug && a.value === value
                              )
                            );
                            
                            const isSelected = selectedValue === value;
                            const isAvailable = variant?.stock_quantity > 0;

                            return (
                              <button
                                key={value}
                                onClick={() => isAvailable && setSelectedVariant(variant)}
                                disabled={!isAvailable}
                                className={`px-16 h-40 rounded border text-[14px] font-medium transition-all ${
                                  isSelected
                                    ? 'border-brand-600 bg-brand-50 text-brand-600'
                                    : isAvailable
                                    ? 'border-gray-300 bg-white text-gray-900 hover:border-brand-600'
                                    : 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed line-through'
                                }`}
                              >
                                {value}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            )}

            {/* Quantity Selector */}
            <div className="mb-24">
              <h3 className="text-[14px] font-semibold text-gray-900 mb-12">Quantity</h3>
              <div className="flex items-center gap-12">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="w-40 h-40 border border-gray-300 rounded flex items-center justify-center text-[18px] hover:border-brand-600 transition-colors"
                >
                  −
                </button>
                <span className="text-[16px] font-semibold text-gray-900 w-40 text-center">
                  {quantity}
                </span>
                <button
                  onClick={() => setQuantity(Math.min(getSelectedStock(), quantity + 1))}
                  disabled={quantity >= getSelectedStock()}
                  className="w-40 h-40 border border-gray-300 rounded flex items-center justify-center text-[18px] hover:border-brand-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  +
                </button>
              </div>
            </div>

            {/* Add to Cart Button - Desktop */}
            <button
              onClick={handleAddToCart}
              disabled={getSelectedStock() === 0 || addingToCart}
              className="hidden md:flex w-full h-52 bg-brand-600 text-white rounded-lg font-semibold text-[16px] leading-none items-center justify-center hover:bg-brand-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed mb-24"
            >
              {addingToCart ? 'Adding...' : getSelectedStock() === 0 ? 'Out of Stock' : 'Add to Cart'}
            </button>

            {/* Accordions */}
            <div className="space-y-0 border-t border-gray-200">
              <AccordionItem
                title="Description"
                isOpen={openAccordion === 'description'}
                onToggle={() => setOpenAccordion(openAccordion === 'description' ? null : 'description')}
              >
                <p className="text-[14px] leading-[22px] text-gray-700">
                  {product.description || 'No description available.'}
                </p>
              </AccordionItem>

              <AccordionItem
                title="Shipping & Delivery"
                isOpen={openAccordion === 'shipping'}
                onToggle={() => setOpenAccordion(openAccordion === 'shipping' ? null : 'shipping')}
              >
                <div className="text-[14px] leading-[22px] text-gray-700 space-y-8">
                  <p>• Free shipping on orders over $50</p>
                  <p>• Standard delivery: 5-7 business days</p>
                  <p>• Express delivery: 2-3 business days</p>
                </div>
              </AccordionItem>

              <AccordionItem
                title="Returns & Exchanges"
                isOpen={openAccordion === 'returns'}
                onToggle={() => setOpenAccordion(openAccordion === 'returns' ? null : 'returns')}
              >
                <div className="text-[14px] leading-[22px] text-gray-700 space-y-8">
                  <p>• 30-day return policy</p>
                  <p>• Free returns on all orders</p>
                  <p>• Items must be unworn with tags attached</p>
                </div>
              </AccordionItem>
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <div className="px-16 md:px-24 py-24 md:py-32">
          <div className="border-t border-gray-200 pt-24">
            <h2 className="text-[18px] leading-[24px] md:text-[22px] md:leading-[28px] font-bold text-gray-900 mb-20">
              Customer Reviews
            </h2>
            
            {/* Rating Summary */}
            <div className="bg-gray-50 rounded-xl p-20 mb-20">
              <div className="flex flex-col items-center text-center mb-16">
                <div className="text-[40px] leading-[48px] font-bold text-gray-900 mb-6">
                  {product.average_rating?.toFixed(1) || '0.0'}
                </div>
                <div className="flex items-center gap-4 mb-6">
                  {[...Array(5)].map((_, i) => (
                    <span
                      key={i}
                      className={`text-[18px] ${
                        i < Math.round(product.average_rating || 0)
                          ? 'text-rating'
                          : 'text-gray-300'
                      }`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                <p className="text-[13px] text-gray-600 mb-16">
                  Based on {product.review_count || 0} reviews
                </p>
                <button className="w-full h-40 bg-brand-600 text-white rounded-lg font-medium text-[14px] hover:bg-brand-700 transition-colors">
                  Write a Review
                </button>
              </div>
            </div>

            {/* Reviews List */}
            {product.reviews && product.reviews.length > 0 ? (
              <div className="space-y-16">
                {product.reviews.map((review: any) => (
                  <div key={review.id} className="border-b border-gray-200 pb-16 last:border-b-0">
                    <div className="flex items-start justify-between mb-8">
                      <div>
                        <p className="text-[14px] font-semibold text-gray-900">
                          {review.user.first_name} {review.user.last_name}
                        </p>
                        <p className="text-[12px] text-gray-500">
                          {new Date(review.created_at).toLocaleDateString('en-US', { 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric' 
                          })}
                        </p>
                      </div>
                      <div className="flex items-center gap-4">
                        {[...Array(5)].map((_, i) => (
                          <span
                            key={i}
                            className={`text-[14px] ${
                              i < review.rating ? 'text-rating' : 'text-gray-300'
                            }`}
                          >
                            ★
                          </span>
                        ))}
                      </div>
                    </div>
                    {review.title && (
                      <h4 className="text-[14px] font-semibold text-gray-900 mb-6">
                        {review.title}
                      </h4>
                    )}
                    <p className="text-[13px] text-gray-700 leading-[20px]">
                      {review.comment}
                    </p>
                    {review.is_verified_purchase && (
                      <span className="inline-block mt-8 text-[11px] text-success font-medium">
                        ✓ Verified Purchase
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[13px] text-gray-500 text-center py-16">No reviews yet. Be the first to review this product!</p>
            )}
          </div>
        </div>
      </div>

      {/* Sticky Add to Cart - Mobile */}
      <div className="fixed md:hidden bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-sticky p-16 z-40">
        <button
          onClick={handleAddToCart}
          disabled={getSelectedStock() === 0 || addingToCart}
          className="w-full h-48 bg-brand-600 text-white rounded-lg font-semibold text-[15px] leading-none hover:bg-brand-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {addingToCart ? 'Adding...' : getSelectedStock() === 0 ? 'Out of Stock' : `Add to Cart - $${getSelectedPrice().toFixed(2)}`}
        </button>
      </div>
    </div>
  );
}

function AccordionItem({ 
  title, 
  children, 
  isOpen, 
  onToggle 
}: { 
  title: string; 
  children: React.ReactNode; 
  isOpen: boolean; 
  onToggle: () => void;
}) {
  return (
    <div className="border-b border-gray-200">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between py-16 text-left hover:text-brand-600 transition-colors"
      >
        <span className="text-[15px] font-semibold text-gray-900">{title}</span>
        <span className={`text-[20px] transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          ⌄
        </span>
      </button>
      {isOpen && (
        <div className="pb-16">
          {children}
        </div>
      )}
    </div>
  );
}
