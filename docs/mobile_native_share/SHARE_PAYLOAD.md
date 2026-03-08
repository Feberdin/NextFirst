# NextFirst Native Share Payload

Purpose:
- Define one structured payload for native sharing across iOS and Android.

Payload fields:
- `title` (string, required): Share title/subject.
- `body` (string, required): Main text/caption.
- `url` (string, optional): External URL to include.
- `image_ref` (string, optional): Local file path, content URI, or HTTP(S) image URL.

Example:

```json
{
  "title": "NextFirst Erlebnis",
  "body": "Wir waren heute im Kletterwald!",
  "url": "https://example.com/angebot",
  "image_ref": "content://com.example.app.fileprovider/share/erlebnis.jpg"
}
```

Compatibility guidance:
- Some target apps ignore `subject` or split URL fields.
- Always include critical text in `body`.
- If caption is ignored for image shares, fallback to image-only share is acceptable.
