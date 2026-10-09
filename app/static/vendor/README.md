# Bundled browser dependencies

Runtime browser assets are served locally so charts, recipe editing and the
calendar work without a CDN connection. Only the pages needing each library load
it. The vendor directories include their upstream licenses; Brew-Web's MIT
license does not replace those notices.

| Package | Pinned version | npm package integrity |
| --- | --- | --- |
| Quill | 2.0.3 | `sha512-xEYQBqfYx/sfb33VJiKnSJp8ehloavImQ2A6564GAbqG55PGw1dAWUn1MUbQB62t0azawUS2CZZhWCjO8gRvTw==` |
| Chart.js | 4.5.1 | `sha512-GIjfiT9dbmHRiYi6Nl2yFCq7kkwdkp1W/lp2J99rX0yo9tgJGn3lKQATztIjb5tVtevcBtIdICNWqlq5+E8/Pw==` |
| FullCalendar | 6.1.20 | `sha512-7lz2P+0YdA86fBTwfr/ducajrM3zUw5o6uoiiYk9xMqcoTf003xBh3mpzW5om9slfAMwGgCBh0KsiYcU1JY1eQ==` |

These files are copied unchanged from the named npm packages. FullCalendar stays
on its compatible v6 line rather than making a v7 API migration in a maintenance
patch. Quill 2 saves semantic HTML, preserving normal bold/link/list formatting;
legacy Quill 1 HTML remains sanitized and readable. Content is sanitized before
being inserted into the editor, and JSON encoding protects the script context.

SHA-256 for the shipped runtime files:

```text
48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a  chartjs-4.5.1/chart.umd.min.js
b101204ba23e14478e957e284d58bba96fc7311021d0eeaf89fa5e65720c46c8  fullcalendar-6.1.20/index.global.min.js
f6157c72ac9b3f51cdead426335688a027b12405d9d6a4daadd38a676b2d7ff2  quill-2.0.3/quill.js
1c7948cd13aa92fac6390319bc1e5e461823da171519d3a768db56164f871636  quill-2.0.3/quill.snow.css
```

For updates, download the exact package from npm, verify its integrity, copy only
the required runtime files and license, update these records/template paths, and
run the browser smoke tests and offline request checks. Do not replace them with
an unversioned CDN URL. npm archives and extraction directories remain ignored
under `.work/` and are not included in the container image.

Quill 2.0.3's known formula/video HTML-export advisory is documented with the
application's format restrictions, sanitization and regression tests in
[SECURITY.md](../../../SECURITY.md). It is not claimed to be patched upstream or
free of advisory findings. Check both npm and Python audit results when reviewing
this candidate; do not downgrade merely to hide an advisory's version range.
