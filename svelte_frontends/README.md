# Turborepo Svelte Monorepo

A monorepo containing multiple Svelte 5/SvelteKit frontend applications for StarCraft 2 utilities and other projects.

## Project Structure

```mermaid
flowchart TB
    subgraph svelte_frontends["svelte_frontends"]
        subgraph apps["Apps (9)"]
            buildorder[buildorder]
            matchinfo[matchinfo]
            replay_comparer[replay_comparer]
            replay_pack_builder[replay_pack_builder]
            raceroom[raceroom]
            audiobook[audiobook]
            tts[tts]
            telegram[telegram]
            login[login]
        end

        subgraph packages["Packages (3)"]
            ui[ui]
            sc2_utils[sc2-utils]
            typescript_config[typescript-config]
        end
    end

    apps --> packages
    buildorder --> sc2_utils
    matchinfo --> sc2_utils
    audiobook --> ui
    login --> ui
    telegram --> ui
    raceroom --> ui
```

## Apps Overview

```mermaid
flowchart LR
    subgraph SC2_Apps["SC2 Utilities"]
        buildorder["buildorder<br/>Build order overlay<br/>Polls SC2 game API"]
        matchinfo["matchinfo<br/>Match info display<br/>MMR, race, opponent"]
        replay_comparer["replay_comparer<br/>Compare replays<br/>with charts"]
        replay_pack_builder["replay_pack_builder<br/>Upload, filter, rename<br/>SC2 replays"]
    end

    subgraph Gaming_Apps["Gaming"]
        raceroom["raceroom<br/>Track RaceRoom<br/>best times"]
    end

    subgraph Media_Apps["Media"]
        audiobook["audiobook<br/>Upload/manage<br/>audiobook files"]
        tts["tts<br/>Text-to-speech<br/>OBS overlay support"]
        telegram["telegram<br/>Search Telegram<br/>messages/media"]
    end

    subgraph Auth_Apps["Auth"]
        login["login<br/>OAuth login<br/>status page"]
    end
```

## External API Connections

```mermaid
flowchart TB
    subgraph Frontend_Apps["Svelte Apps"]
        SC2_Apps[SC2 Apps]
        Other_Apps[Other Apps]
    end

    subgraph External_APIs["External Services"]
        SC2_Game_API["SC2 Game API<br/>localhost:6119"]
        Nephest_API["nephest.com<br/>MMR/rank data"]
        FastAPI["FastAPI Server<br/>localhost:8000"]
    end

    subgraph FastAPI_Routes["FastAPI Routes"]
        Audiobook_API["/api/audiobook/*"]
        Raceroom_API["/api/raceroom/*"]
        Replay_API["/api/parse_replay"]
        TTS_WS["/tts-api/ws/*"]
        Login_API["/login/*"]
    end

    SC2_Apps --> SC2_Game_API
    SC2_Apps --> Nephest_API
    Other_Apps --> FastAPI
    FastAPI --> Audiobook_API
    FastAPI --> Raceroom_API
    FastAPI --> Replay_API
    FastAPI --> TTS_WS
    FastAPI --> Login_API
```

## SC2 App Integration Flow

```mermaid
sequenceDiagram
    participant SC2 as SC2 Game
    participant App as buildorder/matchinfo
    participant Utils as @repo/sc2-utils
    participant Nephest as nephest.com API

    App->>SC2: Poll /game endpoint
    SC2-->>App: Game state data

    App->>SC2: Poll /ui endpoint
    SC2-->>App: Active screen data

    App->>Utils: getCurrentScene(gameData, uiData)
    Utils-->>App: Scene: game|menu|replay

    alt Scene changed to new game
        App->>Nephest: GET /sc2/api/characters?name=XXX
        Nephest-->>App: MMR, rank data
        App->>App: Display overlay
    end
```

## Deployment / Subdomain Mapping

```mermaid
flowchart LR
    subgraph DNS["Subdomains"]
        burnysc2_xyz["burnysc2.xyz"]
    end

    burnysc2_xyz --> buildorder["build.burnysc2.xyz"]
    burnysc2_xyz --> matchinfo["match.burnysc2.xyz"]
    burnysc2_xyz --> raceroom["race.burnysc2.xyz"]
    burnysc2_xyz --> audiobook["book.burnysc2.xyz"]
    burnysc2_xyz --> tts["tts.burnysc2.xyz"]
    burnysc2_xyz --> telegram["tg.burnysc2.xyz"]
    burnysc2_xyz --> login["login.burnysc2.xyz"]
```

## Tech Stack

- **Framework**: Svelte 5 / SvelteKit 2
- **Build Tool**: Turborepo 2
- **Language**: TypeScript 5.9
- **Linting**: Biome
- **Testing**: Vitest, Playwright

## Commands

```sh
# Development
npm run dev              # Run all apps in dev mode
npm run build            # Build all apps
npm run check            # Type-check all apps
npm run lint             # Lint all apps
npm run lint:fix         # Fix lint issues

# Testing
npm run test             # Run all tests
npm run test:unit        # Unit tests only
npm run test:integration # Integration tests only
```
