// src/pages/Auth/RegisterPage.tsx
import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../../services/auth';
import { getApiErrorMessage } from '../../services/api';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError('رمز عبور باید حداقل ۸ کاراکتر باشد.');
      return;
    }
    if (password !== password2) {
      setError('رمز عبور و تکرار آن مطابقت ندارند.');
      return;
    }

    setSubmitting(true);
    try {
      await authService.signup({
        email: email.trim().toLowerCase(),
        phone: phone.trim() || null,
        password,
      });
      navigate(`/verify-email?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'ثبت‌نام ناموفق بود'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-sm border-0">
            <div className="card-body p-4">
              <h1 className="h4 mb-1 text-center">ثبت‌نام</h1>
              <p className="text-muted text-center mb-4">
                پس از ثبت‌نام، ایمیل تأیید برایتان ارسال می‌شود
              </p>

              {error && (
                <div className="alert alert-danger py-2 small" role="alert">
                  {error}
                </div>
              )}

              <form onSubmit={onSubmit} noValidate>
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">ایمیل</label>
                  <input
                    id="email"
                    type="email"
                    className="form-control"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    dir="ltr"
                    autoComplete="email"
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="phone" className="form-label">
                    شماره موبایل <span className="text-muted small">(اختیاری)</span>
                  </label>
                  <input
                    id="phone"
                    type="tel"
                    className="form-control"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    dir="ltr"
                    placeholder="09..."
                    autoComplete="tel"
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="password" className="form-label">رمز عبور</label>
                  <input
                    id="password"
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    dir="ltr"
                    autoComplete="new-password"
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="password2" className="form-label">تکرار رمز عبور</label>
                  <input
                    id="password2"
                    type="password"
                    className="form-control"
                    value={password2}
                    onChange={(e) => setPassword2(e.target.value)}
                    required
                    dir="ltr"
                    autoComplete="new-password"
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary w-100"
                  disabled={submitting}
                >
                  {submitting ? 'در حال ثبت‌نام...' : 'ثبت‌نام'}
                </button>
              </form>

              <div className="text-center mt-3 small">
                <Link to="/login">حساب دارید؟ وارد شوید</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}