'use client';

import { useState } from 'react';

export default function FilterSidebar() {
  const [priceRange, setPriceRange] = useState([0, 1000]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedSizes, setSelectedSizes] = useState<string[]>([]);
  const [selectedColors, setSelectedColors] = useState<string[]>([]);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);

  const categories = ['Women', 'Men', 'Shoes', 'Accessories'];
  const sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
  const colors = [
    { name: 'Black', hex: '#000000' },
    { name: 'White', hex: '#FFFFFF' },
    { name: 'Red', hex: '#EF4444' },
    { name: 'Blue', hex: '#3B82F6' },
    { name: 'Green', hex: '#10B981' },
    { name: 'Yellow', hex: '#F59E0B' },
  ];

  const toggleCategory = (cat: string) => {
    setSelectedCategories(prev =>
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
    );
  };

  const toggleSize = (size: string) => {
    setSelectedSizes(prev =>
      prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]
    );
  };

  const toggleColor = (color: string) => {
    setSelectedColors(prev =>
      prev.includes(color) ? prev.filter(c => c !== color) : [...prev, color]
    );
  };

  return (
    <div className="sticky top-[72px]">
      <div className="bg-white rounded-xl border border-gray-200 p-20">
        <div className="flex items-center justify-between mb-20">
          <h3 className="text-[16px] font-bold text-gray-900">Filters</h3>
          <button className="text-[13px] text-brand-600 hover:text-brand-700 font-medium">
            Clear All
          </button>
        </div>

        {/* Categories */}
        <div className="mb-24 pb-24 border-b border-gray-200">
          <h4 className="text-[14px] font-semibold text-gray-900 mb-12">Category</h4>
          <div className="space-y-8">
            {categories.map((cat) => (
              <label key={cat} className="flex items-center gap-8 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedCategories.includes(cat)}
                  onChange={() => toggleCategory(cat)}
                  className="w-16 h-16 rounded border-gray-300 text-brand-600 focus:ring-brand-600"
                />
                <span className="text-[14px] text-gray-700">{cat}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Price Range */}
        <div className="mb-24 pb-24 border-b border-gray-200">
          <h4 className="text-[14px] font-semibold text-gray-900 mb-12">Price Range</h4>
          <div className="space-y-12">
            <input
              type="range"
              min="0"
              max="1000"
              value={priceRange[1]}
              onChange={(e) => setPriceRange([0, parseInt(e.target.value)])}
              className="w-full accent-brand-600"
            />
            <div className="flex items-center justify-between text-[13px] text-gray-600">
              <span>${priceRange[0]}</span>
              <span>${priceRange[1]}</span>
            </div>
          </div>
        </div>

        {/* Sizes */}
        <div className="mb-24 pb-24 border-b border-gray-200">
          <h4 className="text-[14px] font-semibold text-gray-900 mb-12">Size</h4>
          <div className="flex flex-wrap gap-8">
            {sizes.map((size) => (
              <button
                key={size}
                onClick={() => toggleSize(size)}
                className={`w-40 h-40 rounded-lg border text-[13px] font-medium transition-all ${
                  selectedSizes.includes(size)
                    ? 'border-brand-600 bg-brand-50 text-brand-600'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-brand-600'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>

        {/* Colors */}
        <div className="mb-24 pb-24 border-b border-gray-200">
          <h4 className="text-[14px] font-semibold text-gray-900 mb-12">Color</h4>
          <div className="flex flex-wrap gap-12">
            {colors.map((color) => (
              <button
                key={color.name}
                onClick={() => toggleColor(color.name)}
                className={`w-32 h-32 rounded-full border-2 transition-all ${
                  selectedColors.includes(color.name)
                    ? 'border-brand-600 scale-110'
                    : 'border-gray-300 hover:border-brand-600'
                }`}
                style={{ backgroundColor: color.hex }}
                title={color.name}
              />
            ))}
          </div>
        </div>

        {/* Rating */}
        <div>
          <h4 className="text-[14px] font-semibold text-gray-900 mb-12">Rating</h4>
          <div className="space-y-8">
            {[4, 3, 2, 1].map((rating) => (
              <label key={rating} className="flex items-center gap-8 cursor-pointer">
                <input
                  type="radio"
                  name="rating"
                  checked={selectedRating === rating}
                  onChange={() => setSelectedRating(rating)}
                  className="w-16 h-16 text-brand-600 focus:ring-brand-600"
                />
                <div className="flex items-center gap-4">
                  {[...Array(5)].map((_, i) => (
                    <span
                      key={i}
                      className={`text-[14px] ${
                        i < rating ? 'text-rating' : 'text-gray-300'
                      }`}
                    >
                      ★
                    </span>
                  ))}
                  <span className="text-[13px] text-gray-600">& Up</span>
                </div>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
