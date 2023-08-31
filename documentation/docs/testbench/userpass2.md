title: User / Password 2
level: user_and_passwords2
inject_id: protected
delete_id: teaser

/// html | div#teaser

The following user/passwords are valid to decrypt this page:

- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

If you use one of these users, you'd also be able to decrypt [User/Password 1](userpass1.md).

///
/// html | div#protected

<h1>Page decrypted</h1>

One of the following passwords **were** used to decrypt this page:

- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

You're also able to decrypt [User/Password 1](userpass1.md).

<script id="autostart">
const ctheme = 'css/w3-theme-44bb4f-mono';
document.getElementById('theme-auto').href = base_url + '/' + ctheme + '.css';
document.getElementById('theme-light').href = base_url + '/' + ctheme + '-light.css';
document.getElementById('theme-dark').href = base_url + '/' + ctheme + '-dark.css';
</script>
///