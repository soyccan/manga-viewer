import http.server
import os
import urllib.parse
from http import HTTPStatus
import email
import datetime


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        """Common code for GET and HEAD commands.
        This sends the response code and MIME headers.
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        path = self.translate_path(self.path)
        f = None
        parts = urllib.parse.urlsplit(self.path)
        if parts.path != '/':
            # redirect browser - doing basically what apache does
            self.send_response(HTTPStatus.MOVED_PERMANENTLY)
            new_parts = (parts[0], parts[1], '/', '', '')
            new_url = urllib.parse.urlunsplit(new_parts)
            self.send_header("Location", new_url)
            self.end_headers()
            return None
        try:
            f = open('manga-viewer.html', 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", 'text/html')
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified",
                self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise        

    def do_POST(self):
        print(self.rfile.read())

def main():
    httpd = http.server.HTTPServer(('', 8000), MyHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    main()
