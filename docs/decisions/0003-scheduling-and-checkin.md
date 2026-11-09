# ADR 0003 — Scheduling and check-in

Status: Implemented for Phase 1B, pending user acceptance.

## Domain and access

The scheduling app adds Appointment, AppointmentEvent and ProviderScheduleLock. Appointment links the existing Patient and Django user physician. AppointmentEvent links an appointment to the existing patient AuditEvent, preserving actor, time and shared audit identity without changing the earlier audit model.

Administrator and FrontDesk manage all single-clinic appointments. Physician-only staff see their own schedules, details and patient-context appointments. Nurses can read the single-clinic schedule. Multi-role users receive the union of their roles. Existing patient-demographic permissions remain as defined in ADR 0002.

Physicians must be active users in the Physician group. No separate practitioner, department or room domain is introduced yet. Availability means an active physician with no overlapping reserved appointment. Configurable working hours, leave and recurring sessions are future scope.

## States and transitions

| Current state | Action | Next state | Requirements |
| --- | --- | --- | --- |
| scheduled | arrive | arrived | Appointment's clinic-local calendar date, current version |
| scheduled | cancel | cancelled | Nonblank reason, current version |
| scheduled | no_show | no_show | Start has been reached, nonblank reason, current version |
| arrived | cancel | cancelled | Nonblank reason, current version |

Cancelled and no_show are terminal in this increment. Repeated or other transitions return a conflict. Rescheduling/editing is allowed only while scheduled, preserves patient identity and requires the current version. A stale edit cannot overwrite another action. The clinical roomed, in_progress, completed and encounter workflows are deferred.

Check-in stores checked_in_at and checked_in_by and creates an audit event in the same transaction. It does not create a clinical encounter. Cancellation after arrival preserves the prior check-in provenance.

## Persistence, review and conflicts

Creation/editing requires a server-signed review token binding normalized appointment data, staff identity, target appointment and version, with a ten-minute lifetime. Confirmation revalidates the form, state and availability.

Intervals are half-open. Reservations overlap if existing start is before requested end and existing end is after requested start. Adjacent appointments are allowed. Scheduled/arrived appointments reserve time. Cancelled/no_show appointments release it.

Each write first updates a dedicated provider lock row inside the transaction, in sorted physician order for provider changes. SQLite takes its write lock before availability reads. PostgreSQL's ordinary row locks apply to that update. An additional partial unique constraint protects equal reserved start times, but does not independently enforce general interval exclusion.

All appointment and audit mutations share one transaction. SQLite lock contention returns a retryable HTTP 409 instead of silently allowing a second reservation. Direct ORM/database writes bypass service rules and are unsupported. PostgreSQL exclusion constraints and load testing remain future work before shared deployment.

## Time and presentation

Forms accept clinic-local times and reject ambiguous or nonexistent DST input. Timestamps are persisted in UTC. Duration uses elapsed minutes in UTC, including across DST. Durations are 5–240 minutes in five-minute increments, and creation/rescheduling requires a future start.

Calendars default to readable daytime start-hour rows and expand for actual early, late or cross-midnight bookings. Week view starts Monday. Repeated DST hours share a local hour row, with explicit time-zone abbreviations on appointment start/end labels. Cross-midnight appointments appear on both dates. The agenda provides full start/end details.

The calendar/worklist filter accepts years 1900–2100. Date and physician filters are validated server-side. These local-demo constraints are recorded separately from the immutable product baseline.

Implementation references are Django's [SQLite database notes](https://docs.djangoproject.com/en/5.2/ref/databases/#sqlite-notes) and [time-zone-aware form input](https://docs.djangoproject.com/en/5.2/topics/i18n/timezones/#time-zone-aware-input-in-forms).
