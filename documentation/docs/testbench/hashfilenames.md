title: Hash file names

This test checks whether MD5 hashes are added to the filenames...

/// html | div#testimg-output

///

![](../img/howitworks.svg){ #testimg}


<script>
var testimg = document.getElementById('testimg');
var testimg_output = document.getElementById('testimg-output');

testimg_output.innerHTML = testimg.src;

</script>