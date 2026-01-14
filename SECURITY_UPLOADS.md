# Upload-Sicherheit (Kurzfassung)

## Schutzmassnahmen
- Serverseitige Limits: max. 15 MB pro Datei, max. 10 Dateien pro Upload-Batch.【F:apps/exams/security.py†L8-L12】
- Strikte Allowlist für Dateiendungen (pdf, docx, pptx, xlsx, png, jpg, jpeg, zip) plus Blocklist für ausführbare/skriptbasierte Dateien.【F:apps/exams/security.py†L14-L35】
- MIME-Prüfung: Content-Type wird mit Dateiendung abgeglichen und zusätzlich über Signaturen (Header-Bytes) geprüft; Unbekanntes wird abgelehnt.【F:apps/exams/security.py†L37-L112】
- ZIP-Inspektion: keine Pfad-Traversal-Einträge, keine verschlüsselten ZIPs, Limit für Einträge (200) und entpackte Gesamtgrösse (150 MB), sowie Prüfung der enthaltenen Dateiendungen.【F:apps/exams/security.py†L115-L151】
- Downloads werden immer als Attachment mit `X-Content-Type-Options: nosniff` ausgeliefert; Dateinamen werden bereinigt.【F:apps/exams/views.py†L90-L165】

## Nicht abgedeckt
- Kein Malware-/Virus-Scan innerhalb erlaubter Dateitypen (z. B. bösartige PDF-Inhalte).
- Keine inhaltliche Prüfung der Dokumente (nur Format/Signaturen).

## Empfehlung für Admins
- Dateien nur in einer isolierten Umgebung (z. B. VM/Sandbox) öffnen und vor der Freigabe prüfen.
