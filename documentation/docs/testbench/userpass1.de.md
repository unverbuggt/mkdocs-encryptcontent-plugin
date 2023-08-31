title: Benutzername / Passwort 1
level: user_and_passwords1
inject_id: protected
delete_id: teaser

/// html | div#teaser

Es ist möglich diese Seite mit einem der folgenden Benutzername/Passwort Kombinationen zu entschlüsseln:

- alice: nimbleness
- bob: virus
- carol: gathering
- carlos: canister
- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

Wenn einer der unteren vier Benutzer eingegeben wird, dann wird auch [Benutzername/Passwort 2](userpass2.md) entschlüsselt.

///
/// html | div#protected

<h1>Seite entschlüsselt</h1>

Eines dieser Benutzername/Passwort Kombinationen **wurde** verwendet um diese Seite zu entschlüsseln:

- alice: nimbleness
- bob: virus
- carol: gathering
- carlos: canister
- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

Wenn einer der untersten vier Benutzer eingegeben wurde, dann kann auch [Benutzername/Passwort 2](userpass2.md)
entschlüsselt werden.

<script id="autostart">
const ctheme = 'css/w3-theme-44bb4f-mono';
document.getElementById('theme-auto').href = base_url + '/' + ctheme + '.css';
document.getElementById('theme-light').href = base_url + '/' + ctheme + '-light.css';
document.getElementById('theme-dark').href = base_url + '/' + ctheme + '-dark.css';
</script>
///