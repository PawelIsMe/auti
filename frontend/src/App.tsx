import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AppShell, AccessDenied } from './components/AppShell'
import { Spinner } from './components/UI'
import { AdminView } from './views/Admin'
import { ChatView } from './views/Chat'
import { LoginView, RegisterView } from './views/Auth'
import { OnboardingView } from './views/Onboarding'
import { ProfileView } from './views/Profile'
import './App.css'
import './monochrome.css'

function RoutesView() {
  const { user, loading, initialized } = useAuth()
  if (loading) return <div className="full-loading"><Spinner label="Uruchamiam Auti"/></div>
  const privateView = (element: React.ReactNode) => user ? element : <Navigate to="/login" replace/>
  return <Routes>
    <Route path="/login" element={user ? <Navigate to="/chat" replace/> : <LoginView/>}/>
    <Route path="/register" element={user ? <Navigate to="/chat" replace/> : <RegisterView/>}/>
    <Route path="/onboarding" element={initialized === false && !user ? <OnboardingView/> : user ? <Navigate to="/chat" replace/> : <Navigate to="/login" replace/>}/>
    <Route element={privateView(<AppShell/>) }>
      <Route path="/chat" element={<ChatView/>}/>
      <Route path="/profile" element={<ProfileView/>}/>
      <Route path="/admin" element={user?.role === 'admin' ? <AdminView currentUser={user}/> : <AccessDenied/>}/>
    </Route>
    <Route path="*" element={<Navigate to={user ? '/chat' : initialized === false ? '/onboarding' : '/login'} replace/>}/>
  </Routes>
}

export default function App() {
  return <AuthProvider><BrowserRouter><RoutesView/></BrowserRouter></AuthProvider>
}
