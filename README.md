<<<<<<< HEAD
# ProjektXX
=======
# Social Video AutoPublisher (ProjektXX)

Automatisiertes System zum Sammeln, Rendern und Veröffentlichen von Video-Compilations auf mehreren Plattformen (YouTube, TikTok, Clapper).

## Features

- Modulare Scraper-Struktur (`scraper/`) für Reddit, Instagram, Twitter.
- Rendering-Pipeline auf Basis von `ffmpeg-python`.
- Dynamische Render-Templates mit optionalem Intro/Outro, Wasserzeichen und Hintergrundmusik.
- Upload-Module für YouTube (vollständiges OAuth-Setup) sowie Platzhalter für TikTok und Clapper.
- Scheduler & Automationsmodule (`automation/`) für tägliche Uploads, Logging und Cleanup.
- Konfigurierbare Settings über `config/settings.json` und optionale Flask-UI (`ui/flask_app.py`).

## Schnellstart

1. **Dependencies installieren**

   ```bash
   pip install -r requirements.txt
   ```

2. **FFmpeg bereitstellen**

   - Unter Windows: https://ffmpeg.org/download.html → Binärdateien entpacken und `ffmpeg.exe` zum `PATH` hinzufügen.

3. **Secrets konfigurieren**

   - Lege eine `.env` (nicht im Repo enthalten) mit Pfaden zu OAuth-Dateien und Session-Tokens an.
   - Hinterlege YouTube-OAuth-Datei unter `config/client_secret.json` (siehe [YouTube OAuth Guide](https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps)).

4. **Settings anpassen**

   - Bearbeite `config/settings.json` oder nutze die Flask-UI:

     ```bash
     python -m ui.flask_app
     ```

5. **Testlauf starten**

   ```bash
   python main.py
   ```

   Die Uploads für TikTok und Clapper lösen aktuell `NotImplementedError` aus – ideal für Trockenläufe.

6. **Scheduler aktivieren**

   ```bash
   python main.py --mode schedule
   ```

   - Nutzt APScheduler (`timezone`, `upload_times` in `settings.json`) und erzeugt für jede Plattform einen Cron-Job.
   - Optional kann `scheduler_jobstore_url` gesetzt werden (z. B. `sqlite:///config/scheduler.db`) für persistente Jobs.

## Plattform-spezifische Hinweise

- **YouTube**: Vollständige OAuth-Authentifizierung mit Token-Refresh und Resumable Upload implementiert. API-Quotas beachten.
- **TikTok**: Implementierung über Appium + Emulator oder TikTok-API erforderlich. Stub vorhanden.
- **Clapper**: Selenium-basierte Browser-Automatisierung empfohlen. Stub vorhanden.

## Datenfluss

1. `scraper.reddit.RedditScraper` lädt Top-Meme-Videos herunter (`temp/`).
2. `render.pipeline.render_videos` fügt Intro, Clips & Outro zusammen, normalisiert Audio, mischt Musik & Wasserzeichen.
3. `upload.youtube.upload_to_youtube` übernimmt OAuth, Token-Refresh und Resumable Upload.
4. `automation.cleanup.cleanup` entfernt Rohclips nach erfolgreicher Verarbeitung.

## Konfiguration & Scheduler

- `upload_times`: Zeitpunkt je Plattform (`"HH:MM"` oder Objekt mit `{"time": "...", "days": [...]}`).
- `timezone`: Zeitzone für die Cron-Triggers (z. B. `Europe/Berlin`).
- `reddit_subreddits`: Liste priorisierter Subreddits (Videos werden gesammelt, bis `reddit_limit` erreicht ist).
- `reddit_subreddit`: Einzelnes Subreddit als Fallback, falls keine Liste definiert wurde.
- `scheduler_max_workers` / `scheduler_max_instances`: Kontrolle über gleichzeitige Jobs.
- `output_filename_template`: Platzhalter `{timestamp}` stellt sicher, dass neue Dateien nicht überschrieben werden.

## Render-Templates & Assets

- `render_intro_path` / `render_outro_path`: optionale MP4-Clips, die vor bzw. nach der Compilation eingefügt werden.
- `render_watermark`: PNG/JPEG mit positionierbarem Overlay (`position`, `margin`, `width` oder `relative_width`, `opacity`).
- `render_background_music`: MP3/WAV mit Looping, Lautstärke (`volume`) und optionalem Ducking des Originaltons.
- `render_loudness`: Zielwerte für Loudness-Normalisierung (EBU R128).
- `render_padding_color`: Hintergrundfarbe, wenn Clips gepadded werden (z. B. `black`, `#111111`).

Lege deine Assets im Projekt (z. B. `assets/intro.mp4`, `assets/watermark.png`, `assets/music.mp3`) ab und verweise sie in `config/settings.json`. Bei fehlenden Dateien protokolliert die Pipeline Warnungen und überspringt den Effekt.
## Weiterentwicklung

- Erweiterte Scraper (z. B. Instagram Graph API, Reddit OAuth mit Rate-Limit-Handling).
- Template-System für Intro/Outro, Overlays und Branding (`render/templates/`).
- Scheduler-Setup via Windows Task Scheduler oder Docker + Cron.
- Logging in externe Systeme (Sentry, ELK).

## Rechtliches

Stelle sicher, dass du für alle gesammelten Inhalte über die notwendigen Nutzungsrechte verfügst. Automatisiertes Scraping kann gegen Nutzungsbedingungen der Dienste verstoßen; prüfe regulär die Policies.

>>>>>>> 83f488b (Initial commit)
