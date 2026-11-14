# blog.jtmaui.com

Write posts in `posts/` as `YYYY-MM-DD-slug.md`, run `python build.py`, commit. Cloudflare Workers serves the `site/` folder using `wrangler.jsonc` (no build command; deploy command `npx wrangler deploy`).
Add `draft: true` to a post's header to keep it unpublished.
