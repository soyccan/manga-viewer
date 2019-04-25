<!DOCTYPE html>
<html>
<head>
  <title>MANGA VIEWER BY SOYCCAN</title>
  <style>
    nav {
      position: fixed;
      top: 0;
      width: 100%;
      background: white;
      padding: 5px;
      text-align: center;
    }
    button {
      font-family: 'Segoe UI Symbol';
    }
    .btnLarge {
      position: fixed;
      top: 50%;
      font-size: 70pt;
    }
    main {
      text-align: center;
    }
    #container {
      text-align: center;
    }
    iframe {
      border: none;
      width: 100%;
    }
  </style>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      var images = [];
      var reloadPages = true;

      var changeChapter = function() {
        document.documentElement.scrollTop = 0;

        var chapter = document.forms[0].chapter.value;
        var path = document.forms[0].path.value;
        var targetType = document.forms[0].targetType.value;
        var iframe = document.getElementById('iframe');

        reloadPages = true;
        images = [];
        iframe.src = "";

        if (targetType == 'file') {
          for (var i = 0; i < 100; i++) {
            var idx = String(i + 1);
            if (idx.length < 2) idx = '0' + idx;

            images[i] = new Image();
            images[i].setAttribute('idx', idx);
            images[i].onload = function(event) {
              event.target.setAttribute('status', 'loaded');
            }
            images[i].onerror = function(event) {
              event.target.setAttribute('status', 'fail');
            };

            images[i].src = path + '/ch_' + chapter + '/' + idx + '.jpg';
          }
        }
        else if (targetType == 'url') {
          iframe.src = 'image.php?url=' + path + '&chapter=' + chapter;
        }

//         if (targetType == 'url' && path && chapter) {
//           var rq = new XMLHttpRequest();
//           rq.onload = function() {
//               console.log(rq.responseText);
//               var image_urls = JSON.parse(rq.responseText);
//               for (var i in image_urls) {
//                   images[i].src = image_urls[i];
//               }
//           };
//           rq.open('POST', location.href);
//           rq.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
//           rq.send('manga_url=' + path + '&chapter_index=' + chapter);
//         }
      };

      var resizePages = function() {
        var width = document.forms[0].width.value;
        document.getElementById('container').childNodes.forEach(function(img) {
          img.style.width = width + '%';
          img.style.marginLeft = img.style.marginRight
                               = (100 - parseInt(width)) / 2 + '%';
        });
        document.getElementById('iframe').contentDocument
              .getElementsByTagName('img').forEach(function(img) {
          img.style.width = width + '%';
          img.style.marginLeft = img.style.marginRight
                               = (100 - parseInt(width)) / 2 + '%';
        });
        document.getElementById('widthText').innerText = width;
      };

      var showPages = function() {
        if (!reloadPages)
          return;
        if (!images.every( img => img.getAttribute('status') ))
          return;

        reloadPages = false;

        var container = document.getElementById('container');
        container.innerHTML = '';
        images.sort((x, y) => x.getAttribute('idx') - y.getAttribute('idx'));
        images.forEach(function(elem) {
          if (elem.getAttribute('status') == 'loaded') {
            container.appendChild(elem);
          }
        });

        resizePages();
      };
      setInterval(showPages, 1);

      // events
      document.forms[0].addEventListener('submit', function(event) {
        event.preventDefault();
      });

      document.forms[0].width.addEventListener('change', function(event) {
        resizePages();
      });

      document.forms[0].width.addEventListener('input', function(event) {
        resizePages();
      });

      Array.from(document.getElementsByClassName('changeChapterBtn')).forEach(
      function(changeChapterBtn) {

        changeChapterBtn.addEventListener('click', function(event) {
          event.preventDefault(); 

          if (event.target.getAttribute('change-by') == 'prev')
            document.forms[0].chapter.value =
                parseInt(document.forms[0].chapter.value) - 1;

          else if (event.target.getAttribute('change-by') == 'next')
            document.forms[0].chapter.value =
                parseInt(document.forms[0].chapter.value) + 1;

          changeChapter();
        });
      });

      // default
      document.getElementsByName('chapter')[0].value = 1;
      document.forms[0].width.value = 70;
      changeChapter();
    });
  </script>
</head>
<body>
  <nav>
    <form>
      <label>
        Chapter: <input name="chapter">
      </label>
      <button type="button" class="changeChapterBtn" change-by="prev">⏮</button>
      <button type="button" class="changeChapterBtn" change-by="next">⏭</button>
      &nbsp;&nbsp;

      <label>
        Width: <input name="width" type="range" min="10" max="100">
        <span id="widthText"></span>%
      </label>
      &nbsp;&nbsp;

      <label>
        <input type="radio" name="targetType" value="url" checked>URL
        <input type="radio" name="targetType" value="file">File
      </label>

      <!-- Path: <input name="path" type="file" webkitdirectory> -->
      <input name="path">

      <button type="submit" class="changeChapterBtn" change-by="set">OK</button>
    </form>
  </nav>
  <main>
    <aside id="leftCol">
      <button type="button" style="left: 10px" class="changeChapterBtn btnLarge" change-by="prev">⏮</button>
    </aside>
    <aside id="rightCol">
      <button type="button" style="right: 10px" class="changeChapterBtn btnLarge" change-by="next">⏭</button>
    </aside>

    <div id="container"></div>
    <iframe src="" id="iframe"></iframe>
  </main>
</body>
</html>
