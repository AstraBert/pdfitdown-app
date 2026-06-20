import { createFileRoute } from '@tanstack/react-router'
import { useAuth } from '@workos-inc/authkit-react'
import { usePostHog } from '@posthog/react'
import { useCallback, useRef, useState } from 'react'

export const Route = createFileRoute('/')({ component: App })

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9999'

function App() {
  const { user, isLoading: authLoading, signIn, getAccessToken } = useAuth()
  const posthog = usePostHog()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const [converting, setConverting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const track = useCallback(
    (event: string, props?: Record<string, unknown>) => {
      posthog.capture(event, props)
    },
    [posthog],
  )

  const handleFile = (f: File | null) => {
    if (!f) return
    if (f.type === 'application/pdf') {
      setError('Please upload a non-PDF file.')
      setFile(null)
      track('file_rejected', { reason: 'pdf_not_allowed', fileType: f.type })
      return
    }
    setFile(f)
    setError(null)
    track('file_selected', {
      fileType: f.type,
      fileSize: f.size,
      fileName: f.name,
    })
  }

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }
  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    handleFile(e.dataTransfer.files[0])
  }

  const onConvert = async () => {
    if (!file || !user) return
    setConverting(true)
    setError(null)
    track('conversion_started', { fileType: file.type, fileSize: file.size })

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('file_name', file.name)
      if (title.trim()) formData.append('title', title.trim())

      const token = await getAccessToken()
      const res = await fetch(`${API_BASE}/conversions`, {
        method: 'POST',
        body: formData,
        headers: {
          Authorization: `Bearer ${token}`,
          'x-user-id': user.id,
        },
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Error ${res.status}`)
      }

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const disposition = res.headers.get('content-disposition')
      const match = disposition?.match(/filename=([^;]+)/)
      a.download = match
        ? match[1].trim()
        : file.name.replace(/\.[^/.]+$/, '') + '.pdf'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)

      track('conversion_succeeded', {
        fileType: file.type,
        fileSize: file.size,
      })
      setFile(null)
      setTitle('')
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err: any) {
      setError(err.message || 'Something went wrong.')
      track('conversion_failed', { error: err.message || 'unknown' })
    } finally {
      setConverting(false)
    }
  }

  return (
    <main className="page-wrap px-4 pb-8 pt-14">
      <section className="island-shell rise-in relative overflow-hidden rounded-[2rem] px-6 py-10 sm:px-10 sm:py-14">
        <div className="pointer-events-none absolute -left-20 -top-24 h-56 w-56 rounded-full bg-[radial-gradient(circle,rgba(201,106,66,0.28),transparent_66%)]" />
        <div className="pointer-events-none absolute -bottom-20 -right-20 h-56 w-56 rounded-full bg-[radial-gradient(circle,rgba(150,66,40,0.16),transparent_66%)]" />
        <p className="island-kicker mb-3">PDFItDown</p>
        <h1 className="display-title mb-5 max-w-3xl text-4xl leading-[1.02] font-bold tracking-tight text-[var(--sea-ink)] sm:text-6xl">
          Convert anything to PDF.
        </h1>
        <p className="mb-8 max-w-2xl text-base text-[var(--sea-ink-soft)] sm:text-lg">
          Drop your documents, images, or presentations and get a clean PDF back
          in seconds.
        </p>

        {!user && !authLoading && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-[var(--chip-line)] bg-[var(--chip-bg)] px-4 py-3">
            <p className="m-0 text-sm text-[var(--sea-ink-soft)]">
              Sign in to start converting files.
            </p>
            <button
              onClick={() => signIn()}
              className="ml-auto rounded-full bg-[var(--lagoon)] px-4 py-2 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5 hover:bg-[var(--lagoon-deep)]"
            >
              Sign In
            </button>
          </div>
        )}

        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-2xl border-2 border-dashed px-6 py-10 text-center transition ${
            dragActive
              ? 'border-[var(--lagoon)] bg-[rgba(201,106,66,0.06)]'
              : 'border-[var(--line)] bg-[var(--surface-strong)] hover:border-[var(--lagoon-deep)]'
          } ${!user ? 'pointer-events-none opacity-50' : ''}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] || null)}
          />
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-[rgba(201,106,66,0.12)] text-[var(--lagoon)]">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <p className="m-0 text-sm font-medium text-[var(--sea-ink)]">
            {file ? file.name : 'Click or drag a file here'}
          </p>
          <p className="m-0 mt-1 text-xs text-[var(--sea-ink-soft)]">
            {file
              ? `${(file.size / 1024 / 1024).toFixed(2)} MB`
              : 'Max 25 MB. No PDFs.'}
          </p>
        </div>

        {file && (
          <div className="mt-4 space-y-3">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--sea-ink-soft)]">
                PDF Title (optional)
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="My Document"
                className="w-full rounded-xl border border-[var(--line)] bg-[var(--surface-strong)] px-4 py-2.5 text-sm text-[var(--sea-ink)] outline-none transition focus:border-[var(--lagoon)] focus:ring-2 focus:ring-[rgba(201,106,66,0.15)]"
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              onClick={onConvert}
              disabled={converting}
              className="w-full rounded-full bg-[var(--lagoon)] px-5 py-3 text-sm font-semibold text-white shadow transition hover:-translate-y-0.5 hover:bg-[var(--lagoon-deep)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {converting ? 'Converting…' : 'Convert to PDF'}
            </button>
          </div>
        )}
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        {[
          ['Any Format', 'Word, PowerPoint, images, HTML, and more.'],
          ['Fast & Secure', 'Files are processed in-memory and never stored.'],
          ['High Fidelity', 'Preserves fonts, layouts, and styling.'],
        ].map(([t, d], i) => (
          <article
            key={t}
            className="island-shell feature-card rise-in rounded-2xl p-5"
            style={{ animationDelay: `${i * 90 + 80}ms` }}
          >
            <h2 className="mb-2 text-base font-semibold text-[var(--sea-ink)]">
              {t}
            </h2>
            <p className="m-0 text-sm text-[var(--sea-ink-soft)]">{d}</p>
          </article>
        ))}
      </section>
    </main>
  )
}
