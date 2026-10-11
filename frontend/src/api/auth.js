const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// An error whose message is safe to show to the user.
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function sendRequest(path, options) {
  if (!API_BASE_URL) {
    throw new ApiError('The server address is not configured.')
  }

  try {
    return await fetch(`${API_BASE_URL}${path}`, options)
  } catch {
    throw new ApiError('Cannot reach the server. Please try again.')
  }
}

async function readJson(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function createUnexpectedResponseError(status) {
  if (status >= 500) {
    return new ApiError(
      'The server ran into a problem. Please try again later.',
      status,
    )
  }

  return new ApiError('Unexpected response from the server.', status)
}

// POST /api/v1/auth/login -> { access_token, refresh_token, token_type, expires_in }
export async function login(username, password) {
  const response = await sendRequest('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await readJson(response)

  if (response.status === 401 || response.status === 403) {
    // The backend sends short, user-facing messages here, for example
    // "Invalid credentials" or "Too many login attempts".
    throw new ApiError(
      data?.message || 'Invalid username or password.',
      response.status,
    )
  }

  if (response.status === 422) {
    throw new ApiError(
      'Please check your details. The password must be at least 8 characters.',
      response.status,
    )
  }

  if (!response.ok || !data?.access_token || !data?.refresh_token) {
    throw createUnexpectedResponseError(response.status)
  }

  return data
}

// GET /api/v1/auth/me -> the current user (id, username, full_name, tenant_id, ...)
export async function getCurrentUser(accessToken) {
  const response = await sendRequest('/api/v1/auth/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })

  if (response.status === 401) {
    throw new ApiError('Your session has expired. Please sign in again.', 401)
  }

  const user = await readJson(response)

  if (!response.ok || !user?.id) {
    throw createUnexpectedResponseError(response.status)
  }

  return user
}

// POST /api/v1/auth/logout -> 204. The backend revokes the refresh token.
export async function logout(refreshToken) {
  await sendRequest('/api/v1/auth/logout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
}
