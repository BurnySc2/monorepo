# Svelte Frontends Monorepo

This is a monorepo of SvelteKit applications and shared packages using npm workspaces + Turborepo.

## Project Structure

```
svelte_frontends/
├── apps/                    # 9 SvelteKit applications
│   ├── audiobook/
│   ├── buildorder/
│   ├── login/
│   ├── matchinfo/
│   ├── raceroom/
│   ├── replay_comparer/
│   ├── replay_pack_builder/
│   ├── telegram/
│   └── tts/
├── packages/               # 4 shared packages
│   ├── api-types/
│   ├── sc2-utils/
│   ├── typescript-config/
│   └── ui/
└── AGENTS.md              # This file
```

## Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| Package Manager | npm | 11.11.1 |
| Framework | Svelte | 5.54.1 |
| Framework | SvelteKit | 2.55.0 |
| Build Tool | Vite | 8.0.1 |
| Build Orchestration | Turborepo | 2.9.1 |
| TypeScript | TypeScript | 5.9.3 |
| Type Checking | svelte-check | 4.4.5 |
| Validation | Zod | 4.3.6 |
| Unit Testing | Vitest | 4.1.0 |
| E2E/Integration Testing | Playwright | 1.58.2 |
| Linting/Formatting | Biome | 2.4.6 |
| CSS | Tailwind CSS | 4.0.0 |

---

## Package Descriptions

### Apps

| App | Description |
|-----|-------------|
| login | Authentication/m login portal |
| tts | Text-to-speech interface |
| replay_pack_builder | Replay pack builder tool |
| audiobook | Audiobook management |
| telegram | Telegram bot interface |
| raceroom | Racing room/session manager |
| replay_comparer | Replay comparison tool |
| buildorder | Build order calculator |
| matchinfo | Match information display |

### Packages

| Package | Description |
|---------|-------------|
| `@repo/ui` | Shared UI components |
| `@repo/sc2-utils` | StarCraft 2 utilities |
| `@repo/api-types` | Generated API types (from OpenAPI at localhost:8000) |
| `@repo/typescript-config` | Shared TypeScript configuration |

---

## Development Commands

### Root Level Commands

Run from the monorepo root (`/`):

| Command | Description |
|---------|-------------|
| `npm run dev` | Run all apps in dev mode concurrently |
| `npm run build` | Build all apps (cached via Turborepo) |
| `npm run format` | Check formatting with Biome |
| `npm run format:fix` | Auto-fix formatting |
| `npm run lint` | Lint check with Biome |
| `npm run lint:fix` | Auto-fix lint errors |
| `npm run check` | Run svelte-check on all apps |
| `npm run check-types` | Run TypeScript compiler on all apps |
| `npm run test` | Run all tests (unit + integration) |
| `npm run test:unit` | Run unit tests only |
| `npm run test:integration` | Run integration tests only |
| `npm run precommit` | format:fix → build → lint → check |
| `npm run prepush` | precommit → test:unit → test:integration |

### Per-App Commands

Run from an app directory (`/apps/<app-name>`):

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | svelte-kit sync && vite build |
| `npm run preview` | Preview production build |
| `npm run check` | svelte-kit sync && svelte-check |
| `npm run check:watch` | svelte-kit sync && svelte-check --watch |
| `npm run check-types` | tsc --noEmit |
| `npm run test` | vitest run (or placeholder) |
| `npm run test:watch` | vitest (watch mode) |

> **Note**: Not all apps have Vitest configured. Run `npm run test` from an app to see available test commands.

---

## Dev Server Ports

Each app runs on a unique port:

| App | Port |
|----|------|
| login | 5173 |
| tts | 5174 |
| replay_pack_builder | 5175 |
| audiobook | 5178 |
| telegram | 5179 |
| raceroom | 5180 |
| replay_comparer | 5181 |
| buildorder | 5182 |
| matchinfo | 5183 |

When running `npm run dev` from root, all apps start concurrently on their respective ports.

---

## Type Checking

### Svelte-check (recommended)

```bash
# Root - all apps
npm run check

# Single app
cd apps/<app-name>
npm run check

# Watch mode (single app)
npm run check:watch
```

### TypeScript Compiler

```bash
# Root - all apps
npm run check-types

# Single app
cd apps/<app-name>
npm run check-types
```

---

## Linting with Biome

Biome 2.4.6 is configured with:
- 4-space indentation
- 120 character line width
- TypeScript and Svelte support

### Commands

```bash
# Check formatting
npm run format

# Auto-fix formatting
npm run format:fix

# Lint check
npm run lint

# Auto-fix lint errors
npm run lint:fix

# Check both at once
npx biome check . --error-on-warnings

# Format both at once
npx biome format . --write
```

---

## Testing

### Test Discovery

- Unit tests: `*.test.ts` files in `src/lib/**` directories
- Vitest config: Per-app `vitest.config.ts` (not all apps have this)
- Integration tests: Managed per-app (most are placeholders)

### Running Tests

```bash
# All apps - all tests
npm run test

# All apps - unit tests only
npm run test:unit

# All apps - integration tests only
npm run test:integration

# Single app - unit tests
cd apps/<app-name>
npm run test

# Single app - watch mode
npm run test:watch
```

### App Test Status

| App | Has Vitest | Has Integration Tests |
|-----|-----------|-------------------|
| login | Yes | Placeholder |
| tts | No | - |
| replay_pack_builder | No | - |
| audiobook | No | - |
| telegram | No | - |
| raceroom | No | - |
| replay_comparer | No | - |
| buildorder | No | - |
| matchinfo | No | - |

---

## Environment Variables

### Client-Side Variables

All client-exposed environment variables must use the `VITE_` prefix:

```
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=my-app
```

### Usage in Code

```typescript
// Access in Svelte/Vite
import { PUBLIC_API_URL } from '$env/VITE_PUBLIC_API_URL';
```

### Adding New Variables

1. Add to `.env` file in app root
2. Add to `.env.example` (do not commit secrets)
3. Create `$env/static/` or `$env/dynamic/` files in `$lib/` for typing
4. Use `$env.VITE_*` pattern in code

---

## Build Configuration

### Static Adapter

All apps use `@sveltejs/adapter-static`:

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

Output is generated in `build/` directory for each app.

---

## API Types Generation

The `@repo/api-types` package generates TypeScript types from an OpenAPI specification at `localhost:8000`.

### Regenerate Types

```bash
# From root
npm run generate-types
```

### Using Generated Types

```typescript
import type { SomeEndpointResponse } from '@repo/api-types';
```

---

## Pre-Commit & Pre-Push Hooks

### Pre-Commit Hook

```bash
npm run precommit
# Runs: format:fix → build → lint → check
```

### Pre-Push Hook

```bash
npm run prepush
# Runs: precommit → test:unit → test:integration
```

---

## Common Tasks

### Adding a New App

1. Create directory `apps/<app-name>/`
2. Add `package.json` with scripts and dependencies
3. Add to workspace in root `package.json` (automatic with npm workspaces)
4. Configure dev server port in `vite.config.ts`

### Adding a Shared Package

1. Create directory `packages/<package-name>/`
2. Add `package.json` with name `@repo/<package-name>`
3. Add to workspace in root `package.json`
4. Add as dependency in app `package.json`:

```json
"dependencies": {
  "@repo/<package-name>": "*"
}
```

### Adding Dependencies to an App

```bash
cd apps/<app-name>
npm install <package>
```

---

## Troubleshooting

### Port Already in Use

Stop the conflicting process or use a different port:

```bash
# Find process using port
lsof -i :<port>

# Kill process
kill <PID>
```

### Cache Issues

Clear Turborepo cache:

```bash
rm -rf node_modules/.cache
npm run build -- --force
```

### Type Generation Fails

Ensure FastAPI backend is running at `localhost:8000` with OpenAPI docs available.

---

## Naming Conventions

This project uses consistent naming conventions across all apps.

### Variables and State

Use `snake_case` for all variables and Svelte state:

```typescript
let is_loading = $state(false);
let user_text = $state("");
let selected_track_id = $state(undefined);
let error_message = $state(null);
```

### Functions

Use `snake_case` for all function names (both local and exported):

```typescript
function check_login_status() { ... }
async function generate_audio() { ... }
async function load_voices() { ... }
export async function fetch_login_status() { ... }
export async function fetch_voices() { ... }
```

### Interface and Type Properties

Use `snake_case` for all interface and type properties:

```typescript
interface SearchFilters {
    search_text: string;
    channel_name: string;
    datetime_min: string;
    datetime_max: string;
    reactions_min: number;
}
```

### Constants

Use `UPPER_CASE` with underscores for constants:

```typescript
const DEFAULT_REPLAY_NAME_PATTERN = "*.SC2Replay";
const STORAGE_KEY = "user_settings";
const MAX_UPLOAD_SIZE = 50 * 1024 * 1024;
```

### Type and Interface Names

Use `PascalCase` for type and interface names:

```typescript
interface SearchFilters { ... }
interface FilterSettings { ... }
type UserProfile = { ... };
```

---

## API File Structure

Each app should have a dedicated API file for backend requests.

### File Location

Store API code in `src/lib/` with one of these naming patterns:

- `src/lib/api.ts`
- `src/lib/api_client.ts`
- `src/lib/api/*.ts` (for larger APIs)

### Required get_api_base() Helper

Every API file should include this helper function:

```typescript
const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET;
    const protocol = target?.includes("localhost") ? "http" : "https";
    return target ? `${protocol}://${target}` : "http://localhost:8000";
};
```

### API Function Naming

Use `snake_case` with `fetch_` prefix for API functions:

```typescript
export async function fetch_login_status() {
    const resp = await fetch(`${get_api_base()}/auth/status`);
    if (!resp.ok) {
        throw new Error(`Failed to fetch login status: ${resp.statusText}`);
    }
    return resp.json();
}

export async function fetch_voices() {
    const resp = await fetch(`${get_api_base()}/tts-generate/voices`);
    if (!resp.ok) {
        throw new Error(`Failed to fetch voices: ${resp.statusText}`);
    }
    return resp.json();
}
```

### Error Handling Pattern

Always check `resp.ok` and throw descriptive errors:

```typescript
if (!resp.ok) {
    throw new Error(`Failed to ${action}: ${resp.statusText}`);
}
```

### Current API Files by App

| App | API File | Functions |
|-----|----------|------------|
| login | `src/lib/api.ts` | `fetch_login_status`, `fetch_logout` |
| tts | `src/lib/api.ts` | `fetch_voices`, `fetch_generate_tts` |
| telegram | `src/lib/api.ts` | `fetch_search`, `fetch_queue_file`, `fetch_delete_file` |
| replay_pack_builder | `src/lib/api_client.ts` | `parse_replay_file` |
| replay_comparer | `src/lib/api.ts` | `fetch_parse_replay`, `fetch_replay_events` |
| raceroom | `src/lib/api_client.ts` | `fetch_tracks`, `fetch_times` |
| audiobook | `src/lib/api/*.ts` | `get_books`, `upload_epub`, `get_available_voices` |

---

## Useful Commands Reference

```bash
# Install dependencies
npm install

# Run specific app
cd apps/<app-name> && npm run dev

# Build all apps
npm run build

# Type check all
npm run check

# Lint and format
npm run lint
npm run format

# Run tests
npm run test

# Full pre-push check
npm run prepush

# Generate API types
npm run generate-types
```