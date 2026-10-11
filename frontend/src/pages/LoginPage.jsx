import { useState } from 'react'
import { ApiError, getCurrentUser, login } from '../api/auth'
import { saveTokens } from '../auth/tokenStorage'

const inputClassName =
  'h-11 w-full rounded-xl border border-gray-200 bg-white px-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-400 focus:border-violet-400 focus:ring-2 focus:ring-violet-200'

function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    if (isSubmitting) {
      return
    }

    if (!username.trim() || !password) {
      setErrorMessage('Please enter your username and password.')
      return
    }

    setErrorMessage('')
    setIsSubmitting(true)

    try {
      const tokens = await login(username.trim(), password)
      const user = await getCurrentUser(tokens.access_token)

      // Save only after both requests succeeded, so we never keep
      // tokens for a user we could not load.
      saveTokens(tokens)
      onLoginSuccess(user)
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message)
      } else {
        setErrorMessage('Something went wrong. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 p-4">
      <div className="w-full max-w-md rounded-2xl border border-white/70 bg-white p-6 shadow-xl shadow-purple-900/5 sm:p-8">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-purple-500 text-xl font-bold text-white shadow-md shadow-purple-200">
            V
          </div>
          <div>
            <p className="text-sm font-bold text-gray-900">VoiceDesk</p>
            <p className="mt-0.5 text-xs text-gray-500">AI Call Center</p>
          </div>
        </div>

        <h1 className="text-xl font-bold tracking-tight text-gray-900 sm:text-2xl">
          Welcome back
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Sign in to access your dashboard.
        </p>

        <form onSubmit={handleSubmit} noValidate className="mt-6 space-y-5">
          {errorMessage && (
            <div
              id="login-error"
              role="alert"
              className="rounded-xl border border-red-100 bg-red-50 px-3 py-2.5 text-sm text-red-700"
            >
              {errorMessage}
            </div>
          )}

          <div>
            <label
              htmlFor="username"
              className="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              placeholder="Enter your username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              aria-describedby={errorMessage ? 'login-error' : undefined}
              className={inputClassName}
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-describedby={errorMessage ? 'login-error' : undefined}
                className={`${inputClassName} pr-16`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute inset-y-0 right-0 rounded-r-xl px-3 text-xs font-medium text-gray-500 transition hover:text-violet-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300"
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="h-11 w-full rounded-xl bg-violet-600 text-sm font-semibold text-white transition hover:bg-violet-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default LoginPage
