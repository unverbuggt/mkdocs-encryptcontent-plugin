var base_path = 'function' === typeof importScripts ? '.' : '/search/';
var allowSearch = false;
var index;
var documents = {};
var lang = ['en'];
var data;
var session_storage;

function getScript(script, callback) {
  console.log('Loading script: ' + script);
  $.getScript(base_path + script).done(function () {
    callback();
  }).fail(function (jqxhr, settings, exception) {
    console.log('Error: ' + exception);
  });
}

function getScriptsInOrder(scripts, callback) {
  if (scripts.length === 0) {
    callback();
    return;
  }
  getScript(scripts[0], function() {
    getScriptsInOrder(scripts.slice(1), callback);
  });
}

function loadScripts(urls, callback) {
  if( 'function' === typeof importScripts ) {
    importScripts.apply(null, urls);
    callback();
  } else {
    getScriptsInOrder(urls, callback);
  }
}

function onJSONLoaded () {
  data = JSON.parse(this.responseText);
  var eReq = new XMLHttpRequest();
  eReq.addEventListener("load", onEncryptedJSONLoaded);
  eReq.addEventListener("error", getScripts);
  var index_path = base_path + '/encrypted_index.json';
  if( 'function' === typeof importScripts ){
    index_path = 'encrypted_index.json';
  }
  eReq.open("GET", index_path);
  eReq.send();
}



function fromBase64(base64String) { // https://stackoverflow.com/a/41106346
    return Uint8Array.from(atob(base64String), c => c.charCodeAt(0));
}

/* Split cyphertext bundle and try to decrypt it */
async function decrypt_content_from_bundle(key, ciphertext_bundle) {
  // grab the ciphertext bundle and try to decrypt it
  if (ciphertext_bundle) {
    let parts = ciphertext_bundle.split(';');
    if (parts.length == 2) {
      return await decrypt_content(key, parts[0], parts[1]);
    }
  }
  return false;
};

/* Decrypts the content from the ciphertext bundle. */
async function decrypt_content(key, iv_b64, ciphertext_b64) {
    const iv = fromBase64(iv_b64);
    const ciphertext = fromBase64(ciphertext_b64);
    try {
        const decrypted = await crypto.subtle.decrypt(
            {
                name: "AES-CBC",
                iv: iv
            },
            key,
            ciphertext
        );
        const decoder = new TextDecoder();
        return decoder.decode(decrypted);
    }
    catch (err) {
        // encoding failed; wrong key
        return false;
    }
};

async function onEncryptedJSONLoaded () {
  let encrypted_docs = JSON.parse(this.responseText);
  let requested_keys = [];
  let keys = {};
  console.log('called onEncryptedJSONLoaded();');
  for (let i = 0; i < encrypted_docs.length; i++) {
    let doc = encrypted_docs[i];
    let location_sep = doc.location.indexOf(';');
    if (location_sep !== -1) {
      let location_id = doc.location.substring(0,location_sep);
      let location_bundle = doc.location.substring(location_sep+1);
      if (!(location_id in requested_keys)) {
        requested_keys.push(location_id);
        if (location_id in session_storage) {
          let key = await getKey(session_storage[location_id]);
          keys[location_id] = key;
        }
      }
      if (location_id in keys) {
        let key = keys[location_id];
        let location_decrypted = await decrypt_content_from_bundle(key, location_bundle);
        if (location_decrypted) {
          doc.location = location_decrypted;
          doc.text = await decrypt_content_from_bundle(key, doc.text);
          doc.title = await decrypt_content_from_bundle(key, doc.title);
          console.log(doc);
        }
      }
    }
  }
  getScripts();
}

function getScripts () {
  var scriptsToLoad = ['lunr.js'];
  if (data.config && data.config.lang && data.config.lang.length) {
    lang = data.config.lang;
  }
  if (lang.length > 1 || lang[0] !== "en") {
    scriptsToLoad.push('lunr.stemmer.support.js');
    if (lang.length > 1) {
      scriptsToLoad.push('lunr.multi.js');
    }
    if (lang.includes("ja") || lang.includes("jp")) {
      scriptsToLoad.push('tinyseg.js');
    }
    for (var i=0; i < lang.length; i++) {
      if (lang[i] != 'en') {
        scriptsToLoad.push(['lunr', lang[i], 'js'].join('.'));
      }
    }
  }
  loadScripts(scriptsToLoad, onScriptsLoaded);
}

function onScriptsLoaded () {
  console.log('All search scripts loaded, building Lunr index...');
  if (data.config && data.config.separator && data.config.separator.length) {
    lunr.tokenizer.separator = new RegExp(data.config.separator);
  }

  if (data.index) {
    index = lunr.Index.load(data.index);
    data.docs.forEach(function (doc) {
      documents[doc.location] = doc;
    });
    console.log('Lunr pre-built index loaded, search ready');
  } else {
    index = lunr(function () {
      if (lang.length === 1 && lang[0] !== "en" && lunr[lang[0]]) {
        this.use(lunr[lang[0]]);
      } else if (lang.length > 1) {
        this.use(lunr.multiLanguage.apply(null, lang));  // spread operator not supported in all browsers: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_operator#Browser_compatibility
      }
      this.field('title');
      this.field('text');
      this.ref('location');

      for (var i=0; i < data.docs.length; i++) {
        var doc = data.docs[i];
        this.add(doc);
        documents[doc.location] = doc;
      }
    });
    console.log('Lunr index built, search ready');
  }
  allowSearch = true;
  postMessage({config: data.config});
  postMessage({allowSearch: allowSearch});
}

function init (sessionStorage) {
  session_storage = sessionStorage;
  var oReq = new XMLHttpRequest();
  oReq.addEventListener("load", onJSONLoaded);
  var index_path = base_path + '/search_index.json';
  if( 'function' === typeof importScripts ){
      index_path = 'search_index.json';
  }
  oReq.open("GET", index_path);
  oReq.send();
}

function search (query) {
  if (!allowSearch) {
    console.error('Assets for search still loading');
    return;
  }

  var resultDocuments = [];
  var results = index.search(query);
  for (var i=0; i < results.length; i++){
    var result = results[i];
    doc = documents[result.ref];
    doc.summary = doc.text.substring(0, 200);
    resultDocuments.push(doc);
  }
  return resultDocuments;
}

if( 'function' === typeof importScripts ) {
  onmessage = function (e) {
    if (e.data.init) {
      init(e.data.session_storage);
    } else if (e.data.query) {
      postMessage({ results: search(e.data.query) });
    } else {
      console.error("Worker - Unrecognized message: " + e);
    }
  };
}
