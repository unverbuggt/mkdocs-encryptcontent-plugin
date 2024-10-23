function getSearchTermFromLocation() {
  var sPageURL = window.location.search.substring(1);
  var sURLVariables = sPageURL.split('&');
  for (var i = 0; i < sURLVariables.length; i++) {
    var sParameterName = sURLVariables[i].split('=');
    if (sParameterName[0] == 'q') {
      return decodeURIComponent(sParameterName[1].replace(/\+/g, '%20'));
    }
  }
}

function joinUrl (base, path) {
  if (path.substring(0, 1) === "/") {
    // path starts with `/`. Thus it is absolute.
    return path;
  }
  if (base.substring(base.length-1) === "/") {
    // base ends with `/`
    return base + path;
  }
  return base + "/" + path;
}

function escapeHtml (value) {
  return value.replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function formatResult (location, title, summary) {
  return '<article><h3><a href="' + joinUrl(base_url, location) + '">'+ escapeHtml(title) + '</a></h3><p>' + escapeHtml(summary) +'</p></article>';
}

function displayResults (results) {
  var search_results = document.getElementById("mkdocs-search-results");
  while (search_results.firstChild) {
    search_results.removeChild(search_results.firstChild);
  }
  if (results.length > 0){
    for (var i=0; i < results.length; i++){
      var result = results[i];
      var html = formatResult(result.location, result.title, result.summary);
      search_results.insertAdjacentHTML('beforeend', html);
    }
  } else {
    var noResultsText = search_results.getAttribute('data-no-results-text');
    if (!noResultsText) {
      noResultsText = "No results found";
    }
    search_results.insertAdjacentHTML('beforeend', '<p>' + noResultsText + '</p>');
  }
}

function doSearch () {
  var query = document.getElementById('mkdocs-search-query').value;
  if (query.length > min_search_length) {
    if (!window.Worker) {
      displayResults(search(query));
    } else {
      searchWorker.postMessage({query: query});
    }
  } else {
    // Clear results for short queries
    displayResults([]);
  }
}

function initSearch () {
  var search_input = document.getElementById('mkdocs-search-query');
  if (search_input) {
    search_input.addEventListener("keyup", doSearch);
  }
  var term = getSearchTermFromLocation();
  if (term) {
    search_input.value = term;
    doSearch();
  }
}

function onWorkerMessage (e) {
  if (e.data.allowSearch) {
    initSearch();
  } else if (e.data.results) {
    var results = e.data.results;
    displayResults(results);
  } else if (e.data.config) {
    min_search_length = e.data.config.min_search_length-1;
  }
}

if (!window.hasOwnProperty("init_decryptor")) {

  function fromHex(hexString) { // https://stackoverflow.com/a/50868276
    return new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
  }

  async function getKey(rawKey) {
    return await crypto.subtle.importKey(
      "raw",
      fromHex(rawKey),
      "AES-CBC",
      true,
      ["decrypt"]
    );
  }

  async function getKeysFromSession () {
    let keys = {};
    let value;
    Object.keys(sessionStorage).forEach((id) => {
      value = sessionStorage.getItem(id);
      if (value.length == 64) {
        keys[id] = await getKey(value);
      }
    });
    return keys;
  }

  let keys = await getKeysFromSession();
  console.log(keys);
}

/*let session_storage = {};
Object.keys(sessionStorage).forEach((key) => {
    session_storage[key] = sessionStorage.getItem(key);
});*/



if (!window.Worker) {
  console.log('Web Worker API not supported');
  // load index in main thread
  $.getScript(joinUrl(base_url, "search/worker.js")).done(function () {
    console.log('Loaded worker');
    init(session_storage);
    window.postMessage = function (msg) {
      onWorkerMessage({data: msg});
    };
  }).fail(function (jqxhr, settings, exception) {
    console.error('Could not load worker.js');
  });
} else {
  // Wrap search in a web worker
  var searchWorker = new Worker(joinUrl(base_url, "search/worker.js"));
  searchWorker.postMessage({init: true, session_storage: session_storage});
  searchWorker.onmessage = onWorkerMessage;
}
