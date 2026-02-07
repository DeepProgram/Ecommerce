'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { catalogService } from '@/services/catalogService';
import ProductCard from '@/components/ProductCard';
import { ProductListSkeleton } from '@/components/Skeletons';
import FilterSidebar from '@/components/FilterSidebar';
import FilterBottomSheet from '@/components/FilterBottomSheet';

export default function ProductsPage() {
  const searchParams = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [sortBy, setSortBy] = useState('popular');

  const category = searchParams.get('category');
  const searchQuery = searchParams.get('q');

  useEffect(() => {
    loadProducts();
  }, [category, searchQuery, sortBy]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (category) params.category = category;
      if (searchQuery) params.search = searchQuery;
      if (sortBy) params.ordering = getSortParam(sortBy);
      
      const data = await catalogService.getProducts(params);
      setProducts(data.results || data);
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSortParam = (sort: string) => {
    const sortMap: any = {
      'popular': '-review_count',
      'price_low': 'base_price',
      'price_high': '-base_price',
      'newest': '-created_at',
      'rating': '-average_rating',
    };
    return sortMap[sort] || '-review_count';
  };

  return (
    <div className="min-h-screen bg-white md:bg-gray-50">
      {/* Breadcrumb - Desktop Only */}
      <div className="hidden md:block bg-white border-b border-gray-200">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24 py-12">
          <div className="flex items-center gap-8 text-[13px] text-gray-500">
            <a href="/" className="hover:text-brand-600">Home</a>
            <span>›</span>
            <span className="text-gray-900 font-medium">
              {category ? category.charAt(0).toUpperCase() + category.slice(1) : searchQuery ? `Search: "${searchQuery}"` : 'All Products'}
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-[1280px] mx-auto">
        {/* Header Section */}
        <div className="px-16 md:px-24 pt-20 pb-16 md:py-24">
          {/* Title & Count */}
          <div className="mb-16">
            <h1 className="text-[22px] leading-[28px] md:text-[28px] md:leading-[36px] font-bold text-gray-900 mb-6">
              {category ? category.charAt(0).toUpperCase() + category.slice(1) : searchQuery ? 'Search Results' : 'Products'}
            </h1>
            <p className="text-[13px] md:text-[14px] text-gray-500">
              {loading ? 'Loading products...' : `${products.length} products found`}
            </p>
          </div>

          {/* Filter & Sort Row */}
          <div className="flex gap-8 md:justify-end">
            {/* Mobile Filter Button */}
            <button
              onClick={() => setShowMobileFilters(true)}
              className="md:hidden flex-1 flex items-center justify-center gap-8 h-40 px-16 border border-gray-300 rounded-lg text-[14px] font-medium text-gray-900 bg-white hover:border-brand-600 transition-colors"
            >
              <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filters
            </button>

            {/* Sort Dropdown */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="flex-1 md:flex-initial md:w-auto h-40 px-12 md:px-16 border border-gray-300 rounded-lg text-[14px] font-medium text-gray-900 bg-white hover:border-brand-600 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-600 focus:ring-opacity-20 appearance-none"
              style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%236B7280\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\'%3E%3C/path%3E%3C/svg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center', backgroundSize: '20px', paddingRight: '36px' }}
            >
              <option value="popular">Most Popular</option>
              <option value="newest">Newest</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="rating">Highest Rated</option>
            </select>
          </div>
        </div>

        {/* Main Content */}
        <div className="md:flex md:gap-20 lg:gap-24">
          {/* Desktop Filters Sidebar */}
          <div className="hidden md:block md:px-24 md:w-[240px] lg:w-[260px] flex-shrink-0">
            <FilterSidebar />
          </div>

          {/* Products Grid */}
          <div className="flex-1 px-16 md:px-0 md:pr-24 pb-24 md:pb-32 min-w-0" key={`products-${loading}`}>
            {loading ? (
              <ProductListSkeleton count={12} />
            ) : products.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-12 md:gap-16 lg:gap-20">
                {products.map((product: any) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center min-h-[400px] md:min-h-[500px]">
                <div className="text-center px-24">
                  <div className="w-80 h-80 md:w-96 md:h-96 mx-auto mb-20 md:mb-24 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-32 h-32 md:w-40 md:h-40 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <h3 className="text-[18px] leading-[24px] md:text-[20px] md:leading-[28px] font-bold text-gray-900 mb-8 md:mb-10">
                    No Products Found
                  </h3>
                  <p className="text-[13px] leading-[20px] md:text-[14px] md:leading-[22px] text-gray-500 mb-20 md:mb-24">
                    Try adjusting your filters or search terms
                  </p>
                  <a
                    href="/products"
                    className="inline-flex items-center justify-center px-24 h-40 bg-brand-600 text-white rounded font-medium text-[14px] leading-none hover:bg-brand-700 transition-colors"
                  >
                    Clear Filters
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Filter Bottom Sheet */}
      {showMobileFilters && (
        <FilterBottomSheet onClose={() => setShowMobileFilters(false)} />
      )}
    </div>
  );
}
