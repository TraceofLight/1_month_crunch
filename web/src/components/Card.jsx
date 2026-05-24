import './Card.css';

export function Card({ as = 'div', padding = 'md', interactive = false, children, ...rest }) {
  const Tag = as;
  const cls = ['card', `card--${padding}`, interactive && 'card--interactive']
    .filter(Boolean)
    .join(' ');
  return (
    <Tag className={cls} {...rest}>
      {children}
    </Tag>
  );
}
