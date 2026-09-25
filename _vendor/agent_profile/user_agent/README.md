# User-agent generator

This package contains the sole runtime user-agent generator, its checked-in
browser version tables, and the utilities that refresh those tables. It emits
desktop Chrome, Edge, and Safari strings using either recent releases or an
age-weighted historical release profile.

Generate a user agent from an installed `dately` package:

```sh
python -m dately._vendor.agent_profile.scripts.user_agent.generate
```

Generate from the broader historical pool (mostly current, occasionally old):

```sh
python -m dately._vendor.agent_profile.scripts.user_agent.generate --version-profile historical
```

The default `recent` profile uses only the newest three Chrome/Edge majors and
newest two Safari release families. The `historical` profile weights the latest
major at 65%, the previous major at 20%, ranks 2-5 at 10% combined, and all
remaining checked-in releases at 5% combined.

The refresh retains Chrome's reduced-UA era (major 101 onward), Microsoft Edge
release-note history (including full pre-119 Edge versions), and Safari 14+
releases compatible with the generator's frozen macOS platform token.

Refresh the checked-in version tables:

```sh
python -m dately._vendor.agent_profile.user_agent.update_versions
```

Refreshing versions makes network requests and atomically rewrites the Chrome,
Edge, and Safari tables under
`dately/_vendor/agent_profile/user_agent/browser_versions/`.
