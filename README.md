<h2 align="center">CookieGuard: Characterizing and Isolating the First-Party Cookie Jar</h2>

**Overview**

Modern sites embed many third-party scripts directly in the main frame. As a result, those scripts inherit first-party privileges and can freely read, modify, delete, and exfiltrate first-party cookies set by the site or by other third parties. CookieGuard is a lightweight, deployable defense that:
- Attributes each cookie to the domain of the script or server that created it.
- Filters access to document.cookie / cookieStore so a script can only see its own cookies.
- Preserves default behavior for true first-party scripts (owned by the visited site).
- Offers an entity-group whitelist to reduce breakage for legitimate multi-domain deployments.

**Key findings from our large-scale study (20k sites):**
- 56% of sites include a script that exfiltrates a cookie it didn’t set.
- 32% include a script that overwrites or deletes such cookies.
- CookieGuard reduces cross-domain overwriting by ~82%, deleting by ~86%, and exfiltration by ~83% with a modest average ~0.3s page-load overhead; SSO breakage can be reduced to ~3% with entity grouping.

**Quick Start (Extension)**
1. Load unpacked
- Visit chrome://extensions (or your Chromium-based browser’s extensions page).
- Enable Developer mode, click Load unpacked, and select cookieguard/extension.

2. Use
- Browse as usual. CookieGuard will:
    . Attribute new cookies to creator domains,
    . Filter document.cookie/cookieStore.getAll() results by caller domain,
    . Block cross-domain overwrites/deletes/reads by default (except for true first-party scripts).

**Cite the Paper**
If you use CookieGuard or the dataset/analysis in your work, please cite:
```bibtex
@inproceedings{bahrami2025cookieguard,
  title     = {CookieGuard: Characterizing and Isolating the First-Party Cookie Jar},
  author    = {Pouneh Nikkhah Bahrami and Aurore Fass and Zubair Shafiq},
  booktitle = {Proceedings of the ACM Internet Measurement Conference (IMC '25)},
  year      = {2025},
  address   = {Madison, WI, USA},
  publisher = {ACM}
  % doi = {TBD}  % add when available
}

