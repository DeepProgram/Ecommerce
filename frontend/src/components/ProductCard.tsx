'use client';

import Link from 'next/link';
import Image from 'next/image';

interface ProductCardProps {
  product: {
    id: number;
    name: string;
    slug: string;
    base_price: string;
    brand?: {
      name: string;
    };
    primary_image?: {
      image: string;
      alt_text: string;
    };
    average_rating?: number;
    review_count?: number;
  };
}

export default function ProductCard({ product }: ProductCardProps) {
  const imageUrl = product.primary_image?.image 
    ? (product.primary_image.image.startsWith('http') 
        ? product.primary_image.image 
        : `http://localhost${product.primary_image.image}`)
    : '/placeholder-product.svg';

  return (
    <Link href={`/products/${product.slug}`} className="group block">
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg hover:border-brand-600 transition-all duration-200">
        <div className="aspect-square bg-gray-100 overflow-hidden relative">
          {product.primary_image?.image ? (
            <Image
              src={imageUrl}
              alt={product.primary_image?.alt_text || product.name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
              sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400 text-[14px]">
              No Image
            </div>
          )}
        </div>

        <div className="p-12">
          {product.brand && (
            <p className="text-[12px] text-gray-500 mb-4">{product.brand.name}</p>
          )}
          
          <h3 className="text-[14px] leading-[20px] font-medium text-gray-900 line-clamp-2 mb-8 min-h-[40px]">
            {product.name}
          </h3>

          <div className="flex items-center justify-between">
            <p className="text-[18px] leading-[24px] text-brand-600 font-semibold">
              ${parseFloat(product.base_price).toFixed(2)}
            </p>

            {product.average_rating && (
              <div className="flex items-center gap-4">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <span
                      key={i}
                      className={`text-[11px] ${
                        i < Math.round(product.average_rating!)
                          ? 'text-rating'
                          : 'text-gray-300'
                      }`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                {product.review_count ? (
                  <span className="text-[11px] text-gray-500">
                    ({product.review_count})
                  </span>
                ) : null}
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
