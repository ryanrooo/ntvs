# ntvs
North Texas Volleyball Stats

## Merging into `dev`
The `work` branch and `dev` branch both started from the initial commit that only contained this README. Each branch added its own versions of `index.html` and `styles.css` independently. When you merge, Git raises add/add conflicts on those files because it has no common ancestor version to reconcile.

**How to resolve:**
- First pull `dev` and merge it into your feature branch so you handle the conflicts once locally.
- For each conflict in `index.html` and `styles.css`, choose the version you want to keep (or manually combine them) and commit the resolution.
- After resolving locally, pushing and opening a PR into `dev` will merge cleanly.

If you keep running into conflicts, verify that you are merging the latest `dev` into your branch before opening the PR.
