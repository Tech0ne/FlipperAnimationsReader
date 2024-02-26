const fs = require('mz/fs');
const path = require('path');
const http = require('http');
const url = require('url');
const { Readable } = require('stream');

// Setup frames in memory
let original;
let flipped;

(async () => {
  const framesPath = './frames/';
  const files = await fs.readdir(framesPath);
  flipped = [];
  original = [];
  for (let i = 0; i < files.length; i++) {
    const pth = path.join('./frames/', files[i]);
    const fls = await fs.readdir(pth);

    original[i] = await Promise.all(fls.map(async (file) => {
      const frame = await fs.readFile(path.join(pth, file));
      return frame.toString();
    }));
    flipped[i] = original[i].map(f => {
      return f
        .toString()
        .split('')
        .reverse()
        .join('')
    });
  }
})().catch((err) => {
  console.log('Error loading frames');
  console.log(err);
});


const streamer = (stream, opts) => {
  let index = 0;
  const frames = opts.flip ? flipped[Math.floor(Math.random()*flipped.length)] : original[Math.floor(Math.random()*original.length)];

  return setInterval(() => {
    // clear the screen
    stream.push('\033[2J\033[3J\033[H');

    stream.push(frames[index]);

    index = (index + 1) % frames.length;
  }, 150);
};

const validateQuery = ({ flip }) => ({
  flip: String(flip).toLowerCase() === 'true'
});

const server = http.createServer((req, res) => {
  if (req.url === '/healthcheck') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({status: 'ok'}));
  }

  if (
    req.headers &&
    req.headers['user-agent'] &&
    !req.headers['user-agent'].includes('curl')
  ) {
    res.writeHead(302, { Location: 'https://github.com/hugomd/parrot.live' });
    return res.end();
  }

  const stream = new Readable();
  stream._read = function noop() {};
  stream.pipe(res);
  const interval = streamer(stream, validateQuery(url.parse(req.url, true).query));

  req.on('close', () => {
    stream.destroy();
    clearInterval(interval);
  });
});

const port = process.env.PARROT_PORT || 3000;
server.listen(port, err => {
  if (err) throw err;
  console.log(`Listening on localhost:${port}`);
});
