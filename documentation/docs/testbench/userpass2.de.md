title: Benutzername / Passwort 2
level: user_and_passwords2
inject_id: protected
delete_id: teaser

/// html | div#teaser

Es ist möglich diese Seite mit einem der folgenden Benutzername/Passwort Kombinationen zu entschlüsseln:

- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

Wenn einer dieser Benutzer eingegeben wurde, dann wird auch [Benutzername/Passwort 1](userpass1.md) entschlüsselt.

///
/// html | div#protected

<h1>Seite entschlüsselt</h1>

Eines dieser Benutzername/Passwort Kombinationen **wurde** verwendet um diese Seite zu entschlüsseln:

- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

Nun kann auch [Benutzername/Passwort 1](userpass1.md) entschlüsselt werden.

<script id="autostart">
const ctheme = 'css/w3-theme-44bb4f-mono';
document.getElementById('theme-auto').href = base_url + '/' + ctheme + '.css';
document.getElementById('theme-light').href = base_url + '/' + ctheme + '-light.css';
document.getElementById('theme-dark').href = base_url + '/' + ctheme + '-dark.css';
</script>
///