# Zugang zur Brightspace-API einrichten

bskitool nutzt die offizielle Brightspace-Schnittstelle (Valence API) mit OAuth 2.0.
Dafür muss in eurem Brightspace einmalig eine Anwendung registriert werden. Das geht
in fünf Minuten – wenn dein Konto die Berechtigung dafür hat. Wenn nicht, macht es die
Brightspace-Administration eurer Schule; unten steht ein Textbaustein für die Anfrage.

## 1. Anwendung registrieren

1. In Brightspace als Lehrkraft anmelden.
2. **Admin-Tools** (Zahnrad oben rechts) → **Manage Extensibility**. Wenn du diesen
   Punkt nicht siehst, fehlt dir die Berechtigung → Abschnitt 4.
3. Reiter **OAuth 2.0** → **Register an app**.
4. Felder ausfüllen:

   | Feld | Wert |
   |---|---|
   | Application Name | `bskitool` (oder dein Name – frei wählbar) |
   | Redirect URI | `https://localhost:8080/callback` |
   | Scope | `core:*:* content:*:* grades:*:* dropbox:*:*` |
   | Access Token Lifetime | Standard (3600) |
   | Prompt for user consent | an |
   | Enable refresh tokens | **an** – sonst musst du dich jede Stunde neu anmelden |

   Wenn bskitool auch **Quiz-Hüllen** für benotete Quizze anlegen soll, ergänze
   `quizzing:*:*` in der Scope-Zeile. Ohne diesen Scope legt bskitool trotzdem alles
   andere an und schreibt einen Hinweis ins Protokoll.

5. Speichern. Brightspace zeigt jetzt **Client ID** und **Client Secret**. Das Secret
   wird **nur einmal** angezeigt – kopiere es sofort. Verloren? Anwendung löschen und neu
   registrieren.

## 2. In bskitool eintragen

Reiter **Einstellungen & Anmeldung**:

| Feld | Wert |
|---|---|
| Brightspace-Adresse | eure Adresse ohne `https://`, z. B. `meineschule.brightspace.com` oder `lms.meineschule.de` |
| Client-ID | aus Schritt 1 |
| Client-Secret | aus Schritt 1 |
| Redirect-URI | `https://localhost:8080/callback` – **muss zeichengenau** mit Brightspace übereinstimmen |
| Scopes | dieselbe Zeile wie in Brightspace – **zeichengenau** |
| PKCE | nur anhaken, wenn die Anwendung in Brightspace mit PKCE registriert wurde |

**Speichern**, dann **Bei Brightspace anmelden**.

## 3. Die Anmeldung

1. Ein Browserfenster öffnet die Brightspace-Anmeldung. Wie gewohnt anmelden.
2. Brightspace fragt: „Darf *bskitool* in deinem Namen …?“ → bestätigen.
3. Brightspace leitet zu `https://localhost:8080/callback` zurück. Der Browser warnt:
   „Diese Verbindung ist nicht privat“ / „Dem Zertifikat wird nicht vertraut“.
   **Das ist normal.** bskitool hat ein eigenes Zertifikat für deinen Rechner erzeugt,
   weil Brightspace nur an https-Adressen zurückleitet. Klick **Erweitert** →
   **Weiter zu localhost (unsicher)**. Bei Safari: **Details einblenden** → **Diese Website
   öffnen**.
4. Die Seite zeigt „Geschafft“. In bskitool steht oben rechts **angemeldet** und dein Name.

Das Token liegt in `daten/token.json` und wird automatisch erneuert. Abmelden löscht es.

### Notausgang

Wenn der Browser nach der Bestätigung hängt, aber in der Adresszeile etwas wie
`https://localhost:8080/callback?code=…&state=…` steht: die **komplette Adresse**
kopieren und in bskitool in das Feld unter „Notausgang“ einfügen → Einreichen.

## 4. Wenn du „Manage Extensibility“ nicht siehst

Dann kann nur eure Brightspace-Administration die Anwendung registrieren. Dafür braucht
sie exakt die Angaben aus Schritt 1 und gibt dir danach Client-ID und Client-Secret.
Textbaustein:

> Hallo …,
>
> ich möchte meine Brightspace-Kurse mit einem Werkzeug befüllen, das über die
> offizielle Valence-API arbeitet (bskitool, Open Source, läuft nur lokal auf meinem
> Rechner). Dafür bräuchte ich eine OAuth-2.0-Anwendung unter Admin-Tools → Manage
> Extensibility → OAuth 2.0 → Register an app mit diesen Werten:
>
> - Application Name: bskitool – <mein Name>
> - Redirect URI: https://localhost:8080/callback
> - Scope: core:*:* content:*:* grades:*:* dropbox:*:*
> - Refresh tokens: aktiviert
>
> Die Anwendung handelt ausschließlich mit meinen eigenen Rechten in meinen eigenen
> Kursen; sie bekommt keine zusätzlichen Berechtigungen. Ich bräuchte danach Client-ID
> und Client-Secret.
>
> Danke!

Manche Schulen vergeben statt Wildcards (`core:*:*`) genauere Scopes. Dann muss die
Scope-Zeile in bskitool genau der registrierten entsprechen. Was bskitool mindestens
braucht:

| Funktion | Scope |
|---|---|
| Anmeldung, Kursliste | `core:*:*` (mindestens `users:userdata:read`, `enrollment:orgunit:read`, `organizations:organization:read`) |
| Module, Seiten, Dateien, Links, Inhaltsverzeichnis, Löschen | `content:*:*` |
| Notenelemente | `grades:*:*` |
| Abgabeordner | `dropbox:*:*` |
| Quiz-Hüllen (optional) | `quizzing:*:*` |

## 5. Port 8080 ist belegt?

Dann läuft auf deinem Rechner schon etwas auf diesem Port (oft ein Entwicklungsserver).
Entweder das Programm beenden – oder eine andere Redirect-URI wählen, z. B.
`https://localhost:8443/callback`. Die muss dann **in Brightspace und in bskitool**
gleich eingetragen sein.

## 6. Mehrere Lehrkräfte, eine Schule

Jede Lehrkraft registriert ihre eigene Anwendung (oder bekommt von der Admin eine mit
eigenem Secret). Ein gemeinsames Secret ist technisch möglich, aber dann arbeiten alle
mit demselben Schlüssel – nicht empfehlenswert. Die Anwendung handelt immer mit den
Rechten der Person, die sich anmeldet.
