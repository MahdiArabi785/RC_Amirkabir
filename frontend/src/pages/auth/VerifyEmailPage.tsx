// src/pages/Auth/VerifyEmailPage.tsx
import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { authService } from '../../services/auth';
import { getApiErrorMessage } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshProfile } = useAuth();
  const emailFromQuery = searchParams.get('email') || '';

  const [email, setEmail] = useState(emailFromQuery);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);

  useEffect(() => {
    if (!emailFromQuery) {
      setError('ایمیل مشخص نیست. لطفاً دوباره ثبت‌نام کنید.');
    }
  }, [emailFromQuery]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setSubmitting(true);
    try {
      await authService.verifyEmail(email, code);
      await refreshProfile();
      navigate('/', { replace: true });
    } catch (err) {
      setError(getApiErrorMessage(err, 'تأیید ایمیل ناموفق بود'));
    } finally {
      setSubmitting(false);
    }
  }

  async function onResend() {
    setError(null);
    setInfo(null);
    setResending(true);
    try {
      await authService.resendCode(email);
      setInfo('کد جدید ارسال شد. صندوق ایمیل خود را بررسی کنید.');
    } catch (err) {
      setError(getApiErrorMessage(err, 'ارسال مجدد ناموفق بود'));
    } finally {
      setResending(false);
    }
  }

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow-sm border-0">
            <div className="card-body p-4">
              <h1 className="h4 mb-1 text-center">تأیید ایمیل</h1>
              <p className="text-muted text-center mb-4">
                کد ۶ رقمی ارسال‌شده به <strong dir="ltr">{email}</strong> را وارد کنید.
              </p>

              {error && (
                <div className="alert alert-danger py-2 small" role="alert">
                  {error}
                </div>
              )}
              {info && (
                <div className="alert alert-success py-2 small" role="alert">
                  {info}
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
                  />
                </div>

                <div className="mb-3">
                  <label htmlFor="code" className="form-label">کد تأیید</label>
                  <input
                    id="code"
                    type="text"
                    className="form-control text-center"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    required
                    dir="ltr"
                    maxLength={6}
                    placeholder="123456"
                    style={{ fontSize: '1.5rem', letterSpacing: '0.5rem' }}
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary w-100"
                  disabled={submitting || code.length !== 6}
                >
                  {submitting ? 'در حال تأیید...' : 'تأیید ایمیل'}
                </button>
              </form>

              <div className="d-flex justify-content-between align-items-center mt-3 small">
                <button
                  type="button"
                  className="btn btn-link p-0"
                  onClick={onResend}
                  disabled={resending}
                >
                  {resending ? 'در حال ارسال...' : 'ارسال مجدد کد'}
                </button>
                <Link to="/login">بازگشت به ورود</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}