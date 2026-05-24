import { Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout.jsx';
import { ProtectedRoute } from './components/ProtectedRoute.jsx';
import { HomePage } from './pages/HomePage.jsx';
import { LoginPage } from './pages/LoginPage.jsx';
import { BooksPage } from './pages/BooksPage.jsx';
import { BookDetailPage } from './pages/BookDetailPage.jsx';
import { BookFormPage } from './pages/BookFormPage.jsx';
import { ProfilePage } from './pages/ProfilePage.jsx';
import { NotFoundPage } from './pages/NotFoundPage.jsx';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/books" element={<BooksPage />} />
        <Route path="/books/new" element={<ProtectedRoute><BookFormPage mode="new" /></ProtectedRoute>} />
        <Route path="/books/:id" element={<BookDetailPage />} />
        <Route path="/books/:id/edit" element={<ProtectedRoute><BookFormPage mode="edit" /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
