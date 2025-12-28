# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is an Instagram scraper that uses modal navigation for sequential post scraping. The project focuses on:
- Session persistence (maintaining login state across runs)
- Multi-profile support (handling multiple Instagram accounts)
- Robust error handling and retry mechanisms
- Modal navigation patterns for efficient scraping

## Architecture Principles

### Core Components (To Be Implemented)

The scraper should be designed around these key architectural components:

1. **Session Manager**: Handles authentication, cookie persistence, and session state management across multiple profiles
2. **Navigation Controller**: Manages modal navigation flow for sequential post scraping, including state tracking and navigation history
3. **Scraper Engine**: Core scraping logic that extracts data from Instagram posts while respecting rate limits
4. **Error Handler**: Centralized error handling with retry logic, exponential backoff, and graceful degradation
5. **Profile Manager**: Manages multiple Instagram account credentials and switching between profiles
6. **Data Storage**: Persistent storage for scraped data, session state, and configuration

### Design Considerations

- **Rate Limiting**: Instagram has strict rate limits. Implement request throttling and respect HTTP 429 responses
- **Session Persistence**: Store session cookies and tokens securely. Sessions should survive application restarts
- **Modal Navigation State**: Track navigation state to handle Instagram's modal-based UI (e.g., when viewing posts in overlay modals)
- **Error Recovery**: Implement checkpointing so scraping can resume from the last successful position after errors
- **Anti-Detection**: Randomize request timing, use realistic user-agent strings, and simulate human-like behavior
- **Multi-Profile Isolation**: Ensure complete isolation between different Instagram accounts (separate sessions, cookies, storage)

## Development Commands

**Note**: This project is in initial setup phase. Standard commands will depend on the chosen language/framework:

### For Python-based implementation:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python main.py

# Run tests
pytest tests/

# Run specific test
pytest tests/test_session_manager.py

# Linting
flake8 src/
pylint src/
```

### For Node.js/TypeScript implementation:
```bash
# Install dependencies
npm install

# Run the scraper
npm start

# Run tests
npm test

# Run specific test
npm test -- session-manager.test.ts

# Linting and type checking
npm run lint
npm run typecheck
```

## Important Implementation Notes

### Session Management
- Use secure storage for credentials (environment variables or encrypted config files)
- Implement session validation before each scraping operation
- Handle session expiration gracefully with automatic re-authentication

### Modal Navigation
- Instagram uses a modal-based UI for post viewing. Track modal state to avoid navigation errors
- Implement breadcrumb tracking to know the current position in the scraping flow
- Handle edge cases where modals don't open or load incorrectly

### Multi-Profile Support
- Each profile should have isolated storage (separate cookie files, separate cache)
- Implement profile switching without cross-contamination of session data
- Support concurrent operations across different profiles with separate rate limiters

### Error Handling
- Implement exponential backoff for rate limit errors (HTTP 429)
- Distinguish between transient errors (retry) and permanent errors (skip/log)
- Save progress frequently to enable resumption after crashes
- Log all errors with sufficient context for debugging

### Data Storage
- Store scraped data in a structured format (JSON, SQLite, or database)
- Include metadata: timestamp, profile used, scraping session ID
- Implement data deduplication to avoid re-scraping the same content
