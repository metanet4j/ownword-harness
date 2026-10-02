"""只在本机提供原型静态资源，压缩可压缩的文本文件。"""
import argparse
import functools
import gzip
import io
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class PreviewHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        file = self.translate_path(self.path)
        accepted = re.search(r'(?:^|,)\s*gzip\s*(?:;\s*q=([01](?:\.\d+)?))?', self.headers.get('Accept-Encoding', ''))
        if accepted and float(accepted.group(1) or '1') > 0 and os.path.isfile(file) and file.endswith(('.js', '.css', '.svg', '.json', '.html')):
            with open(file, 'rb') as source:
                body = gzip.compress(source.read(), compresslevel=6, mtime=0)
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(file))
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Vary', 'Accept-Encoding')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Last-Modified', self.date_time_string(os.path.getmtime(file)))
            self.end_headers()
            return io.BytesIO(body)
        return super().send_head()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()
    ThreadingHTTPServer((args.bind, args.port), functools.partial(PreviewHandler, directory=args.directory)).serve_forever()
