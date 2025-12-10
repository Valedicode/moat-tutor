# Components Structure

This directory contains all reusable React components for the Moat Explain application.

## Directory Organization

```
components/
├── chat/              # Chat-related components
│   ├── ChatInput.tsx  # Reusable input component for both idle and active states
│   ├── MessageBubble.tsx  # Individual message display component
│   └── index.ts       # Barrel export
├── icons/             # SVG icon components
│   ├── MicIcon.tsx    # Microphone icon
│   ├── SendIcon.tsx   # Send/submit icon
│   └── index.ts       # Barrel export
├── ActiveShell.tsx    # Active chat state with left panel and right dashboard
├── IdleHero.tsx       # Initial greeting/idle state
└── README.md          # This file
```

## Component Descriptions

### Chat Components (`chat/`)

- **ChatInput**: A flexible input component that adapts to both idle and active chat states. Includes mic button, text input, and send button.
- **MessageBubble**: Displays individual chat messages with different styles for user and assistant messages.

### Icons (`icons/`)

- **MicIcon**: Microphone icon with active/inactive states
- **SendIcon**: Arrow icon for sending messages

### Layout Components

- **IdleHero**: The centered greeting screen shown when no messages exist
- **ActiveShell**: The split-screen layout with chat panel (30%) and dashboard panel (70%)

## Usage

Import components using path aliases:

```tsx
import { IdleHero } from "@/components/IdleHero";
import { ChatInput, MessageBubble } from "@/components/chat";
import { MicIcon, SendIcon } from "@/components/icons";
```

## Supporting Directories

- **types/**: TypeScript type definitions (e.g., `Message`)
- **utils/**: Utility functions (e.g., `nowStamp` for timestamps)
- **constants/**: Application constants (e.g., `assistantNarratives`)

