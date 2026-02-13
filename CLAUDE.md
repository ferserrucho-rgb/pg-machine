# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
pip install streamlit pandas openpyxl
streamlit run pg_machine_app.py
```

No test framework, linter, or build system is configured.

## Architecture

Single-file Streamlit application (`pg_machine_app.py`, ~115 lines) for managing sales leads and opportunities. All UI, data logic, and styling live in one file organized into four sections: CONFIG, DATA LOGIC, SIDEBAR, and LAYOUT.

**Data model:** In-memory list of dictionaries stored in `st.session_state.db_leads`. Each opportunity has an `id` (truncated UUID), project/account names, USD amount, category, and a list of activity records. No persistent storage — data lives only for the session duration.

**Three categories:** LEADS, OFFICIAL, GTM — displayed as columns in the dashboard, sorted by amount descending.

**Key flows:**
- **Excel import** (sidebar): Bulk import from two formats ("Leads Propios" and "Forecast BMC") with auto-categorization
- **Manual entry** (sidebar): Add individual opportunities via form
- **Activity management** (detail view): Add activities (Email, Call, Meeting, Assignment) with SLA levels (Urgent/Important/Not Urgent), then mark as Completed/Answered

State transitions use `st.rerun()` to trigger full app rerenders. Navigation between dashboard and detail views is driven by `st.session_state.selected_id`.

## Conventions

- All code, comments, and UI text are in **Spanish**
- Custom CSS is embedded via `st.markdown()` with `unsafe_allow_html=True`
- Dictionary-based data model (no classes or ORM)
- Emojis used extensively in the UI for visual hierarchy
