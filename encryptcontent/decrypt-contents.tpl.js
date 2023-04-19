/* encryptcontent/decrypt-contents.tpl.js */

/* Decrypts the key from the key bundle. */
function decrypt_key(password, iv_b64, ciphertext_b64, salt_b64) {
    let salt = CryptoJS.enc.Base64.parse(salt_b64),
        kdfcfg = {keySize: 256 / 32,hasher: CryptoJS.algo.SHA256,iterations: encryptcontent_obfuscate ? 1 : {{ kdf_iterations }}};
    let kdfkey = CryptoJS.PBKDF2(encodeURIComponent(password), salt,kdfcfg);
    let iv = CryptoJS.enc.Base64.parse(iv_b64),
        ciphertext = CryptoJS.enc.Base64.parse(ciphertext_b64);
    let encrypted = {ciphertext: ciphertext},
        cfg = {iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7};
    let key = CryptoJS.AES.decrypt(encrypted, kdfkey, cfg);
    if (key.sigBytes == 32) {
        return key.toString(CryptoJS.enc.Hex);
    } else {
        return false;
    }
};

/* Split key bundle and try to decrypt it */
function decrypt_key_from_bundle(password, ciphertext_bundle) {
    // grab the ciphertext bundle and try to decrypt it
    if (ciphertext_bundle) {
        let parts = ciphertext_bundle.split(';');
        if (parts.length == 3) {
            return decrypt_key(password, parts[0], parts[1], parts[2]);
        }
    }
    return false;
};

/* Decrypts the content from the ciphertext bundle. */
function decrypt_content(key, iv_b64, ciphertext_b64) {
    let iv = CryptoJS.enc.Base64.parse(iv_b64),
        ciphertext = CryptoJS.enc.Base64.parse(ciphertext_b64);
    let encrypted = {ciphertext: ciphertext},
        cfg = {iv: iv, mode: CryptoJS.mode.CBC, padding: CryptoJS.pad.Pkcs7};
    let plaintext = CryptoJS.AES.decrypt(encrypted, CryptoJS.enc.Hex.parse(key), cfg);
    if(plaintext.sigBytes >= 0) {
        try {
            return plaintext.toString(CryptoJS.enc.Utf8)
        } catch (err) {
            // encoding failed; wrong key
            return false;
        }
    } else {
        // negative sigBytes; wrong key
        return false;
    }
};

/* Split cyphertext bundle and try to decrypt it */
function decrypt_content_from_bundle(key, ciphertext_bundle) {
    // grab the ciphertext bundle and try to decrypt it
    if (ciphertext_bundle) {
        let parts = ciphertext_bundle.split(';');
        if (parts.length == 2) {
            return decrypt_content(key, parts[0], parts[1]);
        }
    }
    return false;
};

{% if remember_password -%}
/* Set key:value in sessionStorage/localStorage */
function setItem(key, value) {
    {% if session_storage -%}
    sessionStorage.setItem('encryptcontent_' + encodeURIComponent(key), encodeURIComponent(value))
    {%- else %}
    localStorage.setItem('encryptcontent_' + encodeURIComponent(key), encodeURIComponent(value))
    {%- endif %}
};

/* Delete key with specific name in sessionStorage/localStorage */
function delItemName(key) {
    {% if session_storage -%}
    sessionStorage.removeItem('encryptcontent_' + encodeURIComponent(key));
    {%- else %}
    localStorage.removeItem('encryptcontent_' + encodeURIComponent(key));
    {%- endif %}
};

function getItem(key) {
    {% if session_storage -%}
    return sessionStorage.getItem(key);
    {%- else %}
    return localStorage.getItem(key);
    {%- endif %}
};

/* Get key:value from sessionStorage/localStorage */
function getItemFallback(key) {
    let ret = {
        value: null,
        fallback: false
    };
    let item_value;
    item_value = getItem('encryptcontent_' + encodeURIComponent(key));
    if (!item_value) {
        ret.fallback = true; //fallback is set to not display a "decryption failed" message
        // fallback one level up
        let last_slash = key.slice(0, -1).lastIndexOf('/')
        if (last_slash !== -1 && last_slash > 0) {
            let keyup = key.substring(0,last_slash+1);
            item_value = getItem('encryptcontent_' + encodeURIComponent(keyup));
        }
        if (!item_value) {
            // fallback site_path
            item_value = getItem('encryptcontent_' + encodeURIComponent("{{ site_path }}"));
            if (!item_value) {
                // fallback global
                item_value = getItem('encryptcontent_');
                if (!item_value) {
                    //no password saved and no fallback found
                    return null;
                }
            }
        }
    }
    ret.value = decodeURIComponent(item_value);
    return ret;
};
{%- endif %}

/* Reload scripts src after decryption process */
function reload_js(src) {
    let script_src, script_tag, new_script_tag;
    let head = document.getElementsByTagName('head')[0];

    if (src.startsWith('#')) {
        script_tag = document.getElementById(src.substr(1));
        if (script_tag) {
            script_tag.remove();
            new_script_tag = document.createElement('script');
            if (script_tag.innerHTML) {
                new_script_tag.innerHTML = script_tag.innerHTML;
            }
            if (script_tag.src) {
                new_script_tag.src = script_tag.src;
            }
            head.appendChild(new_script_tag);
        }
    } else {
        if (base_url == '.') {
            script_src = src;
        } else {
            script_src = base_url + '/' + src;
        }

        script_tag = document.querySelector('script[src="' + script_src + '"]');
        if (script_tag) {
            script_tag.remove();
            new_script_tag = document.createElement('script');
            new_script_tag.src = script_src;
            head.appendChild(new_script_tag);
        }
    }
};

{% if experimental -%}
/* Decrypt part of the search index and refresh it for search engine */
function decrypt_search(key, path_location) {
    sessionIndex = sessionStorage.getItem('encryptcontent-index');
    let could_decrypt = false;
    if (sessionIndex) {
        sessionIndex = JSON.parse(sessionIndex);
        for (var i=0; i < sessionIndex.docs.length; i++) {
            var doc = sessionIndex.docs[i];
            if (doc.location.indexOf(path_location.replace('{{ site_path }}', '')) !== -1) {
                // grab the ciphertext bundle and try to decrypt it
                let title = decrypt_content_from_bundle(key, doc.title);
                if (title !== false) {
                    could_decrypt = true;
                    doc.title = title;
                    // any post processing on the decrypted search index should be done here
                    let content = decrypt_content_from_bundle(key, doc.text);
                    if (content !== false) {
                        doc.text = content;
                        let location_bundle = doc.location;
                        let location_sep = location_bundle.indexOf(';')
                        if (location_sep !== -1) {
                            let toc_bundle = location_bundle.substring(location_sep+1)
                            let location_doc = location_bundle.substring(0,location_sep)
                            let toc_url = decrypt_content_from_bundle(key, toc_bundle);
                            if (toc_url !== false) {
                                doc.location = location_doc + toc_url;
                            }
                        }
                    }
                }
            }
        }
        if (could_decrypt) {
            //save decrypted index
            sessionIndex = JSON.stringify(sessionIndex);
            sessionStorage.setItem('encryptcontent-index', sessionIndex);
            // force search index reloading on Worker
            if (typeof searchWorker !== 'undefined') {
                searchWorker.postMessage({init: true, sessionIndex: sessionIndex});
            } else { //not default search plugin: reload whole page
                window.location.reload();
            }
        }
    }
};
{%- endif %}

/* Decrypt speficique html entry from mkdocs configuration */
function decrypt_somethings(key, encrypted_something) {
    var html_item = '';
    for (const [name, tag] of Object.entries(encrypted_something)) {
        if (tag[1] == 'id') {
            html_item = [document.getElementById(name)];
        } else if (tag[1] == 'class') {
            html_item = document.getElementsByClassName(name);
        } else {
            console.log('WARNING: Unknow tag html found, check "encrypted_something" configuration.');
        }
        if (html_item[0]) {
            for (i = 0; i < html_item.length; i++) {
                // grab the cipher bundle if something exist
                let content = decrypt_content_from_bundle(key, html_item[i].innerHTML);
                if (content !== false) {
                    // success; display the decrypted content
                    html_item[i].innerHTML = content;
                    html_item[i].style.display = null;
                    // any post processing on the decrypted content should be done here
                }
            }
        }
    }
};

/* Decrypt content of a page */
function decrypt_action(password_input, encrypted_content, decrypted_content, key_from_storage) {
    // grab the ciphertext bundle
    // and decrypt it
    let key;
    if (key_from_storage !== false) {
        key = key_from_storage;
    } else {
        key = decrypt_key_from_bundle(password_input.value, encryptcontent_keystore);
    }
    let content = false;
    if (key) {
        content = decrypt_content_from_bundle(key, encrypted_content.innerHTML);
    }
    if (content !== false) {
        // success; display the decrypted content
        decrypted_content.innerHTML = content;
        // encrypted_content.parentNode.removeChild(encrypted_content);
        // any post processing on the decrypted content should be done here
        {% if arithmatex -%}
        if (typeof MathJax === 'object') { MathJax.typesetPromise(); };
        {%- endif %}
        {% if mermaid2 -%}
        if (typeof mermaid === 'object') { mermaid.contentLoaded(); };
        {%- endif %}
        {% if hljs -%}
        document.getElementById("mkdocs-decrypted-content").querySelectorAll('pre code').forEach((block) => {
            hljs.highlightBlock(block);
        });
        {%- endif %}
        {% if reload_scripts | length > 0 -%}
        let reload_scripts = {{ reload_scripts }};
        for (i = 0; i < reload_scripts.length; i++) { 
            reload_js(reload_scripts[i]);
        }
        {%- endif %}
        return key
    } else {
        return false
    }
};

function decryptor_reaction(key, password_input, fallback_used, set_global, save_cookie) {
    let location_path;
    if (set_global) {
        location_path = "/{{ site_path}}"; //global password decrypts at "/{site_path}"
    } else {
        location_path = encryptcontent_path;
    }
    if (key) {
        {% if remember_password -%}
        // keep password value on sessionStorage/localStorage with specific path (relative)
        if (set_global) {
            setItem("", key);
        }
        else if (!fallback_used) {
            setItem(location_path, key);
        }
        {%- endif %}
        // continue to decrypt others parts
        {% if experimental -%}
        decrypt_search(key, location_path);
        {%- endif %}
        {% if encrypted_something -%}
        let encrypted_something = {{ encrypted_something }};
        decrypt_somethings(key, encrypted_something);
        {%- endif %}
    } else {
        // remove item on sessionStorage/localStorage if decryption process fail (Invalid item)
        if (!fallback_used || set_global) {
            if (!encryptcontent_obfuscate) {
                // create HTML element for the inform message
                let mkdocs_decrypt_msg = document.getElementById('mkdocs-decrypt-msg');
                mkdocs_decrypt_msg.textContent = decryption_failure_message;
                password_input.value = '';
                password_input.focus();
            }
            {% if remember_password -%}
            delItemName(location_path);
            {%- endif %}
        }
    }
}

/* Trigger decryption process */
function init_decryptor() {
    var password_input = document.getElementById('mkdocs-content-password');
    // adjust password field width to placeholder length
    if (password_input.hasAttribute('placeholder')) {
        password_input.setAttribute('size', password_input.getAttribute('placeholder').length);
    }
    var encrypted_content = document.getElementById('mkdocs-encrypted-content');
    var decrypted_content = document.getElementById('mkdocs-decrypted-content');
    {% if remember_password -%}
    /* If remember_password is set, try to use sessionStorage/localstorage item to decrypt content when page is loaded */
    let key_from_storage = getItemFallback(encryptcontent_path);
    if (key_from_storage) {
        let content_decrypted = decrypt_action(
            password_input, encrypted_content, decrypted_content, key_from_storage.value
        );
        decryptor_reaction(content_decrypted, password_input, key_from_storage.fallback, false, false); //dont save cookie as it was loaded from cookie
    }
    {%- endif %}
    {% if password_button -%}
    /* If password_button is set, try decrypt content when button is press */
    let decrypt_button = document.getElementById("mkdocs-decrypt-button");
    if (decrypt_button) {
        decrypt_button.onclick = function(event) {
            event.preventDefault();
            let content_decrypted = decrypt_action(
                password_input, encrypted_content, decrypted_content, false
            );
            decryptor_reaction(content_decrypted, password_input, false, false, true); //no fallback, save cookie
        };
    }
    {%- endif %}
    /* Default, try decrypt content when key (ctrl) enter is press */
    password_input.addEventListener('keypress', function(event) {
        let set_global = false;
        if (event.key === "Enter") {
            if (event.ctrlKey) {
                set_global = true;
            }
            event.preventDefault();
            let content_decrypted = decrypt_action(
                password_input, encrypted_content, decrypted_content, false
            );
            decryptor_reaction(content_decrypted, password_input, false, set_global, true); //no fallback, set_global?, save cookie
        }
    });
}

document.addEventListener('DOMContentLoaded', init_decryptor());
