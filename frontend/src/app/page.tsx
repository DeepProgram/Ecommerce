'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { catalogService } from '@/services/catalogService';
import { ProductListSkeleton } from '@/components/Skeletons';
import ProductCard from '@/components/ProductCard';

export default function HomePage() {
  const [trendingProducts, setTrendingProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    catalogService.getProducts({ limit: 8 })
      .then(data => setTrendingProducts(data.results || data))
      .catch(err => console.error('Error loading products:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-brand-600 to-brand-700 text-white overflow-hidden">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24 py-48 md:py-64 lg:py-80">
          <div className="max-w-[600px]">
            <h1 className="text-[36px] leading-[44px] md:text-[48px] md:leading-[56px] lg:text-[56px] lg:leading-[64px] mb-16 font-bold">
              New Arrivals<br />For You
            </h1>
            <p className="text-[16px] leading-[24px] md:text-[18px] md:leading-[28px] mb-32 opacity-95">
              Discover the latest trends in fashion. Shop our newest collection with exclusive deals.
            </p>
            <Link 
              href="/products" 
              className="inline-flex items-center justify-center px-32 h-48 bg-white text-brand-600 hover:bg-gray-50 rounded-lg font-semibold text-[15px] leading-none transition-colors shadow-lg"
            >
              Shop Now
            </Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24 py-32 md:py-24 lg:py-28">
          <div className="grid grid-cols-4 gap-12 md:gap-20 lg:gap-24">
            <CategoryIcon href="/products?category=women" icon="👗" label="Women" />
            <CategoryIcon href="/products?category=men" icon="👔" label="Men" />
            <CategoryIcon href="/products?category=shoes" icon="👟" label="Shoes" />
            <CategoryIcon href="/products?category=accessories" icon="👜" label="Accessories" />
          </div>
        </div>
      </section>

      {/* Trending Products */}
      <section className="bg-gray-50">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24 py-40 md:py-32 lg:py-40">
          <div className="flex items-center justify-between mb-32">
            <h2 className="text-[24px] leading-[32px] md:text-[28px] md:leading-[36px] font-bold text-gray-900">
              Trending Now
            </h2>
            <Link 
              href="/products" 
              className="text-[15px] text-brand-600 hover:text-brand-700 font-semibold transition-colors"
            >
              View All →
            </Link>
          </div>

          {loading ? (
            <ProductListSkeleton count={8} />
          ) : trendingProducts.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-16 md:gap-20 lg:gap-24">
              {trendingProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="text-center py-48">
              <p className="text-[16px] text-gray-500 mb-16">No products available yet</p>
              <Link 
                href="/products" 
                className="inline-flex items-center justify-center px-24 h-44 bg-brand-600 text-white rounded-lg font-semibold text-[14px] leading-none hover:bg-brand-700 transition-colors"
              >
                Browse All Products
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Special Offers */}
      <section className="bg-white">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24 py-40 md:py-32 lg:py-40">
          <h2 className="text-[24px] leading-[32px] md:text-[28px] md:leading-[36px] font-bold text-gray-900 mb-32">
            Special Offers
          </h2>
          <div className="grid md:grid-cols-2 gap-16 md:gap-20 lg:gap-24">
            <OfferCard
              title="20% Off"
              subtitle="Summer Sale"
              bgColor="bg-gradient-to-br from-orange-400 to-pink-500"
              link="/products?sale=summer"
            />
            <OfferCard
              title="Buy 1 Get 1 Free"
              subtitle="Selected Items"
              bgColor="bg-gradient-to-br from-blue-400 to-purple-500"
              link="/products?promo=bogo"
            />
          </div>
        </div>
      </section>
    </main>
  );
}

function CategoryIcon({ href, icon, label }: { href: string; icon: string; label: string }) {
  return (
    <Link 
      href={href}
      className="flex flex-col items-center gap-8 md:gap-12 p-12 md:p-20 bg-white rounded-xl border border-gray-200 hover:border-brand-600 hover:shadow-lg transition-all duration-200"
    >
      <div className="w-40 h-40 md:w-56 md:h-56 lg:w-64 lg:h-64 rounded-full bg-brand-50 flex items-center justify-center text-[20px] md:text-[28px] lg:text-[32px]">
        {icon}
      </div>
      <span className="text-[13px] md:text-[14px] lg:text-[15px] font-semibold text-gray-900 text-center">{label}</span>
    </Link>
  );
}

function OfferCard({ title, subtitle, bgColor, link }: { 
  title: string; 
  subtitle: string; 
  bgColor: string;
  link: string;
}) {
  return (
    <Link 
      href={link}
      className={`${bgColor} rounded-xl p-32 md:p-40 text-white hover:opacity-90 transition-opacity duration-200 min-h-[160px] md:min-h-[200px] flex flex-col justify-center shadow-card`}
    >
      <h3 className="text-[28px] leading-[34px] md:text-[36px] md:leading-[44px] font-bold mb-8">{title}</h3>
      <p className="text-[15px] md:text-[16px] opacity-90">{subtitle}</p>
    </Link>
  );
}
