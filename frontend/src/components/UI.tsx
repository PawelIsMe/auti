import { useState, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import appLogo from '../assets/app_logo.png'

export function Button({ children, variant = 'primary', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' | 'danger' }) {
  return <button className={`button button-${variant} ${props.className ?? ''}`} {...props}>{children}</button>
}

export function Input({ label, hint, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string }) {
  if (props.type === 'password') return <PasswordInput label={label} hint={hint} {...props} />
  return <label className="field"><span>{label}</span><input {...props} />{hint && <small>{hint}</small>}</label>
}

export function PasswordInput({ label, hint, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string }) {
  const [visible, setVisible] = useState(false)
  return <label className="field"><span>{label}</span><span className="password-control"><input {...props} type={visible ? 'text' : 'password'} /><button type="button" className="password-toggle" onClick={() => setVisible((value) => !value)} aria-label={visible ? 'Ukryj hasło' : 'Pokaż hasło'} title={visible ? 'Ukryj hasło' : 'Pokaż hasło'}>{visible ? '◉' : '◎'}</button></span>{hint && <small>{hint}</small>}</label>
}

export function Notice({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'success' }) {
  return <div className={`notice notice-${tone}`} role="status">{children}</div>
}

export function Brand({ compact = false }: { compact?: boolean }) {
  return <Link to="/chat" className={`brand ${compact ? 'brand-compact' : ''}`} aria-label="Auti — strona główna"><img src={appLogo} alt=""/><span>Auti</span></Link>
}

export function Icon({ name }: { name: 'chat' | 'profile' | 'admin' | 'logout' }) {
  const paths = {
    chat: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-5.5A7.5 7.5 0 1 1 20 11.5Z"/><path d="M8 11h.01M12 11h.01M16 11h.01"/></>,
    profile: <><circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/></>,
    admin: <><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16M10 4v16"/></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/></>,
  }
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

export function Spinner({ label = 'Ładowanie' }: { label?: string }) {
  return <div className="loading"><span className="spinner" />{label}</div>
}
