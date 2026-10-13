# 1st Nanpantan Scouts website

Source code for **<https://nanpantanscouts.org.uk>**, the website of 1st Nanpantan Scout Group in Loughborough.

The site is a static site built with [Hugo](https://gohugo.io/), using the [Universal theme](https://github.com/devcows/hugo-universal-theme). It is hosted on GitHub Pages. **Every push to `main` is built and published automatically**, so check your changes locally first (see [Running the site locally](#running-the-site-locally-on-windows-wsl)).

- [How it works](#how-it-works)
- [What's where](#whats-where)
- [Editing content](#editing-content)
- [Running the site locally (Windows / WSL)](#running-the-site-locally-on-windows-wsl)
  - [Option A: Docker](#option-a-docker)
  - [Option B: Install Hugo directly in WSL](#option-b-install-hugo-directly-in-wsl)
- [Publishing](#publishing)
- [Troubleshooting](#troubleshooting)

## How it works

| Piece | Details |
| --- | --- |
| Site generator | Hugo **extended**, version **0.150.0**, the same version the deploy workflow uses |
| Theme | `github.com/devcows/hugo-universal-theme`, pulled in as a [Hugo Module](https://gohugo.io/hugo-modules/) (see `go.mod`). Hugo needs **Go** installed to download it. |
| Hosting | GitHub Pages, custom domain set by `CNAME` |
| Deployment | `.github/workflows/deploy-hugo.yml` runs on every push to `main`: it runs `hugo --minify` and publishes the `public/` folder |

## What's where

| Path | What it's for |
| --- | --- |
| `hugo.toml` | Site settings: title, menus, top bar, contact details, map location, theme options |
| `content/` | The pages, written in Markdown (`about.md`, `faq.md`, `admissions.md`, `venue-hire.md`, …) |
| `content/blog/` | News posts, one file per post |
| `data/carousel/` | Homepage slideshow, one YAML file per slide (Squirrels, Beavers, Cubs, Scouts) |
| `layouts/` | Our customised copies of theme templates. A file here replaces the theme file with the same path. `layouts/index.html` is the homepage. |
| `layouts/shortcodes/hut_gallery.html` | The photo gallery shortcode used on the venue hire page |
| `static/` | Images, CSS, JavaScript and documents, copied to the site as-is: `static/img/Logo.jpg` becomes `/img/Logo.jpg`. Only our own files and ones we've changed live here; the theme supplies the rest. |
| `i18n/en.yaml` | Our changes to the theme's built-in English text (buttons, labels and so on) |
| `archetypes/` | The template `hugo new` uses for new content |
| `Dockerfile`, `docker-compose.yml` | Run the site locally in Docker (see below) |

## Editing content

### Add a news post

Create a file in `content/blog/` named `YYYY-MM-DD-Short-Title.md`, for example `content/blog/2026-10-13-Autumn-Camp.md`:

```toml
+++
title = "Autumn Camp"
date = "2026-10-13T10:00:00+01:00"
tags = ["camp"]
categories = ["events"]
banner = "img/banners/banner-4.jpg"
authors = ["Your Name"]
+++

The start of the post is shown as its summary on the homepage and blog list.
To choose where the summary ends, put <!--more--> on its own line.

More text here. Normal **Markdown** works, including [links](https://example.com) and images:

![Campfire](/img/campfire.jpg)
```

- Put images in `static/img/`. Refer to them as `img/...` in `banner` and as `/img/...` in the post itself.
- Resize photos before adding them: about 1200px wide and under 300 KB is plenty. Photos straight from a phone are often 3–5 MB and slow the site down on mobile data.
- The post appears at `/blog/YYYY/MM/DD/<file-name>/`, using the `date` in the front matter.
- Add `draft = true` to keep a post off the live site while you work on it. The local dev server still shows drafts.
- A post with a future `date` won't be published until a build runs after that date.

You can also let Hugo create the file for you (in Docker, put `docker compose run --rm dev` in front of the command). It starts as a draft, and the title is made from the file name, so tidy the title and remove `draft = true` when it's ready:

```bash
hugo new content blog/2026-10-13-Autumn-Camp.md
```

### Edit or add a page

The pages are the Markdown files directly in `content/`. To add a new page, create `content/my-page.md` (it will be at `/my-page/`). To add it to the menu, add a `[[menu.main]]` entry in `hugo.toml`, copying one of the existing entries.

## Running the site locally on Windows (WSL)

You can run the site on your own machine, see changes immediately in your browser, and check that it builds before pushing. On Windows, use **WSL 2** (Windows Subsystem for Linux).

### One-off setup

1. **Install WSL with Ubuntu** if you haven't already. In PowerShell (as Administrator):

   ```powershell
   wsl --install
   ```

   Restart when asked, then open **Ubuntu** from the Start menu and choose a username and password.

2. **Clone the repo into your Linux home folder**, not under `/mnt/c/...`. Files on the Windows drive are much slower in WSL, and live reload often doesn't notice changes to them.

   ```bash
   sudo apt update && sudo apt install -y git curl
   cd ~
   git clone https://github.com/Nanpantan-Scouts/nanpantan-scouts.github.io.git
   cd nanpantan-scouts.github.io
   ```

3. *(Optional)* To edit in VS Code, install the [WSL extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl) and run `code .` from the repo folder. You can reach the files from Windows Explorer at `\\wsl$\Ubuntu\home\<you>\nanpantan-scouts.github.io`.

Then choose **one** of the two options below. Docker needs fewer installs and always uses the same Hugo version as the live site. Installing Hugo directly is quicker to start and uses less disk space.

### Option A: Docker

**Requirements:** [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) with WSL integration turned on for Ubuntu (*Settings → Resources → WSL integration*), **or** Docker Engine installed inside WSL. Check it works from your Ubuntu terminal:

```bash
docker compose version
```

**Start the dev server** from the repo folder:

```bash
docker compose up
```

The first run builds the image, which takes a few minutes. Later runs start in seconds. Then:

- Open **<http://localhost:1313>**.
- Edit and save any file. The browser reloads with your change.
- Drafts are shown, so you can preview posts before publishing them.
- Press `Ctrl+C` to stop.

**Preview the production build.** This is the same minified, no-drafts build that goes live, served by nginx:

```bash
docker compose up --build preview
```

Open **<http://localhost:8080>**. The site is baked into this image, so keep the `--build` to pick up your latest changes. Press `Ctrl+C` to stop.

**Run other Hugo commands** inside the container:

```bash
# Create a new post
docker compose run --rm dev hugo new content blog/2026-10-13-Autumn-Camp.md

# Build the site into ./public, exactly as the deploy workflow does
docker compose run --rm dev hugo --minify --cleanDestinationDir
```

**Tidy up:** `docker compose down` removes the containers. Add `-v` to also remove the cached theme download.

### Option B: Install Hugo directly in WSL

You need **Hugo extended** and **Go**. Don't use `sudo apt install hugo` or `golang-go`: Ubuntu's packages are too old for this site.

1. **Install Go.** Hugo uses it to download the theme. Any Go from 1.24.4 onwards works, and the newest release is listed at <https://go.dev/dl/>.

   ```bash
   GO_VERSION=1.26.9
   curl -fsSL -o /tmp/go.tar.gz "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
   sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf /tmp/go.tar.gz
   echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
   source ~/.bashrc
   go version
   ```

2. **Install Hugo extended**, using the same version as the deploy workflow (`HUGO_VERSION` in `.github/workflows/deploy-hugo.yml`):

   ```bash
   HUGO_VERSION=0.150.0
   curl -fsSL -o /tmp/hugo.deb "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.deb"
   sudo dpkg -i /tmp/hugo.deb
   hugo version   # should say "+extended"
   ```

3. **Start the dev server** from the repo folder:

   ```bash
   hugo server --buildDrafts
   ```

   Open **<http://localhost:1313>**. It reloads when you save a file. Press `Ctrl+C` to stop. The first run downloads the theme, so it takes a little longer.

4. **Check the production build.** This is what the deploy workflow runs:

   ```bash
   hugo --minify --cleanDestinationDir
   ```

   It should finish without any `ERROR` lines and write the site to `public/` (which git ignores). `--cleanDestinationDir` removes files left over from earlier runs. Without it, `public/` can still contain draft pages written by `hugo server`.

## Publishing

1. Check your change locally (see above).
2. Commit and push to `main`, or open a pull request and merge it.
3. The **Deploy Hugo site to Pages** workflow runs automatically. You can follow it in the repo's **Actions** tab, and the live site updates a minute or two after it goes green.

To upgrade Hugo, change `HUGO_VERSION` in **both** `.github/workflows/deploy-hugo.yml` and `Dockerfile`, then check the site locally.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `binary with name "go" not found in PATH` | Go isn't installed or isn't on your `PATH`. See step 1 of [Option B](#option-b-install-hugo-directly-in-wsl), then open a new terminal. |
| `failed to download modules` | Hugo couldn't download the theme. Check your internet connection and run the command again. |
| Changes don't appear in the browser | Make sure the repo is in your WSL home folder (`~/...`) and not under `/mnt/c/...`. Hard-refresh the page with `Ctrl+F5`. |
| `port is already allocated` / `address already in use` | Something else is using port 1313 or 8080. Stop it (perhaps another `hugo server` or `docker compose up`), or change the left-hand port in `docker-compose.yml`, e.g. `"1314:1313"`. |
| `docker: command not found` in WSL | In Docker Desktop, turn on *Settings → Resources → WSL integration* for your Ubuntu distro, then reopen the terminal. |
| Docker: `permission denied` writing files, or files in the repo owned by `root` | The dev container runs as user ID 1000, the usual first WSL user. If `id -u` shows a different number, run `export UID GID=$(id -g)` before `docker compose ...`. |
