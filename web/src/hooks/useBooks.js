import { useCallback, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase.js';
import { useAuth } from '../contexts/AuthContext.jsx';

export function useBooks({ category = 'all', search = '' } = {}) {
  const { user } = useAuth();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBooks = useCallback(async () => {
    if (!user) {
      setData([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    let query = supabase
      .from('books')
      .select('id, title, author, category, rating, finished_on, created_at')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (category && category !== 'all') {
      query = query.eq('category', category);
    }
    if (search?.trim()) {
      const term = `%${search.trim()}%`;
      query = query.or(`title.ilike.${term},author.ilike.${term}`);
    }

    const { data: rows, error: err } = await query;
    if (err) {
      setError(err);
      setData([]);
    } else {
      setData(rows ?? []);
    }
    setLoading(false);
  }, [user, category, search]);

  useEffect(() => {
    fetchBooks();
  }, [fetchBooks]);

  const remove = useCallback(
    async (id) => {
      const { error: err } = await supabase.from('books').delete().eq('id', id);
      if (err) throw err;
      setData((prev) => prev.filter((b) => b.id !== id));
    },
    [],
  );

  return { data, loading, error, refresh: fetchBooks, remove };
}
