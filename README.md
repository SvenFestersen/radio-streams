# Radio Streams

A small server to proxy audio (radio station) streams. I had to write this
because my DLNA-enabled AV receiver does not support radio streams without
file extension...

## Usage
Create a JSON file (e.g. `streams.json`) in the following format:

```
{
  "station1": "http://url/for/station1",
  "station2": "http://url/for/station2"
}
```

Start the server:

```
stream-proxy --port 8080 streams.json
```

The streams will then be available at "http://localhost:8080/radio/station1.mp3"
and "http://localhost:8080/radio/station2.mp3".

