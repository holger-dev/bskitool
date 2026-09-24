# Fehlersuche

Jede Zeile im Protokoll hat eine Markierung: `[ok]`, `[trocken]`, `[hinweis]`,
`[fehler]`. Bei `[fehler]` steht dahinter die Antwort von Brightspace. Die häufigsten
Fälle:

## Start und Oberfläche

**„python3: command not found“ / „Python fehlt“**
Python ist nicht installiert oder (Windows) nicht im PATH. Installer von python.org,
Haken „Add python.exe to PATH“. Danach die Startdatei erneut doppelklicken.

**Mac: „bskitool starten.command kann nicht geöffnet werden“**
Rechtsklick → Öffnen → Öffnen. Nur beim ersten Mal. Alternativ im Terminal:
`chmod +x "bskitool starten.command"`.

**Browser zeigt „Verbindung abgelehnt“ auf localhost:8765**
Der Server läuft nicht mehr (Terminalfenster geschlossen?). Neu starten. Ist Port 8765
belegt, nimmt bskitool automatisch den nächsten freien und zeigt ihn im Terminal an.

**Kursdatei taucht nicht in der Liste auf**
Sie muss unter `kurse/` liegen und auf `.md` enden. „Neu einlesen“ klicken. Dateien
namens `README.md`/`LIESMICH.md` werden absichtlich ignoriert.

## Anmeldung

**„Client-ID und Client-Secret fehlen“**
Einstellungen ausfüllen und **Speichern** klicken – erst dann ist die Anmeldung möglich.

**Brightspace: „invalid_scope“ oder „Brightspace lehnt ab“**
Die Scope-Zeile in bskitool weicht von der registrierten ab. Sie muss zeichengenau
gleich sein – auch die Reihenfolge und die Leerzeichen. Mehr anfragen als registriert
ist, lehnt Brightspace ab. → OAUTH-EINRICHTEN.md

**Brightspace: „redirect_uri mismatch“**
Redirect-URI in bskitool und in Brightspace müssen identisch sein, inklusive `https://`
und `/callback`.

**Browser: „Diese Verbindung ist nicht privat“ nach der Bestätigung**
Normal – das ist das selbst erzeugte Zertifikat für localhost. Erweitert → Weiter zu
localhost. Bei Safari: Details einblenden → Diese Website öffnen.

**Anmeldung wartet endlos**
Steht im Browser `…/callback?code=…`? Adresse komplett kopieren → Notausgang-Feld →
Einreichen. Steht dort nichts: Port 8080 belegt? (Terminal: `lsof -i :8080` auf Mac,
`netstat -ano | findstr 8080` auf Windows.) → andere Redirect-URI, in Brightspace und
bskitool.

**„Die Anmeldung ist abgelaufen – bitte neu anmelden“**
Das Refresh-Token ist ungültig (nach längerer Pause oder wenn die Anwendung in
Brightspace geändert wurde). Einfach neu anmelden.

**„openssl konnte kein Zertifikat erzeugen“**
Auf Mac/Linux ist `openssl` normalerweise da. Auf Windows: mit Git for Windows kommt es
mit (`C:\Program Files\Git\usr\bin` in den PATH), oder eine http-Redirect-URI verwenden,
falls eure Brightspace-Instanz das erlaubt (viele erlauben nur https).

## Einspielen

**403 „Insufficient scope to call API. Required: …“**
Der genannte Scope fehlt der Anwendung. In Brightspace ergänzen, in den Einstellungen
ergänzen, abmelden, neu anmelden. Häufig: `quizzing:*:*` für Quiz-Hüllen – das ist
optional, alles andere wird trotzdem angelegt.

**403 ohne Scope-Meldung**
Dein Konto hat in diesem Kurs nicht die Rechte (z. B. Rolle „Beobachter“). Die API
kann nur, was du in Brightspace auch von Hand könntest.

**400 „JSON Binding Error“ / „Provided JSON is invalid“**
Ein Feld in der Anfrage passt nicht zur API-Version eurer Instanz. Bitte die komplette
Protokollzeile als Issue melden – das ist meist mit einer Zeile behoben. Zwischenlösung:
in den Einstellungen `v_le` bzw. `v_lp` auf die Version setzen, die
„Erreichbarkeit prüfen“ als neueste anzeigt.

**400 `{"Errors": []}` bei Seiten oder Dateien**
Der Kursinhalt-Pfad stimmt nicht. bskitool liest ihn aus dem Kursobjekt; die Zeile
`[Url war …]` zeigt, was gesendet wurde. Erwartet wird etwas wie
`/content/enforced/12345-KURSCODE/datei.html`. Mit `python3 bskitool.py themen <orgUnitId>`
siehst du den Pfad, den bskitool ermittelt.

**Notenelement: „Name … enthält unzulässige Zeichen“ oder 400**
Brightspace erlaubt in Notennamen kein `/ " * < > + = | , %`. bskitool ersetzt diese
Zeichen automatisch (`+` → „und“). Wenn zwei Titel dadurch gleich werden, meldet
Brightspace einen doppelten Namen – Titel in der kurs.md anpassen.

**Abgabeordner „ohne Punkte/Notenverknüpfung angelegt“**
Eure Instanz nimmt die Bewertungsfelder beim Anlegen nicht an (ältere API-Version).
Punkte und Notenelement in Brightspace beim Abgabeordner nachtragen; die
Noch-zu-tun-Liste erinnert daran.

**Datei-Upload bricht ab bei großen Dateien**
Multipart-Uploads über 50 MB sind unzuverlässig. Große Dateien (Videos!) gehören nicht
in den Kurs, sondern in einen Videodienst; im Kurs dann `## Link:`.

**Alles doppelt im Kurs**
Zweimal eingespielt. **Letztes Einspielen rückgängig** entfernt den letzten Lauf;
für ältere Läufe der Reiter Aufräumen.

## Netzwerk

**„… nicht erreichbar“ bei Erreichbarkeit prüfen**
Bist du im Netz? Stimmt die Adresse (ohne `https://`, ohne Pfad)? Manche Schulnetze
und Firmenproxys blockieren die API-Pfade `/d2l/api/…`, obwohl die Weboberfläche geht.
Von zu Hause oder über Handy-Hotspot testen. Wenn es dort geht, ist es der Proxy –
dann bleibt der .imscc-Export als Weg.

**Proxy mit eigenem Zertifikat (Schul-Firewall)**
Python vertraut dem Proxy-Zertifikat nicht → „CERTIFICATE_VERIFY_FAILED“. Auf dem Mac
`/Applications/Python 3.x/Install Certificates.command` ausführen; sonst das
Schul-Zertifikat in den Python-Zertifikatsspeicher aufnehmen (IT fragen).

## Rückfallweg: .imscc

Wenn die API nicht will: **Als .imscc exportieren** → Brightspace: Kursverwaltung →
Import/Export/Kopieren → Komponenten importieren → Datei hochladen. Erfahrungen:

- Module, HTML-Seiten (inkl. Selbstchecks) und Abgabeordner kommen an.
- Dateianhänge kommen **nicht** mit → per Drag & Drop ins Modul ziehen.
- QTI-Quizze erscheinen nicht als Quizze → Fragen-CSV aus `ausgabe/<kurs>/fragen/`
  in die Fragensammlung importieren.
- Notenelemente gibt es im Format nicht → von Hand anlegen.
