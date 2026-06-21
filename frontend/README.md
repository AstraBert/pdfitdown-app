# PDFItDown Frontend

Frontend for [PDFItDown](https://pdfitdown.app), a web app that converts files to PDF. Built with [TanStack Start](https://tanstack.com/start), [React](https://react.dev), and [Tailwind CSS](https://tailwindcss.com).

## Getting Started

To run this application:

```bash
pnpm install
pnpm dev
```

## Building For Production

```bash
pnpm build
```

## Testing

This project uses [Vitest](https://vitest.dev/):

```bash
pnpm test
```

## Linting & Formatting

```bash
pnpm lint
pnpm format
pnpm check
```

## Deploy to Cloudflare Workers

This project uses the Cloudflare Vite plugin and `wrangler.jsonc`:

1. Install Wrangler: `npm install -g wrangler`
2. Authenticate: `wrangler login`
3. Deploy: `npx wrangler deploy`

For production env vars, run `wrangler secret put MY_VAR` for each secret listed in `.env.example`. Public (non-secret) vars go in `wrangler.jsonc` under `vars`.

## Environment Variables

| Variable                   | Description                                       |
| -------------------------- | ------------------------------------------------- |
| `VITE_WORKOS_CLIENT_ID`    | WorkOS client ID for authentication               |
| `VITE_WORKOS_API_HOSTNAME` | WorkOS Custom Authentication Domain in production |
| `VITE_POSTHOG_KEY`         | PostHog project API key for analytics             |
| `VITE_POSTHOG_HOST`        | PostHog host (optional, defaults to US cloud)     |
| `VITE_API_BASE_URL`        | Base URL for the backend API                      |

## Tech Stack

- **Framework:** [TanStack Start](https://tanstack.com/start) (full-stack React)
- **Router:** [TanStack Router](https://tanstack.com/router) with file-based routing
- **Styling:** [Tailwind CSS](https://tailwindcss.com)
- **UI Components:** [Shadcn/ui](https://ui.shadcn.com)
- **Auth:** [WorkOS AuthKit](https://workos.com/authkit)
- **Analytics:** [PostHog](https://posthog.com)
- **Deployment:** [Cloudflare Workers](https://workers.cloudflare.com)
