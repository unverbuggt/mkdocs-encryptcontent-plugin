title: Search encryption

This test checks whether there exist encrypted search entries...

///html | div#searchtest-output
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
        let output='';
        for (let i = 0; i < data.docs.length; i++) {
          if (data.docs[i].location.startsWith('encryptcontent_plugin_')) {
            output = output + data.docs[i].location + "<br>";
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