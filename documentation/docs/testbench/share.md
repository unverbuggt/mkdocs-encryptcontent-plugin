title: Encode share link

# Various tests

[Test1a (user: dave)](userpass1.md#IWRhdmV-b3hpZGl6ZQ)\
[Test1b (user: dave)](userpass1.md#!dave~oxidize)

[Test2a (user: dave, go to anchor-6)](anchor.md#IWRhdmV-b3hpZGl6ZQ#anchor-6)\
[Test2b (user: dave, go to anchor-6)](anchor.md#!dave~oxidize#anchor-6)

[Test3 (password: squirrel)](onlypasswords2.md#IX5zcXVpcnJlbA)

[Test4 (obfuscate: Crawler be gone!)](obfuscate.md#IX5DcmF3bGVyIGJlIGdvbmUh)

# Create share link

<div class="w3-row-padding" style="padding-left: 0px;">
  <div class="w3-third">
    <label for="share-user">username</label>
    <input class="w3-input w3-border w3-hover-theme w3-theme-l1" name="share-user" id="share-user" type="text" value="dave" onchange="genB64Url();">
  </div>
  <div class="w3-third">
    <label for="share-pass">password</label>
    <input class="w3-input w3-border w3-hover-theme w3-theme-l1" name="share-pass" id="share-pass" type="text" value="oxidize" onchange="genB64Url();">
  </div>
</div>

<div class="w3-row-padding w3-margin-top" style="padding-left: 0px;">
  <div class="w3-twothird">
    <label for="share-output">output</label>
    <input class="w3-input w3-border w3-hover-theme w3-theme-l1" name="share-output" id="share-output" type="text" onchange="decB64Url();">
    <div id="output-length"></div>
  </div>
</div>

<div class="w3-row-padding w3-margin-top" style="padding-left: 0px;">
  <div class="w3-twothird">
    <label for="share-decode">decoded</label>
    <code name="share-decode" id="share-decode" type="text"></code>
    <div id="decode-length"></div>
  </div>
</div>

<div class="w3-row-padding w3-margin-top" style="padding-left: 0px;">
  <div class="w3-twothird">
    <label for="share-url">url encoded</label>
    <code name="share-url" id="share-url" type="text"></code>
    <div id="url-length"></div>
  </div>
</div>

<script>
var share_user = document.getElementById('share-user');
var share_pass = document.getElementById('share-pass');
var share_output = document.getElementById('share-output');
var share_decode = document.getElementById('share-decode');
var share_url = document.getElementById('share-url');
var output_length = document.getElementById('output-length');
var decode_length = document.getElementById('decode-length');
var url_length = document.getElementById('url-length');


//https://developer.mozilla.org/en-US/docs/Glossary/Base64#the_unicode_problem
function base64ToBytes(base64) {
  const binString = atob(base64);
  return Uint8Array.from(binString, (m) => m.codePointAt(0));
}

function bytesToBase64(bytes) {
  const binString = Array.from(bytes, (x) => String.fromCodePoint(x)).join("");
  return btoa(binString);
}

function base64url_decode(input) {
    try {
        return new TextDecoder().decode(base64ToBytes(input.replace(/-/g, '+').replace(/_/g, '/')));
    }
    catch (err) {
        return "!ERROR!";
    }
}
function base64url_encode(input) {
    try {
        return bytesToBase64(new TextEncoder().encode(input)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }
    catch (err) {
        return "!ERROR!";
    }
}


function genB64Url() {
    const str = "!" + share_user.value + "~" + share_pass.value;
    let encstr = base64url_encode(str);
    share_output.value = '#' + encstr;
    decB64Url()
}

function decB64Url() {
    let encstr = share_output.value.substr(1);
    output_length.innerHTML = "length: " + encstr.length;
    let decstr = base64url_decode(encstr)
    share_decode.textContent = decstr;
    decode_length.innerHTML = "length: " + decstr.length;
    share_url.textContent = '#' + encodeURIComponent(share_user.value) + "~" + encodeURIComponent(share_pass.value);
    url_length.innerHTML = "length: " + share_url.textContent.length;
}
genB64Url();

</script>

# Sharelinks output

sharelinks.txt

```
{% include "../../sharelinks.txt" %}
```
