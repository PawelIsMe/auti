import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Brand, Icon } from './UI'
import { useAuth } from '../context/AuthContext'
import type { ReactNode } from 'react'

export function AppShell({ children }: { children?: ReactNode }) {
  const { user, signOut } = useAuth()
  const location = useLocation()
  const title = location.pathname === '/chat' ? 'Czat' : location.pathname === '/profile' ? 'Profil' : 'Administracja'
  return <div className="app-shell">
    <aside className="sidebar">
      <Brand/>
      <div className="workspace-label">MENU</div>
      <nav className="side-nav">
        <NavLink to="/chat" className={({isActive})=>`nav-link ${isActive?'selected':''}`}><Icon name="chat"/><span>Czat</span></NavLink>
        {user?.role === 'admin' && <NavLink to="/admin" className={({isActive})=>`nav-link ${isActive?'selected':''}`}><Icon name="admin"/><span>Administracja</span></NavLink>}
      </nav>
      <div className="sidebar-bottom">
        <Link className="profile-link" to="/profile"><span className="user-avatar-small">{user?.preferred_name.slice(0,1).toUpperCase()}</span><span className="user-menu-name"><b>{user?.preferred_name}</b><small>Profil</small></span><Icon name="profile"/></Link>
        <button className="logout-button" onClick={()=>void signOut()}><Icon name="logout"/><span>Wyloguj się</span></button>
      </div>
    </aside>
    <div className="main-column">
      <header className="topbar"><h1 className="section-title">{title}</h1></header>
      <main className="workspace">{children ?? <Outlet/>}</main>
      <nav className="mobile-nav">
        <NavLink to="/chat"><Icon name="chat"/><span>Czat</span></NavLink>
        <NavLink to="/profile"><Icon name="profile"/><span>Profil</span></NavLink>
        {user?.role === 'admin' && <NavLink to="/admin"><Icon name="admin"/><span>Admin</span></NavLink>}
        <button onClick={()=>void signOut()}><Icon name="logout"/><span>Wyloguj</span></button>
      </nav>
    </div>
  </div>
}

export function AccessDenied() {
  return <div className="access-denied"><h2>Brak dostępu</h2><Link className="button button-primary" to="/chat">Wróć do czatu</Link></div>
}
