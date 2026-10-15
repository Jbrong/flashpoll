// CloudFront Function (cloudfront-js-2.0) on the site's default behavior.
function handler(event) {
  var request = event.request;
  var host = request.headers.host ? request.headers.host.value : '';

  // www.flashpoll.dev -> flashpoll.dev
  if (host.indexOf('www.') === 0) {
    return {
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: { location: { value: 'https://' + host.substring(4) + request.uri } },
    };
  }

  // Client-side routes (/p/abc123, /admin) have no file extension: serve the app shell.
  // Real files (/assets/index-abc.js, /logo.png) pass through unchanged.
  if (!/\.[A-Za-z0-9]+$/.test(request.uri)) {
    request.uri = '/index.html';
  }
  return request;
}
