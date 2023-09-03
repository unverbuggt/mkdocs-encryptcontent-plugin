title: Search encryption

This test checks whether there exist encrypted search entries...

First line is an entry in the search_index.json and second is the encryptcontent-index from sessionStorage.

If nothing was decrypted, yet, they must match (otherwise open a new tab).

Now decrypt pages and check if the search_index decrypted the entries.

/// html | div#searchtest-output
    attrs: {class: 'w3-responsive'}

empty

///

<script>
var searchtest_output = document.getElementById('searchtest-output');

fetch(base_url + '/search/search_index.json')
.then(
  function(response) {
    if (response.status !== 200) {
      searchtest_output.innerHTML = "error fetching search_index.json: "+response.status;
      return;
    }
    response.json().then(
      function(data) {
        let sessionIndex = sessionStorage.getItem('encryptcontent-index')
        if (sessionIndex) {
            sessionIndex = JSON.parse(sessionIndex);
        } else {
            searchtest_output.innerHTML = "Please hit refresh.";
            return;
        }
        let output='';
        for (let i = 0; i < data.docs.length; i++) {
          if (data.docs[i].location.startsWith('encryptcontent_plugin_')) {
            output = output + '<p>' + data.docs[i].location + ' <br>' + sessionIndex.docs[i].location + '</p>';
          }
        }
      searchtest_output.innerHTML = output;
      }
    );
  }
)
.catch(
  function(err) {
    searchtest_output.innerHTML = "error fetching search_index.json: "+err;
  }
);
</script>