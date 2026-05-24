import { useCallback, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase.js';

export function useBook(id) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(id));
  const [error, setError] = useState(null);

  const fetchBook = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    const { data: row, error: err } = await supabase
      .from('books')
      .select('*')
      .eq('id', id)
      .maybeSingle();
    if (err) {
      setError(err);
      setData(null);
    } else {
      setData(row);
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    fetchBook();
  }, [fetchBook]);

  return { data, loading, error, refresh: fetchBook };
}
