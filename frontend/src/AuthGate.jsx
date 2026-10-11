import { useEffect, useState } from 'react'
import App from './App.jsx'
import { ApiError, getCurrentUser, logout } from './api/auth'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
} from './auth/tokenStorage'
import LoginPage from './pages/LoginPage.jsx'

// Shows the login page or the dashboard, depending on whether the user is signed in.
function AuthGate() {
  const [user, setUser] = useState(null)
  const [isCheckingSession, setIsCheckingSession] = useState(
    Boolean(getAccessToken()),
  )

  // When the page loads, check if a saved session is still valid.
  useEffect(() => {
    const accessToken = getAccessToken()

    if (!accessToken) {
      return
    }

    getCurrentUser(accessToken)
      .then(setUser)
      .catch((error) => {
        // Only a 401 means the token is bad. A network error keeps the token.
        if (error instanceof ApiError && error.status === 401) {
          clearTokens()
        }
      })
      .finally(() => setIsCheckingSession(false))
  }, [])

  async function handleLogout() {
    const refreshToken = getRefreshToken()

    clearTokens()
    setUser(null)

    try {
      if (refreshToken) {
        await logout(refreshToken)
      }
    } catch {
      // The user is already signed out in the browser. Revoking the token
      // on the server is best effort, so a failure here is ignored.
    }
  }

  if (isCheckingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100">
        <p className="text-sm text-gray-500">Loading...</p>
      </div>
    )
  }

  if (!user) {
    return <LoginPage onLoginSuccess={setUser} />
  }

  return <App user={user} onLogout={handleLogout} />
}

export default AuthGate
