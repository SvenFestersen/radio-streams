import logging
import json
import os
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.web


# use pycurl for AsyncHTTPClient
tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")


def load_streams(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            streams = json.loads(f.read())
    else:
        streams = {}
    return streams


class RadioStreamHandler(tornado.web.RequestHandler):

    def initialize(self, streams={}):
        self.streams = streams

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, stream_name):
        logger = logging.getLogger("RadioStreamHandler")
        logger.debug("Connection from {}".format(self.request.remote_ip))
        logger.debug("Requested stream: {}".format(stream_name))

        # get the stream url from config file
        if stream_name not in self.streams:
            logger.error("Stream not found: {}".format(stream_name))
            self.set_status(404)
            self.finish()
            return
        stream_url = self.streams[stream_name]

        # build headers to send to server
        icy_headers = {}
        for header in self.request.headers:
            if header.lower().startswith("icy"):
                icy_headers[header] = self.request.headers[header]
                logger.debug("Additional header: '{0}: {1}'".format(header, icy_headers[header]))

        # prepare client
        client = tornado.httpclient.AsyncHTTPClient()

        # resolve redirects
        request = tornado.httpclient.HTTPRequest(stream_url, method="HEAD",
                                                 headers=icy_headers,
                                                 request_timeout=0)
        response = yield client.fetch(request)
        if response.effective_url != stream_url:
            logger.debug("Redirected. New URL: {}".format(response.effective_url))

        stream_url = response.effective_url

        # connect to stream and proxy data to client
        logger.debug("Starting stream...")
        request = tornado.httpclient.HTTPRequest(stream_url,
                                                 headers={"icy-metadata": "1"},
                                                 streaming_callback=self.stream_callback,
                                                 header_callback=self.header_callback,
                                                 request_timeout=0)
        yield client.fetch(request, self.async_callback)

    def async_callback(self, response):
        self.flush()

    def stream_callback(self, chunk):
        self.write(chunk)
        self.flush()

    def header_callback(self, header_line):
        d = header_line.strip().split(":", 1)
        if len(d) == 2 and (d[0].lower().startswith("icy")
                            or d[0].lower().startswith("content")):
            self.set_header(d[0], d[1].strip())


def run_server(filename, port=8080):
    application = tornado.web.Application([
        (r"/radio/(.*?).mp3", RadioStreamHandler,
         dict(streams=load_streams(filename)))
        ])
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("RadioStreamHandler").setLevel(logging.DEBUG)
    run_server("../../streams.json")