import { useState } from 'react';
import { Input } from './Input.jsx';
import { Textarea } from './Textarea.jsx';
import { Select } from './Select.jsx';
import { Rating } from './Rating.jsx';
import { Button } from './Button.jsx';
import { CATEGORIES } from '../lib/supabase.js';

function validate(values) {
  const errors = {};
  if (!values.title?.trim()) errors.title = '제목을 입력해 주세요.';
  if (!values.author?.trim()) errors.author = '저자를 입력해 주세요.';
  if (values.rating < 0 || values.rating > 5) errors.rating = '0 ~ 5 사이로 입력해 주세요.';
  return errors;
}

export function BookForm({ initialValue, onSubmit, onCancel, submitLabel = '저장' }) {
  const [values, setValues] = useState(() => ({
    title: '',
    author: '',
    category: '기타',
    rating: 0,
    memo: '',
    finished_on: '',
    ...initialValue,
  }));
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const set = (name) => (e) => {
    const v = e.target.value;
    setValues((prev) => ({ ...prev, [name]: v }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const v = validate(values);
    setErrors(v);
    if (Object.keys(v).length > 0) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit({
        ...values,
        title: values.title.trim(),
        author: values.author.trim(),
        memo: values.memo?.trim() ?? '',
        finished_on: values.finished_on || null,
        rating: Number(values.rating) || 0,
      });
    } catch (err) {
      setSubmitError(err.message || '저장에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  const categoryOptions = CATEGORIES.map((c) => ({ value: c, label: c }));

  return (
    <form onSubmit={handleSubmit} className="form-grid" noValidate>
      {submitError ? <div className="banner">{submitError}</div> : null}
      <Input
        label="제목"
        name="title"
        value={values.title}
        onChange={set('title')}
        error={errors.title}
        required
      />
      <Input
        label="저자"
        name="author"
        value={values.author}
        onChange={set('author')}
        error={errors.author}
        required
      />
      <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Select
          label="카테고리"
          name="category"
          value={values.category}
          onChange={set('category')}
          options={categoryOptions}
        />
        <Input
          label="다 읽은 날"
          name="finished_on"
          type="date"
          value={values.finished_on || ''}
          onChange={set('finished_on')}
        />
      </div>
      <div className="field">
        <label>별점</label>
        <Rating value={Number(values.rating) || 0} onChange={(v) => setValues((p) => ({ ...p, rating: v }))} />
        {errors.rating ? <span className="error">{errors.rating}</span> : null}
      </div>
      <Textarea
        label="메모"
        name="memo"
        value={values.memo}
        onChange={set('memo')}
        help="인상 깊었던 문장이나 한줄평을 적어 두면 좋다."
      />
      <div className="row" style={{ marginTop: 8 }}>
        <Button type="submit" loading={submitting} disabled={submitting}>
          {submitLabel}
        </Button>
        {onCancel ? (
          <Button type="button" variant="ghost" onClick={onCancel} disabled={submitting}>
            취소
          </Button>
        ) : null}
      </div>
    </form>
  );
}
