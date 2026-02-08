export function ProductCardSkeleton() {
  return (
    <div className="product-card animate-pulse">
      <div className="aspect-square bg-gray-200 rounded-lg mb-12"></div>
      <div className="h-16 bg-gray-200 rounded mb-8"></div>
      <div className="h-16 bg-gray-200 rounded w-3/4 mb-12"></div>
      <div className="flex justify-between items-center">
        <div className="h-20 bg-gray-200 rounded w-1/3"></div>
        <div className="h-12 bg-gray-200 rounded w-1/4"></div>
      </div>
    </div>
  );
}

export function ProductListSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-16">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function ProductDetailSkeleton() {
  return (
    <div className="min-h-screen bg-white">
      {/* Desktop Breadcrumb */}
      <div className="hidden md:block bg-white">
        <div className="max-w-[1280px] mx-auto px-16 md:px-24">
          <div className="py-12 border-b border-gray-200 animate-pulse">
            <div className="h-20 bg-gray-200 rounded w-2/5 max-w-[360px]"></div>
          </div>
        </div>
      </div>

      <div className="max-w-[1280px] mx-auto">
        <div className="md:flex md:gap-32 lg:gap-40">
          {/* Left: Images */}
          <div className="md:flex-1 md:px-24 md:py-32">
            {/* Mobile Breadcrumb */}
            <div className="md:hidden px-16 pt-12 pb-12 animate-pulse">
              <div className="h-12 bg-gray-200 rounded w-2/3"></div>
            </div>

            {/* Main Image */}
            <div className="h-[300px] md:h-auto md:aspect-square bg-gray-100 relative overflow-hidden md:rounded-xl animate-pulse"></div>

            {/* Thumbnail Gallery */}
            <div className="px-16 md:px-0 mt-8 md:mt-12">
              <div className="flex gap-6 overflow-x-auto pb-2 pt-2 scrollbar-hide animate-pulse">
                {[1, 2].map((i) => (
                  <div
                    key={i}
                    className="w-48 h-48 flex-shrink-0 rounded-lg border-2 border-gray-200 bg-gray-100"
                  ></div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Product Info */}
          <div className="md:flex-1 px-16 md:px-0 md:pr-24 pt-16 pb-16 md:py-32 animate-pulse">
            <div className="h-12 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="h-32 bg-gray-200 rounded w-3/4 mb-12"></div>

            {/* Rating & Reviews */}
            <div className="flex items-center gap-12 mb-16">
              <div className="flex items-center gap-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="w-16 h-16 bg-gray-200 rounded-full"></div>
                ))}
              </div>
              <div className="h-16 bg-gray-200 rounded w-120"></div>
            </div>

            {/* Price */}
            <div className="mb-24 space-y-8">
              <div className="h-40 bg-gray-200 rounded w-1/3"></div>
              <div className="h-12 bg-gray-200 rounded w-1/4"></div>
            </div>

            {/* Variant Selection */}
            <div className="mb-24 space-y-20">
              <div>
                <div className="h-16 bg-gray-200 rounded w-1/3 mb-12"></div>
                <div className="flex flex-wrap gap-8">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-40 bg-gray-200 rounded w-60"></div>
                  ))}
                </div>
              </div>
              <div>
                <div className="h-16 bg-gray-200 rounded w-1/3 mb-12"></div>
                <div className="flex flex-wrap gap-8">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-40 bg-gray-200 rounded w-60"></div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quantity Selector */}
            <div className="mb-24">
              <div className="h-16 bg-gray-200 rounded w-1/4 mb-12"></div>
              <div className="flex items-center gap-12">
                <div className="w-40 h-40 bg-gray-200 rounded"></div>
                <div className="w-40 h-16 bg-gray-200 rounded"></div>
                <div className="w-40 h-40 bg-gray-200 rounded"></div>
              </div>
            </div>

            {/* Add to Cart Button - Desktop */}
            <div className="hidden md:block h-40 bg-gray-200 rounded-lg w-full mb-24"></div>

            {/* Accordions */}
            <div className="space-y-0 border-t border-gray-200">
              {[1, 2, 3].map((i) => (
                <div key={i} className="border-b border-gray-200 py-16">
                  <div className="flex items-center justify-between">
                    <div className="h-16 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-16 bg-gray-200 rounded w-16"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Reviews Section */}
        <div className="px-16 md:px-24 py-24 md:py-32 animate-pulse">
          <div className="border-t border-gray-200 pt-24">
            <div className="h-24 bg-gray-200 rounded w-1/3 mb-20"></div>

            <div className="bg-gray-50 rounded-xl p-20 mb-20">
              <div className="flex flex-col items-center text-center mb-16">
                <div className="h-48 bg-gray-200 rounded w-120 mb-6"></div>
                <div className="flex items-center gap-4 mb-6">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="w-18 h-18 bg-gray-200 rounded-full"></div>
                  ))}
                </div>
                <div className="h-16 bg-gray-200 rounded w-1/2 mb-16"></div>
                <div className="h-40 bg-gray-200 rounded w-full"></div>
              </div>
            </div>

            <div className="space-y-16">
              {[1, 2].map((i) => (
                <div key={i} className="border-b border-gray-200 pb-16">
                  <div className="flex items-start justify-between mb-8">
                    <div className="space-y-6">
                      <div className="h-16 bg-gray-200 rounded w-160"></div>
                      <div className="h-12 bg-gray-200 rounded w-120"></div>
                    </div>
                    <div className="flex items-center gap-4">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <div key={star} className="w-14 h-14 bg-gray-200 rounded-full"></div>
                      ))}
                    </div>
                  </div>
                  <div className="h-16 bg-gray-200 rounded w-2/3 mb-6"></div>
                  <div className="h-12 bg-gray-200 rounded w-full"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function CartItemSkeleton() {
  return (
    <div className="flex gap-16 p-16 border-b border-gray-200 animate-pulse">
      <div className="w-80 h-80 bg-gray-200 rounded"></div>
      <div className="flex-1">
        <div className="h-16 bg-gray-200 rounded mb-8"></div>
        <div className="h-12 bg-gray-200 rounded w-1/2 mb-12"></div>
        <div className="h-20 bg-gray-200 rounded w-1/4"></div>
      </div>
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="container-padding py-24 animate-pulse">
      <div className="h-32 bg-gray-200 rounded mb-24 w-1/3"></div>
      <div className="space-y-12">
        <div className="h-16 bg-gray-200 rounded"></div>
        <div className="h-16 bg-gray-200 rounded"></div>
        <div className="h-16 bg-gray-200 rounded w-4/5"></div>
      </div>
    </div>
  );
}
