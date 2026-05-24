import { Select } from './Select.jsx';
import { Input } from './Input.jsx';
import { CATEGORIES } from '../lib/supabase.js';
import './FilterBar.css';

export function FilterBar({ category, onCategoryChange, search, onSearchChange }) {
  const options = [
    { value: 'all', label: '전체 카테고리' },
    ...CATEGORIES.map((c) => ({ value: c, label: c })),
  ];
  return (
    <div className="filter-bar">
      <div className="filter-bar__search">
        <Input
          name="search"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="제목 또는 저자로 검색"
        />
      </div>
      <div className="filter-bar__category">
        <Select
          name="category"
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          options={options}
        />
      </div>
    </div>
  );
}
