
import { useState } from 'react'

const navigation = [
  { label: 'Overview', icon: '◫', active: true },
  { label: 'Calls', icon: '◷', active: false },
]

const statistics = [
  {
    title: 'Total Calls',
    key: 'total_calls',
    description: 'Calls during selected period',
    icon: '↗',
    color: 'bg-violet-100 text-violet-700',
  },
  {
    title: 'Answered Calls',
    key: 'answered',
    description: 'Successfully answered calls',
    icon: '✓',
    color: 'bg-emerald-100 text-emerald-700',
  },
  {
    title: 'Active Calls',
    key: 'active_calls',
    description: 'Calls currently in progress',
    icon: '◉',
    color: 'bg-blue-100 text-blue-700',
  },
  {
    title: 'AI Resolution',
    key: 'containment',
    description: 'Calls resolved by AI',
    icon: '✳',
    color: 'bg-pink-100 text-pink-700',
  },
]

function App({ user, onLogout }) {
  const [period, setPeriod] = useState('today')

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 p-3 sm:p-5 lg:p-8">
      <div className="mx-auto flex min-h-[calc(100vh-24px)] max-w-[1600px] overflow-hidden rounded-2xl border border-white/70 bg-white shadow-xl shadow-purple-900/5 sm:min-h-[calc(100vh-40px)] lg:min-h-[calc(100vh-64px)]">
        <aside className="hidden w-60 shrink-0 flex-col border-r border-gray-100 bg-gray-50/90 p-5 md:flex">
          <div className="mb-10 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-purple-500 text-xl font-bold text-white shadow-md shadow-purple-200">
              V
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900">
                VoiceDesk
              </h1>
              <p className="mt-0.5 text-xs text-gray-500">
                AI Call Center
              </p>
            </div>
          </div>

          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-gray-400">
            Workspace
          </p>

          <nav className="space-y-1">
            {navigation.map((item) => (
              <button
                key={item.label}
                type="button"
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition ${
                  item.active
                    ? 'bg-violet-100 text-violet-700'
                    : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <span className="w-5 text-center text-lg">
                  {item.icon}
                </span>
                {item.label}
                {item.active && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-600" />
                )}
              </button>
            ))}
          </nav>

          <div className="mt-auto rounded-xl border border-purple-100 bg-gradient-to-br from-purple-50 to-blue-50 p-4">
            <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-white text-violet-600 shadow-sm">
              ✳
            </div>
            <p className="text-sm font-semibold text-gray-800">
              AI Call Center
            </p>
            <p className="mt-1 text-xs leading-5 text-gray-500">
              Monitor calls and service performance in one place.
            </p>
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-100 px-5 py-5 sm:px-8">
            <div>
              <p className="mb-1 text-xs text-gray-400">
                Workspace / Dashboard
              </p>
              <h2 className="text-xl font-bold tracking-tight text-gray-900 sm:text-2xl">
                Dashboard Overview
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Monitor your call center performance.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <label htmlFor="period" className="sr-only">
                Select reporting period
              </label>
              <select
                id="period"
                value={period}
                onChange={(event) => setPeriod(event.target.value)}
                className="rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-700 outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
              >
                <option value="today">Today</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
              </select>

              <button
                type="button"
                onClick={onLogout}
                className="rounded-xl border border-gray-200 px-3 py-2.5 text-sm font-medium text-gray-600 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"
              >
                Sign out
              </button>

              <div
                title={user.full_name}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 font-semibold text-violet-700"
              >
                {user.full_name.charAt(0).toUpperCase()}
              </div>
            </div>
          </header>

          <div className="space-y-7 p-5 sm:p-8">
            <section>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    Call Statistics
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    An overview of your call activity
                  </p>
                </div>
                <span className="rounded-lg bg-violet-50 px-3 py-1.5 text-xs font-medium text-violet-700">
                  {period === 'today'
                    ? 'Today'
                    : period === '7d'
                      ? 'Last 7 days'
                      : 'Last 30 days'}
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {statistics.map((stat) => (
                  <article
                    key={stat.key}
                    className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm shadow-gray-100/70 transition hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-medium text-gray-500">
                        {stat.title}
                      </p>
                      <span
                        className={`flex h-10 w-10 items-center justify-center rounded-xl text-lg font-semibold ${stat.color}`}
                      >
                        {stat.icon}
                      </span>
                    </div>
                    <p className="mt-5 text-3xl font-bold tracking-tight text-gray-900">
                      —
                    </p>
                    <p className="mt-2 text-xs text-gray-400">
                      {stat.description}
                    </p>
                  </article>
                ))}
              </div>
            </section>

            <section className="grid grid-cols-1 gap-5 xl:grid-cols-2">
              <article className="rounded-2xl border border-gray-100 bg-white p-5 sm:p-6">
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900">
                    Service Level
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Calls answered within the target time
                  </p>
                </div>

                <div className="flex items-center gap-5">
                  <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-full border-[8px] border-violet-100">
                    <span className="text-xl font-bold text-gray-400">
                      —
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      SLA achievement
                    </p>
                    <p className="mt-2 text-xs leading-5 text-gray-400">
                      Service-level results will appear here when the
                      dashboard API is connected.
                    </p>
                  </div>
                </div>
              </article>

              <article className="rounded-2xl border border-gray-100 bg-white p-5 sm:p-6">
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900">
                    Wait Time
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Waiting time across incoming calls
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl bg-purple-50 p-4">
                    <p className="text-sm text-gray-500">
                      Average wait
                    </p>
                    <p className="mt-3 text-2xl font-bold text-violet-700">
                      —
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      Seconds
                    </p>
                  </div>
                  <div className="rounded-xl bg-blue-50 p-4">
                    <p className="text-sm text-gray-500">
                      95th percentile
                    </p>
                    <p className="mt-3 text-2xl font-bold text-blue-700">
                      —
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      Seconds
                    </p>
                  </div>
                </div>
              </article>
            </section>

            <section className="overflow-hidden rounded-2xl border border-gray-100 bg-white">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 p-5 sm:px-6">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    Recent Calls
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Review call activity and outcomes
                  </p>
                </div>
                <button
                  type="button"
                  className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 transition hover:border-violet-200 hover:bg-violet-50 hover:text-violet-700"
                >
                  View all calls
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <thead className="bg-gray-50/80 text-xs uppercase tracking-wider text-gray-400">
                    <tr>
                      <th className="px-6 py-4 font-medium">Caller</th>
                      <th className="px-6 py-4 font-medium">Direction</th>
                      <th className="px-6 py-4 font-medium">Start time</th>
                      <th className="px-6 py-4 font-medium">Duration</th>
                      <th className="px-6 py-4 font-medium">Status</th>
                      <th className="px-6 py-4 font-medium">AI resolved</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td
                        colSpan={6}
                        className="px-6 py-12 text-center"
                      >
                        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-xl text-violet-500">
                          ◷
                        </div>
                        <p className="font-medium text-gray-700">
                          Call data is not connected yet
                        </p>
                        <p className="mt-1 text-sm text-gray-400">
                          Real call records will appear here after API integration.
                        </p>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <footer className="pb-2 text-center text-xs text-gray-400">
              AI VoIP Agent · Call Center Dashboard
            </footer>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
