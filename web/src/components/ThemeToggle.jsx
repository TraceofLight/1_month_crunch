import { useTheme } from '../contexts/ThemeContext.jsx';
import { Button } from './Button.jsx';

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return (
    <Button variant="ghost" size="sm" onClick={toggle} aria-label="테마 전환">
      {theme === 'dark' ? '☀︎ 라이트' : '☾ 다크'}
    </Button>
  );
}
