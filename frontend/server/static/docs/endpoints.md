# UI Endpoints

- `/` – Home (dashboard)
- `/login` – Login (GET/POST)
- `/signup` – Create account (GET/POST)
- `/signup-success` – Post-signup info page
- `/logout` – Logout
- `/verify-email/<token>` – Email verification callback

- `/list-files` – List files from a disk (GET/POST form)
- `/files-json` – Get files metadata as JSON (GET/POST form view)
- `/meta` – Disk metadata (GET/POST)
- `/file-contents` – Read a file’s contents (GET/POST)
- `/file-contents-format` – Read and format bytes (hex/bits) (GET/POST)
- `/file-compare` – Compare two files (GET/POST)
- `/check-exists` – Check whether a file exists (GET/POST)
- `/files-diff` – Difference in files between two disks (GET/POST)
- `/directory-diff` – Compare files in a directory (GET/POST)

- `/compare` – Block comparison UI
- `/block-data` – Block data viewer UI
- `/block-contents-compare` – Side-by-side block contents compare (GET/POST, also supports query params)

- `/docs` – Static placeholder docs pages (Coming soon)
- `/docs/<page>` – Static placeholder for specific page
- `/guide` – GitBook-style docs SPA served from `static/guide/`



