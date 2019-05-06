<!DOCTYPE html>
<html>
<head>
<script>
function resize() {
  parent.document.getElementById('iframe').style.height = document.body.scrollHeight + 100 + 'px';
}
</script>
</head>
<body>
<?php
if ($_GET['url'] && $_GET['chapter']) {
    $cmd =
        'bin/python dm5dl.py -d '
        . escapeshellarg($_GET['url'])
        . ' '
        . escapeshellarg($_GET['chapter']);
    $result = json_decode(exec($cmd));
    $referer = $result->referer;
    $image_urls = $result->image_urls;

    foreach ($image_urls as $url) {
        $context = stream_context_create(
            array('http' => 
                array('header' => 'Referer: ' . $referer)));
        $data = base64_encode(file_get_contents($url, false, $context)); 
        echo '<img src="data:image/jpeg;base64,' . $data .'" onload="resize()" style="width: 70%; margin-left: 15%; margin-right: 15%">';
    }
}
?>
</body>
</html>
