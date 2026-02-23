# Privacy Statement

**Last Updated:** 2026-02-23
**Version:** 1.0
**Authority:** PRS-01 §7 (Publishing Readiness Spec)

---

## Data Locality

This application processes all data locally on your machine. **No telemetry is collected. No data leaves your machine in default configuration.**

- All game state, session logs, and generated content remain on your local filesystem
- No cloud synchronization or remote storage
- No analytics, tracking, or usage reporting
- Network access is disabled by default (offline-first architecture)

Any future features that require network access will be:
- Explicitly opt-in (default: OFF)
- Clearly documented with user-facing notifications
- Designed to fail gracefully when network is unavailable

---

## Microphone

Microphone access (for speech-to-text input) is **opt-in only**. It is **not enabled by default**.

When microphone access is enabled:
- Audio is processed locally by the speech-to-text (STT) engine
- Raw audio is **not retained** after transcription unless you explicitly enable recording via configuration
- Transcripts are stored locally as session artifacts (see Retention Defaults below)
- No audio data is transmitted over the network

To enable microphone input, you must explicitly configure it in your settings. The application will not access your microphone without your consent.

---

## Retention Defaults

The following table describes what data is stored, where, and for how long:

| Data Type | Location | Retention | Deletion |
|-----------|----------|-----------|----------|
| Session logs | `logs/` | Until user deletes | Delete directory |
| Oracle state | `oracle_db/` | Until user deletes | Delete directory |
| Generated audio | `audio_cache/` | Until user deletes | Delete directory |
| Generated images | `image_cache/` | Until user deletes | Delete directory |
| Configuration | `config/` | Until user modifies | Edit or delete files |

All data persists until you explicitly delete it. No automatic deletion or expiration occurs.

---

## Delete Everything

To completely remove all user-generated data and reset the application to a clean state:

1. **Delete data directories:**
   ```bash
   rm -rf logs/
   rm -rf oracle_db/
   rm -rf audio_cache/
   rm -rf image_cache/
   ```

2. **Delete any `.sqlite` database files in the project root:**
   ```bash
   rm -f *.sqlite
   rm -f *.db
   ```

3. **Reset configuration (optional):**
   - To reset to defaults: delete `config/` directory and re-run setup
   - To preserve custom settings: leave `config/` directory intact

After deleting these directories and files, no user data remains on disk. The application will regenerate default configuration on next run.

---

## Questions or Concerns

If you have questions about data handling or privacy practices, please open an issue on the project's GitHub repository. This project is open-source — you can audit the code to verify these privacy claims.
