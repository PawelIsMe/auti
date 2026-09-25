import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Brand, Button, Input, Notice, PasswordInput } from '../components/UI'

export function LoginView() {
  const { signIn, initialized } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(''); setBusy(true)
    try { await signIn(username, password, remember); navigate('/chat') }
    catch (err) { setError(err instanceof ApiError ? err.message : 'Nie udało się zalogować.') }
    finally { setBusy(false) }
  }
  return <div className="auth-shell"><div className="auth-aside"><Brand /><div className="aside-copy"><span className="eyebrow">TWÓJ DOM, W DOBRYCH RĘKACH</span><h1>Inteligentny dom.<br/><em>Prościej.</em></h1><p>Rozmawiaj z Auti i zarządzaj swoim domem z jednego, spokojnego miejsca.</p><div className="orbit-art"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><span className="orbit-center">a</span><i>✳</i><b>⌂</b><small>✦</small></div></div><div className="aside-foot">AUTI HOME ASSISTANT <span>•</span> ZAWSZE POD RĘKĄ</div></div>
    <main className="auth-main"><div className="auth-card"><span className="eyebrow">WITAJ PONOWNIE</span><h2>Zaloguj się</h2><p className="muted">Zaloguj się, aby wrócić do swojego domu.</p>{error && <Notice>{error}</Notice>}
      {initialized === false && <Notice tone="success">To pierwsze uruchomienie. Utwórz konto administratora, aby skonfigurować Auti. <Link to="/onboarding">Rozpocznij konfigurację</Link></Notice>}
      <form onSubmit={submit}><Input label="Login" autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} required minLength={2} placeholder="Wpisz swój login"/><PasswordInput label="Hasło" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} placeholder="Wpisz swoje hasło"/><label className="check-row"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)}/><span>Pozostań zalogowany</span></label><Button type="submit" disabled={busy}>{busy ? 'Logowanie…' : 'Zaloguj się'}<span>→</span></Button></form>
      <div className="auth-divider"><span/></div><p className="auth-bottom">Masz kod zaproszenia? <Link to="/register">Utwórz konto</Link></p></div><footer className="auth-legal">Bezpieczny dostęp do Twojego inteligentnego domu <span>•</span> Auti © 2026</footer></main></div>
}

export function RegisterView() {
  const { signUp } = useAuth(); const navigate = useNavigate()
  const [data, setData] = useState({ invite_code: '', preferred_name: '', date_of_birth: '', username: '', password: '', gemini_api_key: '', info_for_ai: '' })
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const change = (key: keyof typeof data) => (value: string) => setData((old) => ({ ...old, [key]: value }))
  async function submit(e: FormEvent) { e.preventDefault(); setError(''); setBusy(true); try { await signUp({ ...data, gemini_api_key: data.gemini_api_key || null, info_for_ai: data.info_for_ai || null }); navigate('/chat') } catch (err) { setError(err instanceof Error ? err.message : 'Nie udało się utworzyć konta.') } finally { setBusy(false) } }
  return <div className="auth-shell"><div className="auth-aside"><Brand/><div className="aside-copy"><span className="eyebrow">RAZEM LEPIEJ</span><h1>Dom, który<br/><em>rozumie.</em></h1><p>Dołącz do swojego Auti i spraw, żeby codzienność działała trochę płynniej.</p><div className="orbit-art"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><span className="orbit-center">A</span><i>✳</i><b>⌂</b><small>✦</small></div></div><div className="aside-foot">AUTI HOME ASSISTANT <span>•</span> ZAWSZE POD RĘKĄ</div></div><main className="auth-main"><div className="auth-card register-card"><span className="eyebrow">TWOJE KONTO</span><h2>Dołącz do Auti</h2><p className="muted">Załóż konto przy użyciu kodu zaproszenia.</p>{error && <Notice>{error}</Notice>}<form onSubmit={submit}><Input label="Kod zaproszenia" value={data.invite_code} onChange={(e)=>change('invite_code')(e.target.value)} required/><Input label="Preferowane imię" value={data.preferred_name} onChange={(e)=>change('preferred_name')(e.target.value)} required placeholder="Twoje imię"/><Input label="Data urodzenia" type="date" value={data.date_of_birth} onChange={(e)=>change('date_of_birth')(e.target.value)} required/><Input label="Nazwa użytkownika" value={data.username} onChange={(e)=>change('username')(e.target.value)} required minLength={2}/><PasswordInput label="Hasło" value={data.password} onChange={(e)=>change('password')(e.target.value)} required minLength={6}/><PasswordInput label="Klucz Gemini API (opcjonalnie)" value={data.gemini_api_key} onChange={(e)=>change('gemini_api_key')(e.target.value)} placeholder="Możesz dodać go później"/><label className="field"><span>Informacje dla AI (opcjonalnie)</span><textarea rows={3} value={data.info_for_ai} onChange={(e)=>change('info_for_ai')(e.target.value)} placeholder="Preferencje lub kontekst dla asystenta"/></label><Button type="submit" disabled={busy}>{busy ? 'Tworzenie konta…' : 'Utwórz konto'}<span>→</span></Button></form><p className="auth-bottom">Masz już konto? <Link to="/login">Zaloguj się</Link></p></div></main></div>
}
