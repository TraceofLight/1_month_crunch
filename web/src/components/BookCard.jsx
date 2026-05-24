import { memo } from 'react';
import { Link } from 'react-router-dom';
import { Card } from './Card.jsx';
import { Badge } from './Badge.jsx';
import { Rating } from './Rating.jsx';
import './BookCard.css';

function BookCardImpl({ book }) {
  return (
    <Link to={`/books/${book.id}`} className="book-card-link">
      <Card padding="md" interactive>
        <div className="book-card">
          <div className="book-card__head">
            <h3 className="book-card__title">{book.title}</h3>
            <Badge tone="accent">{book.category}</Badge>
          </div>
          <p className="book-card__author">{book.author}</p>
          <Rating value={book.rating} readOnly />
        </div>
      </Card>
    </Link>
  );
}

// 목록이 자주 갱신될 때 같은 책 카드는 리렌더되지 않도록 메모이제이션한다.
export const BookCard = memo(BookCardImpl, (prev, next) => {
  const a = prev.book;
  const b = next.book;
  return (
    a.id === b.id &&
    a.title === b.title &&
    a.author === b.author &&
    a.category === b.category &&
    a.rating === b.rating
  );
});
