title: User / Password 1
level: user_and_passwords1
inject_id: protected
delete_id: teaser

/// html | div#teaser

The following user/passwords are valid to decrypt this page:

- alice: nimbleness
- bob: virus
- carol: gathering
- carlos: canister
- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

If you use one of the last four users, you'd also be able to decrypt [User/Password 2](userpass2.md).

///
/// html | div#protected

<h1>Page decrypted</h1>

One of the following user/passwords **were** used to decrypt this page:

- alice: nimbleness
- bob: virus
- carol: gathering
- carlos: canister
- charlie: hazelnut
- dan: apple
- dave: oxidize
- david: palm

If you used one of the last four users, you'd also be able to decrypt [User/Password 2](userpass2.md).

<script id="autostart">
const ctheme = 'css/w3-theme-44bb4f-mono';
document.getElementById('theme-auto').href = base_url + '/' + ctheme + '.css';
document.getElementById('theme-light').href = base_url + '/' + ctheme + '-light.css';
document.getElementById('theme-dark').href = base_url + '/' + ctheme + '-dark.css';
</script>
///