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

    @tornado.gen.coroutine
    def get_stream_headers(self, stream_url):
        client = tornado.httpclient.AsyncHTTPClient()
        request = tornado.httpclient.HTTPRequest(stream_url, method="HEAD",
                                                 headers={"icy-metadata": "1"})
        response = yield client.fetch(request)
        return response.headers

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

        # get stream headers to proxy them
        all_stream_headers = yield self.get_stream_headers(stream_url)
        filtered_headers = filter(lambda x: x.lower().startswith("icy"),
                                  all_stream_headers)
        stream_headers = {header: all_stream_headers[header] for header
                          in filtered_headers}
        for header in stream_headers:
            value = stream_headers[header]
            logger.debug("Stream header: '{0}: {1}'".format(header, value))
            self.set_header(header, value)

        logger.debug("Starting stream...")
        # connect to stream and proxy data to client
        client = tornado.httpclient.AsyncHTTPClient()
        request = tornado.httpclient.HTTPRequest(stream_url,
                                                 headers={"icy-metadata": "1"},
                                                 streaming_callback=self.stream_callback,
                                                 request_timeout=0)
        yield client.fetch(request, self.async_callback)

    def async_callback(self, response):
        self.flush()

    def stream_callback(self, chunk):
        self.write(chunk)
        self.flush()


def run_server(filename, port=8080):
    application = tornado.web.Application([
        (r"/radio/(.*?).mp3", RadioStreamHandler, dict(streams=load_streams(filename)))
        ])
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger("RadioStreamHandler").setLevel(logging.DEBUG)
    run_server("../../streams.json")