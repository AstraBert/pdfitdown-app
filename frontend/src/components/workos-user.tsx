import { useAuth } from '@workos-inc/authkit-react'

export default function SignInButton() {
  const { user, isLoading, signIn, signOut } = useAuth()

  if (user) {
    return (
      <button
        onClick={() => signOut()}
        className="rounded-full border border-[var(--chip-line)] bg-[var(--chip-bg)] px-3 py-1.5 text-sm font-semibold text-[var(--sea-ink)] shadow-[0_8px_24px_rgba(30,90,72,0.08)] transition hover:-translate-y-0.5 hover:bg-[var(--link-bg-hover)] disabled:opacity-50 disabled:cursor-not-allowed sm:px-4 sm:py-2"
        disabled={isLoading}
      >
        Sign Out
      </button>
    )
  }

  return (
    <button
      onClick={() => signIn()}
      className="rounded-full border border-[rgba(50,143,151,0.3)] bg-[rgba(79,184,178,0.14)] px-3 py-1.5 text-sm font-semibold text-[var(--lagoon-deep)] transition hover:-translate-y-0.5 hover:bg-[rgba(79,184,178,0.24)] disabled:opacity-50 disabled:cursor-not-allowed sm:px-4 sm:py-2"
      disabled={isLoading}
    >
      Sign In
    </button>
  )
}
