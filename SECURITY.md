# Security and Responsible Data Use

TalentIQ is a local demonstration MVP. Do not use it to process real candidate personal data until security, privacy, operational and legal reviews are complete.

## Repository

https://github.com/Sankalp-gupta1/TalentIQ-AI-Resume-Screening

## Secrets
- Store private configuration in a local `.env` file.
- `.env`, `.env.local`, virtual environments, databases, uploads and build output are ignored by Git.
- Never commit API keys, JWT secrets, production passwords or real CVs.
- `OPENAI_API_KEY` is optional and used only for job-description extraction in this version.
- Do not place private provider keys in frontend `NEXT_PUBLIC_` variables.

## Current safeguards
- Passwords are hashed using Argon2; API sessions use signed JWT bearer tokens.
- Client users are filtered to submissions associated with their `client_id`.
- Client profile responses mask email and phone and omit raw CV text.
- The scoring module excludes direct identifiers from its score calculation.
- Candidate profile reads generate audit events.
- Recruiter deletion anonymizes selected fields and removes client submissions.
- Uploads are limited by file extension and per-file size; exact-file duplicates use SHA-256 within a job.

## Known gaps
This prototype does not include a complete threat model, rate limiting, malware scanning, encrypted object storage, key rotation, comprehensive tenant-isolation tests, automated retention/deletion across backups, or an independently audited DPDP compliance program. Consent confirmation is a recruiter attestation, not a full candidate-facing consent system. Upload processing is synchronous; the 500-file setting is not a performance guarantee. OCR is not included.

## Safe demo practices
- Use only fictional/sample data.
- Do not upload real CVs to a public demo or public issue.
- Rotate demo credentials and replace local secrets before any hosted environment.
- Report security issues privately to the repository owner.
