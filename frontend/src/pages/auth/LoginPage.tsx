// src/pages/Auth/LoginPage.tsx
import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { getApiErrorMessage } from '../../services/api';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string })?.from || '/';

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({ identifier: identifier.trim(), password });
      navigate(from, { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, 'ورود ناموفق بود'));
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
              <h1 className="h4 mb-1 text-center">ورود به حساب</h1>
              <p className="text-muted text-center mb-4">
                با ایمیل یا شماره موبایل وارد شوید
              </p>

              {error && (
                <div className="alert alert-danger py-2 small" role="alert">
                  {error}
                </div>
              )}

              <form onSubmit={onSubmit} noValidate>
                <div className="mb-3">
                  <label htmlFor="identifier" className="form-label">
                    ایمیل یا موبایل
                  </label>
                  <input
                    id="identifier"
                    type="text"
                    className="form-control"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    required
                    autoComplete="username"
                    dir="ltr"
                    placeholder="you@example.com یا 0912..."
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="password" className="form-label">
                    رمز عبور
                  </label>
                  <input
                    id="password"
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    dir="ltr"
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary w-100"
                  disabled={submitting}
                >
                  {submitting ? 'در حال ورود...' : 'ورود'}
                </button>
              </form>

              <div className="text-center mt-3 small">
                <Link to="/register">حساب ندارید؟ ثبت‌نام کنید</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}