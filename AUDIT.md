# Audit complet de l'écosystème — 6 juillet 2026

Audit « au peigne fin » de l'ensemble des actifs du compte : 6 dépôts GitHub, 3 projets Supabase (« vaults »), l'automatisation quotidienne Gmail, l'état CI/déploiements, et un balayage Notion/Google Drive.

**Méthode** : 79 agents spécialisés en 2 vagues — cartographie par dépôt, puis audit sur 3 dimensions (bugs, sécurité, complétude/qualité), puis **contre-vérification adversariale** des findings critiques (chaque finding « high » a été confié à un agent chargé de le *réfuter*, preuve à l'appui — build reproduit, code tracé). **25 findings critiques vérifiés → 25 confirmés réels** (quelques sévérités re-gradées à la baisse). Total : **147 findings** (31 high / 68 medium / 48 low).

---

## Résumé exécutif

| Actif | État | Verdict en une phrase |
|-------|------|----------------------|
| **streamflix** | 🔴 Cassé | Le dernier commit (export statique + GitHub Pages) a brisé toute la chaîne de build — 3 bloqueurs indépendants, le site n'a jamais été déployé. |
| **business-idea-radar** | 🟠 Fonctionnel avec risques | Le scanner marche, mais chaîne d'injection de prompt via contenu Reddit → exécution de commandes, et le dashboard affiche des champs que le pipeline ne produit pas. |
| **nous-deux** | 🟠 WIP avancé | App riche et soignée (~6 300 lignes) mais déploiement Pages cassé (11 échecs/11), écritures Supabase « fire-and-forget » (perte de données silencieuse), policies RLS trouées. |
| **code-examen** | 🟢 Sain | PWA fonctionnelle ; 1 réponse de quiz fausse (feu vert clignotant), memo vs quiz contradictoires (trottinette 12 vs 14 ans). |
| **citation** | 🟠 Fourre-tout | Contient en fait **4 projets** (Oral PASS Sorbonne, boutique VÉLOCE, thème Shopify AURA…) ; XSS réfléchi, mot de passe admin `veloce2026` publié dans le code **et** le README. |
| **README profil** | 🟢 Sain | Cohérent ; quelques mises à jour à faire (projets manquants, « Vercel » dans la stack alors que 0 projet Vercel actif sur le compte lié). |
| **Vault principal** | ⚪ Coquille vide | 0 table, 0 migration, 0 advisor — sain mais inutilisé. Remis en pause. |
| **Vault nous-deux** | 🟠 À corriger | 21 tables (toutes vides), RLS activé partout **mais** 3 tables avec policies « toujours vraies » (écriture `anon` illimitée), 17 advisors sécurité / 27 perf. |
| **Vault veloce-sneakers** | 🔴 Critique | 4 RPC admin `SECURITY DEFINER` exécutables par `anon`, protégées par le seul secret `veloce2026`… publié dans le dépôt Citation → catalogue modifiable par n'importe qui. |
| **Digest Gmail quotidien** | 🟡 Marche mais déborde | Tourne fidèlement chaque jour à 8h UTC ; **65 brouillons jamais envoyés** accumulés depuis le 3 mai, 1 jour manqué, rotation « quotidienne » qui ne couvre que 7 tranches fixes. |

---

## 1. Dépôts

### 1.1 streamflix — 🔴 cassé (7 high, 10 medium, 6 low)

Interface façon Netflix (Next.js 16, React 19, Tailwind 4, API TMDB en français, ~880 lignes). Le code applicatif est propre et fonctionnerait en dev avec une clé TMDB — mais le dernier commit, censé déployer sur GitHub Pages, a tout cassé. **Trois bloqueurs indépendants, chacun vérifié par reproduction du build** :

1. **`output: 'export'` + routes dynamiques sans `generateStaticParams()`** (`src/app/film/[id]/page.tsx`, `src/app/series/[id]/page.tsx`) → `next build` échoue systématiquement.
2. **`npm ci` + `cache: npm` sans lockfile commité** (`.github/workflows/deploy.yml`) — un `package-lock.json` existe sur le disque mais n'a jamais été commité → le workflow échoue à l'étape d'install à chaque run (l'unique run est en échec).
3. **La page de recherche** (`src/app/search/page.tsx`) `await searchParams` dans un composant serveur → incompatible avec l'export statique, et conceptuellement impossible sur un site statique.

Plus : la clé `NEXT_PUBLIC_TMDB_API_KEY` n'est jamais fournie au build CI (les pages /films /series /anime ne sont pas protégées par try/catch → échec du prerender), le README documente la mauvaise variable (`TMDB_API_KEY`), et il n'y a ni `error.tsx` ni `not-found.tsx`.

**Plan de réparation** (dans l'ordre) : commiter le lockfile → choisir entre (a) abandonner l'export statique et déployer sur Vercel, ou (b) garder Pages avec `generateStaticParams` sur les IDs réellement listés + recherche côté client (`useSearchParams`) → ajouter le secret TMDB au workflow → corriger le README → ajouter les error boundaries.

### 1.2 business-idea-radar — 🟠 risques réels (7 high → re-gradés 6 medium + 1 low, 15 medium, 7 low)

Scanner Reddit en Python (~930 lignes) qui fait noter des idées business par Claude, avec dashboard local (~990 lignes, `http.server` stdlib). L'outil fonctionne, mais :

- **Injection de prompt → exécution de commandes** : le texte brut de posts Reddit est inséré dans un prompt passé au CLI Claude Code avec `--permission-mode auto`. Un post malveillant peut détourner l'agent local. *Correction : passer le contenu Reddit en données (fichier/stdin) avec un prompt qui l'encadre comme non-fiable, et retirer le mode auto.*
- **Écrasement de données** : les fichiers `TIER1_/TIER2_/ALL_` sont datés au jour — un second run le même jour écrase le premier. *Correction : horodater à la seconde ou suffixer un compteur.*
- **Dashboard désynchronisé du pipeline** : il lit `url`/`score`/`comments` sur les threads, champs que le scanner n'émet pas → liens jamais rendus, tris et stats cassés (trouvé indépendamment par 2 dimensions d'audit).
- **Bouton « Scan » in-UI** : scan synchrone dans le handler HTTP mono-thread → toute l'UI gèle, timeout sur les runs réalistes, erreurs avalées.
- README : commande de lancement documentée fausse (Streamlit vs stdlib), vérification PRAW incompatible avec la version installée.

### 1.3 nous-deux — 🟠 WIP avancé (7 high, 18 medium, 10 low)

Dashboard de couple longue distance (React 19 + TypeScript + Vite + Tailwind 4 + Supabase, ~6 300 lignes, CI complète lint/type-check/Vitest/build). Le plus abouti des projets, mais :

- **Déploiement GitHub Pages cassé depuis toujours** (11 runs/11 en échec) : pas de `base` Vite pour un project site, pas de fallback SPA pour BrowserRouter (deep links → 404). Vérifié.
- **Écritures Supabase « fire-and-forget »** : les envois échoués (mots doux, humeurs, réponses…) sont silencieusement perdus — l'UI affiche un succès. Vérifié high.
- **Le chat « pensées » gèle après 100 messages** : il récupère les 100 *plus anciens* au lieu des plus récents. Vérifié high.
- **Page Activités inaccessible sur mobile** : la nav basse ne la liste pas. Vérifié high.
- Question du jour qui ne tourne jamais (`limit(1)` sans aléatoire), capsules temporelles livrées au client *avant* la date de révélation (secret uniquement côté UI), races à l'inscription et à la création de question, ~1 270 lignes de widgets morts, moitié du texte français sans accents.
- Le schéma Supabase (17 tables + RPC) n'est **ni versionné ni documenté** dans le dépôt.

### 1.4 code-examen — 🟢 sain (2 high, 10 medium, 12 low)

PWA de révision du Code de la route (458 questions, 10 séries, sans build). Solide. À corriger en priorité :

- **Réponse fausse au quiz** : la question « feu vert clignotant » contredit sa propre explication — les utilisateurs apprennent une règle erronée. Vérifié.
- **Memo vs quiz contradictoires** : trottinette électrique 12 ans (memo) vs 14 ans (quiz).
- `JSON.parse` du localStorage non protégé (peut bricker l'app), compteur de streak qui affiche 0 chaque matin et plafonne à 7, 58 images Wikimedia hotlinkées sans fallback, nav clavier inaccessible.

### 1.5 citation — 🟠 fourre-tout à scinder (8 high, 15 medium, 13 low)

Le dépôt « Citation » (annoncé comme « générateur de citations » dans le README de profil) contient en réalité **quatre projets sans rapport** : l'app « Oral PASS Sorbonne 2026 » (React 18 via CDN, 2 765 lignes, en ligne sur Pages), la boutique **VÉLOCE** (catalogue Supabase = le vault `veloce-sneakers`), un thème Shopify OS 2.0 « AURA », et des zips commités. Findings critiques :

- **XSS réfléchi** via termes de recherche non échappés. Vérifié high.
- **Mot de passe admin `veloce2026` committé dans le JS client et documenté dans le README** — le catalogue live peut être modifié par n'importe qui. À révoquer immédiatement.
- **Firebase Realtime Database sans authentification** avec room partagée `rooms/default` : les données de tous les visiteurs se lisent/écrasent mutuellement.
- Formulaire « retour en stock » imbriqué dans le formulaire panier (capture email cassée), `wishlist.js` chargé 2× (ajout panier en double), faux « Ajouté ✓ » sans `res.ok`, breadcrumbs avec un filtre Liquid inexistant, export de données qui throw systématiquement.

**Recommandation structurelle** : scinder en 3-4 dépôts (`oral-pass`, `veloce-sneakers`, `aura-shopify-theme`), supprimer les zips, et réécrire le README de profil en conséquence.

### 1.6 README de profil — 🟢 sain

Cohérent et déjà en place. Améliorations : le lien « Citation » décrit un « générateur de citations quotidien » qui ne correspond plus au contenu réel ; la stack affiche « Vercel » alors qu'aucun projet Vercel n'est actif sur le compte connecté ; ajouter les projets réellement montrables une fois réparés.

---

## 2. Vaults Supabase

Les 3 projets étaient **tous en pause** au début de la session. Ils ont été restaurés pour audit (avec rotation, le plan gratuit limitant à 2 projets actifs), puis remis dans leur état d'origine (en pause) à la fin.

### 2.1 principal (« martinbouvet2000-tech's Project », eu-west-1)

Coquille vide : 0 table, 0 migration, 0 edge function, 0 advisor de sécurité ou de performance. Aucun risque — mais aucune utilité actuelle. Candidat à la suppression si aucun projet ne le réclame (ça libérerait un slot actif du plan gratuit).

### 2.2 nous-deux (eu-west-1)

21 tables (toutes vides — l'app n'a pas encore d'utilisateurs réels), 4 migrations, 0 edge function. RLS est activé sur les 21 tables, **mais** :

- `album_memories` : policies `anon` DELETE/INSERT/UPDATE **toujours vraies** → n'importe quel visiteur non authentifié peut écrire/supprimer.
- `daily_questions` : INSERT sans restriction (`WITH CHECK true`).
- `streaks` : INSERT/UPDATE toujours vrais.
- Bucket public `album-photos` : lecture de tous les fichiers par n'importe quel client.
- 17 advisors sécurité (dont `function_search_path_mutable` sur 5 fonctions : `update_updated_at`, `get_partner_id`, `generate_partner_code`, `link_partner_by_code`, `enforce_single_origin`) et 27 advisors performance.

**Correction prioritaire** : réécrire les policies toujours-vraies avec un scoping par couple (`auth.uid()`), fixer `search_path` des fonctions, et versionner le schéma dans le dépôt `nous-deux`.

### 2.3 veloce-sneakers (eu-west-3)

1 table `produits` (0 ligne, RLS activé), 2 migrations (`veloce_schema_rls_storage`, `veloce_admin_write_rpcs`), 0 edge function. **8 advisors sécurité — et c'est le finding le plus grave de tout l'audit une fois recoupé avec le code** :

- Les 4 fonctions **`SECURITY DEFINER`** `admin_upsert(p_secret, p_row)`, `admin_delete(p_secret, p_id)`, `admin_new(p_secret)`, `admin_list_all(p_secret)` sont **exécutables par les rôles `anon` et `authenticated`** via `/rest/v1/rpc/…`.
- Leur seule protection est le paramètre `p_secret` — or ce secret (`veloce2026`) est **committé dans le JS client et documenté dans le README** du dépôt Citation.
- Conséquence : **n'importe qui sur Internet peut lister, créer, modifier et supprimer les produits du catalogue VÉLOCE** avec un simple appel REST. La combinaison « secret publié + RPC anon » annule totalement le RLS de la table.

**Correction** : changer le secret immédiatement, puis remplacer ce mécanisme par de vraies policies RLS sur un rôle authentifié (ou révoquer `EXECUTE` pour `anon`/`authenticated` et passer par une edge function avec service_role côté serveur). Côté perf : 4 policies avec `auth.<fn>()` ré-évalué par ligne (utiliser `(select auth.<fn>())`) et 2 policies SELECT permissives redondantes.

---

## 3. Automatisations

### 3.1 « Claude Code Plugin Daily Digest » (trigger quotidien, 8h00 UTC)

**Verdict : il fonctionne** — le brouillon du jour (2026-07-06) a bien été créé à 08:07 UTC, 65 brouillons produits du 3 mai au 6 juillet (1 seul jour manqué : le 21 mai ; 1 doublon le 3 mai, jour d'installation). Points relevés :

1. **65 brouillons non envoyés s'accumulent** dans Gmail — l'automatisation crée mais n'envoie ni ne nettoie jamais. Décider : envoi automatique, ou purge des brouillons > 7 jours.
2. **La « rotation quotidienne » de la section 3 est bancale** : `offset = (jour_semaine × 3) mod 20` ne produit que 7 tranches fixes {0,3,6,9,12,15,18} — le même contenu chaque lundi, etc. Une vraie rotation utiliserait le jour de l'année.
3. **Décalage horaire en hiver** : le footer promet « chaque matin à 10h » — vrai en été (8h UTC = 10h CEST), faux de fin octobre à fin mars (9h CET). Utiliser un cron adapté ou reformuler.
4. `allowed_tools` ne liste que Bash/WebFetch/WebSearch/Read/Write sans les outils MCP Gmail — en pratique la connexion Gmail MCP du trigger passe outre, mais la config est incohérente avec son propre prompt.
5. Les pages de recherche GitHub en HTML sont une SPA JS — le prompt gagnerait à cibler l'API GitHub (`api.github.com/search/repositories`) pour des résultats fiables.
6. Pas de règle de déduplication entre les 3 sections.
7. Modèle `claude-sonnet-4-6` : valide et actif, mais une génération en retard (envisager `claude-sonnet-5`).

La skill **routine-builder** (déjà activée sur le compte) est l'outil naturel pour reconstruire ce trigger proprement.

### 3.2 Hygiène GitHub

- **0 PR ouverte, 0 issue ouverte** sur les 6 dépôts — rien d'oublié en vol.
- **streamflix** : workflow « Deploy to GitHub Pages » — l'unique run a échoué ; jamais déployé.
- **nous-deux** : même workflow — **11 échecs sur 11 runs** ; le run CI initial a aussi échoué.
- **Citation** : 3 branches `claude/*` mortes sans PR (`claude/clever-wilbur-…`, `claude/cryoglow-ecommerce-shop-…`, `claude/sports-shoe-showcase-…`) → à supprimer.
- **code-examen** : branche `feat/initial-setup` obsolète (probablement mergée) → à supprimer.
- Dernière activité générale : 19 juin (Citation) ; le reste est intact depuis le 26 mai.

### 3.3 Balayage écosystème (Notion, Google Drive)

Le terme « vault » n'existe nulle part dans Notion ; les seuls résultats Drive sont des guides Obsidian « second brain » tiers. **Confirmation : « les vaults » = les 3 projets Supabase**, rien d'autre. Aucun des projets (streamflix, veloce…) n'a de documentation dans Notion ou Drive. Les connecteurs Adobe Marketing Agent et Miro nécessitent une ré-authentification OAuth (hors de portée de cette session).

---

## 4. Plan d'action priorisé

### ✅ Correctifs P0 déjà appliqués (7 juillet 2026)

Les correctifs de sécurité critiques ont été appliqués dans la foulée de l'audit :

- **veloce-sneakers (Supabase)** : le secret `admin_secret` de `private.config` a été **rotationné** vers une valeur aléatoire de 28 caractères jamais commitée → l'ancien code `veloce2026` (publié) ne déverrouille plus rien. *(Nouveau code transmis à Martin hors dépôt.)*
- **citation (PR [#30](https://github.com/martinbouvet2000-tech/citation/pull/30))** : XSS réfléchi corrigé (`search.liquid`), constante `veloce2026` + mode admin hors-ligne supprimés, room Firebase par défaut remplacée par une room aléatoire par appareil. Preview Vercel déployée avec succès.
- **business-idea-radar (PR [#1](https://github.com/martinbouvet2000-tech/business-idea-radar/pull/1))** : CLI invoqué en génération seule (`--tools ""`) au lieu de `--permission-mode auto`, contenu Reddit encadré comme non-fiable.
- **nous-deux (Supabase)** : policies RLS toujours-vraies `anon`/`PUBLIC` sur `album_memories`, `daily_questions`, `streaks` réécrites en `authenticated` uniquement ; `search_path` fixé sur les 5 fonctions. **Advisors sécurité : 17 → 6** (restants = listing bucket, 2 RPC anon, toggles Auth — reclassés P1).

Reste en P1 (nécessite une vraie authentification, non fait unilatéralement) : passer les RPC admin veloce sous Supabase Auth + révoquer `EXECUTE` pour `anon` ; règles de sécurité Firebase ; restreindre le listing du bucket `album-photos`.

### P0 — Sécurité (statut)
1. ✅ **Code admin `veloce2026` rotationné côté serveur** (Citation/VÉLOCE). Durcissement restant (P1) : révoquer `EXECUTE` pour `anon`/`authenticated` sur les 4 RPC `admin_*` une fois Supabase Auth en place.

<details><summary>Actions P0 initialement recommandées (avant correctifs)</summary>

1. **Révoquer/changer le code admin `veloce2026`** (Citation/VÉLOCE — committé + documenté publiquement) **et révoquer `EXECUTE` pour `anon`/`authenticated` sur les 4 RPC `admin_*` du vault veloce-sneakers** — en l'état, le catalogue live est modifiable par n'importe qui via REST.
2. **Corriger le XSS réfléchi** de la recherche (Citation).
3. **Réécrire les policies RLS toujours-vraies** du vault `nous-deux` (`album_memories`, `daily_questions`, `streaks`) avec scoping `auth.uid()`.
4. **Désamorcer l'injection de prompt** de business-idea-radar (contenu Reddit → CLI en `--permission-mode auto`).
5. **Sécuriser/authentifier Firebase RTDB** de l'app Oral PASS (room partagée publique).

</details>

### P1 — Réparer ce qui est cassé
6. streamflix : lockfile + choix Vercel *ou* `generateStaticParams` + recherche client + secret TMDB en CI.
7. nous-deux : `base` Vite + fallback SPA → premier déploiement Pages réussi ; gestion d'erreurs sur toutes les écritures Supabase ; fix du chat 100 messages ; page Activités dans la nav mobile.
8. business-idea-radar : aligner le contrat scanner ↔ dashboard ; horodatage des fichiers de sortie.
9. code-examen : corriger la réponse « feu vert clignotant » et l'incohérence trottinette 12/14 ans.
10. Digest Gmail : décider envoyer vs purger les 65 brouillons ; vraie rotation ; API GitHub au lieu du HTML.

### P2 — Qualité / structure
11. Scinder le dépôt Citation en 3-4 dépôts et mettre à jour le README de profil.
12. Versionner le schéma Supabase de nous-deux ; supprimer les 4 branches mortes ; nettoyer les widgets morts (~1 270 lignes) ; accessibilité (nav clavier, ARIA) sur code-examen et nous-deux ; `JSON.parse` protégé (code-examen).

---

*Audit réalisé le 6 juillet 2026 — 79 agents, ~4,2 M tokens d'analyse, 147 findings dont 25 critiques contre-vérifiés un par un (25/25 confirmés). Détail complet en annexe.*


---

## Annexe — Findings détaillés par dépôt

### business-idea-radar

| Sév. | Vérifié | Finding | Fichier |
|------|---------|---------|---------|
| high | ✅ confirmé (re-gradé medium) | PRAW auth check always fails (praw 8.x) or validates nothing (praw 7.x) — authenticated scraping path is unreachable | `reddit_idea_radar.py:348` |
| high | ✅ confirmé (re-gradé medium) | Second run on the same day overwrites TIER1_/TIER2_/ALL_ files, permanently losing the earlier run's ideas | `reddit_idea_radar.py:776` |
| high | — | Dashboard reads thread fields (url/score/comments) that the pipeline never produces — thread links never render and upvote/comment sorts are no-ops | `dashboard.py:500` |
| high | ✅ confirmé (re-gradé medium) | Untrusted Reddit content piped into Claude Code CLI with --permission-mode auto enables prompt-injection command execution | `reddit_idea_radar.py:540` |
| high | ✅ confirmé (re-gradé low) | README advertises a Streamlit dashboard but the app is a stdlib http.server — documented launch command fails | `README.md:33` |
| high | — | Dashboard reads thread fields (url/score/comments) that the scanner never emits — thread links, sorts, and upvote stats are all dead | `dashboard.py:499` |
| high | ✅ confirmé (re-gradé medium) | In-UI 'Scan' button freezes the whole dashboard and times out on realistic runs; failure details are discarded | `dashboard.py:943` |
| medium | — | Dashboard scoring axes are mislabeled and the GAP axis / CSV Gap column are always 0; modal omits angle, monetization, contacts, and competition data the pipeline produces | `dashboard.py:488` |
| medium | — | Prompt asks Claude for date-stamped IDs but never supplies the current date — dedup keys and scanned_date are hallucinated | `reddit_idea_radar.py:128` |
| medium | — | Scan button blocks the single-threaded server for up to 15 minutes; browser fetch times out and reports ERROR while the scan is still running | `dashboard.py:943` |
| medium | — | Default file selection sorts by filename, not recency — dashboard can silently open a stale previous-day file | `dashboard.py:920` |
| medium | — | --output with a nested non-existent directory crashes at save time, after the full scrape and paid Claude analysis | `reddit_idea_radar.py:771` |
| medium | — | esc() does not escape double quotes, but its output is interpolated into HTML attribute values (href) — attribute breakout / DOM XSS | `dashboard.py:833` |
| medium | — | XSS in dashboard: esc() does not neutralize attribute breakout or javascript: URLs, and several fields are rendered unescaped | `dashboard.py:666` |
| medium | — | /api/run is an unauthenticated state-changing endpoint with no CSRF or Host validation — any website can trigger scans that launch the Claude Code CLI | `dashboard.py:910` |
| medium | — | Radar chart and score panel mislabel every axis and always show a phantom 'GAP = 0' dimension | `dashboard.py:488` |
| medium | — | Detail modal drops the richest analysis data (pain evidence, competitors, angle, monetization, contacts) and renders a nonexistent 'opportunity' field | `dashboard.py:751` |
| medium | — | No error handling or loading state on init()/loadFile() fetches — any API failure leaves a silent blank page | `dashboard.py:461` |
| medium | — | esc() does not escape double quotes but is used inside href attributes — attribute breakout with untrusted pipeline data | `dashboard.py:833` |
| medium | — | Silent data loss when Claude output exceeds max_tokens — stop_reason never checked | `reddit_idea_radar.py:445` |
| medium | — | Dashboard is keyboard-inaccessible: clickable divs, modal without dialog semantics, unlabeled controls, failing contrast | `dashboard.py:648` |
| medium | — | Hardcoded French/English mix across UI, reports, and docs — with unaccented French strings | `dashboard.py:15` |
| low | — | Subreddit rendered with a duplicated prefix: "r/r/Entrepreneur" | `reddit_idea_radar.py:728` |
| low | — | Mini radar chart forces 200×200px inline size, overriding the intended 100%×90px card layout | `dashboard.py:674` |
| low | — | README instructs `streamlit run dashboard.py`, but the dashboard is a plain http.server app and streamlit is not a dependency | `README.md:33` |
| low | — | run_radar.ps1 silently analyzes a stale THREADS file when the scrape step fails | `run_radar.ps1:14` |
| low | — | Subreddit displayed as 'r/r/X' — double prefix in both the dashboard and the markdown report | `reddit_idea_radar.py:728` |
| low | — | README misstates requirements: Reddit credentials marked 'Required: Yes' despite a working no-credential fallback, and '--local' is not 'fully offline' | `README.md:42` |
| low | — | Dead code: legacy 'IDEAS_' file prefix and ignored --output/--model options | `dashboard.py:921` |
### citation

| Sév. | Vérifié | Finding | Fichier |
|------|---------|---------|---------|
| high | ✅ confirmé | Reflected XSS via unescaped search terms | `shopify-theme/templates/search.liquid:13` |
| high | ✅ confirmé | Back-in-stock form is nested inside the add-to-cart form; email capture is completely broken | `shopify-theme/snippets/back-in-stock.liquid:30` |
| high | ✅ confirmé (re-gradé medium) | wishlist.js is loaded twice on /pages/favoris — 'Ajouter au panier' adds the product to the cart twice | `shopify-theme/templates/page.favoris.liquid:146` |
| high | — | Diagnostic add-to-cart shows 'Ajouté ✓' on failed requests (no res.ok check) — and always fails due to placeholder variant IDs | `shopify-theme/assets/diagnostic.js:568` |
| high | — | Default admin/management password committed in code and documented in README (veloce2026) | `sneakers/index.html:587` |
| high | — | Data export feature is completely broken: exportData always throws on non-JSON 'oral-pass-theme' value | `oral-medecine.html:2538` |
| high | — | Firebase sync defaults every visitor to the shared room 'rooms/default' — strangers read/overwrite each other's personal data | `oral-medecine.html:922` |
| high | — | VÉLOCE admin management code 'veloce2026' published in client JS and README — live catalog can be modified/wiped by anyone | `sneakers/index.html:587` |
| medium | — | Breadcrumbs use nonexistent Liquid `push` filter — breadcrumb trail renders empty on every page | `shopify-theme/snippets/breadcrumbs.liquid:52` |
| medium | — | Diagnostic results link to nonexistent product URLs (handles don't match the catalog) | `shopify-theme/assets/diagnostic.js:19` |
| medium | — | diagnostic.js targets wrong theme APIs: window.theme.refreshCart doesn't exist and toast uses wrong CSS class | `shopify-theme/assets/diagnostic.js:572` |
| medium | — | Cart page +/− and Remove buttons update the server cart but the page never re-renders | `shopify-theme/sections/main-cart.liquid:19` |
| medium | — | Newsletter success confirmation throws ReferenceError: showToast is not defined | `shopify-theme/sections/newsletter.liquid:11` |
| medium | — | Cart drawer upsell '+' button does nothing: inline stopPropagation blocks the delegated quick-add handler | `shopify-theme/snippets/cart-drawer.liquid:87` |
| medium | — | Order email/DM shows wrong 'Total indicatif' — uses global cart total instead of the ordered items | `sneakers/index.html:878` |
| medium | — | Firebase Realtime Database used with no authentication and a shared default room — all synced data is world-readable/writable | `oral-medecine.html:917` |
| medium | — | Advertised 'notes personnelles par question' feature has no UI — state is persisted and synced but unreachable | `oral-medecine.html:1459` |
| medium | — | Light theme renders progress charts unreadable: hardcoded white/dark-theme colors in SVG charts | `oral-medecine.html:2419` |
| medium | — | Uploading ARED images can exceed localStorage quota and crash the whole app (unguarded setItem in useEffect) | `oral-medecine.html:1539` |
| medium | — | PWA/touch icons referenced but missing: icon-180.png, icon-192.png, icon-512.png do not exist | `sneakers/index.html:26` |
| medium | — | Navigation appears broken during a practice session: tab clicks change highlight but not content | `oral-medecine.html:2730` |
| medium | — | Root README documents only one of four projects shipped in the repo; committed zips violate the repo's own .gitignore | `README.md:1` |
| medium | — | Oral-prep app is keyboard-inaccessible: interactive divs with no roles, tabindex, or ARIA anywhere | `oral-medecine.html:1986` |
| low | — | Upsell exclusion uses substring matching on joined product IDs — false positives possible | `shopify-theme/snippets/cart-drawer.liquid:75` |
| low | — | Wishlist button label shows past tense 'Retiré de mes favoris' as the persistent active state | `shopify-theme/assets/wishlist.js:71` |
| low | — | Pagination current-page highlight never applies (string vs number comparison) | `shopify-theme/sections/main-collection.liquid:46` |
| low | — | SEO title tag misapplies join filter to the translation output instead of the tags array | `shopify-theme/layout/theme.liquid:33` |
| low | — | Streak/journal dates use UTC (toISOString) while streak math mixes local dates | `oral-medecine.html:1354` |
| low | — | Supabase project URL + anon key committed; app security depends entirely on unverifiable RLS/RPC configuration | `sneakers/index.html:593` |
| low | — | Inconsistent and partly dead exam-date data: DATA dates never rendered, duplicated 'Epreuves orales' stat tile, countdown hardcoded separately | `oral-medecine.html:2648` |
| low | — | console.log debug leftover announcing Firebase room in production | `oral-medecine.html:945` |
| low | — | Clipboard copy in phrases toolkit has no rejection handling or fallback | `oral-medecine.html:2503` |
| low | — | Enlarging a user-uploaded ARED image via window.open(dataURL) is blocked by modern browsers | `oral-medecine.html:2014` |
| low | — | Entire oral-prep UI is written in accent-stripped French ('Preparation Complete', 'Methodologie', 'A revoir') | `oral-medecine.html:6` |
| low | — | Cloud restore and sync listeners have no error callbacks — failures are silent while UI claims 'Sauvegarde cloud automatique active' | `oral-medecine.html:2551` |
| low | — | Import restores arbitrary keys from the JSON file and never validates shape | `oral-medecine.html:2585` |
### code-examen

| Sév. | Vérifié | Finding | Fichier |
|------|---------|---------|---------|
| high | ✅ confirmé (re-gradé medium) | Wrong answer key: flashing-green-light question contradicts its own explanation | `js/questions.js:236` |
| high | — | TOP IMPROVEMENT 1 — Question marks the wrong answer as correct (contradicts its own explanation) | `js/questions.js:236` |
| medium | — | SIGNS catalog mislabels B6d/B6a1 (and C24a), contradicting the app's own questions and showing wrong sign names in quiz and gallery | `js/questions.js:112` |
| medium | — | Service worker caches error responses unconditionally, can poison the offline cache | `sw.js:31` |
| medium | — | Off-by-one in goHome quit guard: no confirmation on the last question, and finishing state never recorded | `js/app.js:695` |
| medium | — | TOP IMPROVEMENT 1 (same pass) — Memo card teaches 12 ans for e-scooters while the quiz teaches 14 ans | `js/app.js:640` |
| medium | — | TOP IMPROVEMENT 2 — Primary navigation is keyboard-inaccessible clickable divs | `index.html:92` |
| medium | — | TOP IMPROVEMENT 3 — Sign gallery styled with undefined CSS variables (--card, --grey1) | `css/style.css:728` |
| medium | — | TOP IMPROVEMENT 3 (same feature) — 58 hotlinked Wikimedia images: no loading state, silent failure, empty gallery offline | `js/app.js:674` |
| medium | — | Unguarded JSON.parse of localStorage can permanently brick the whole app | `js/app.js:16` |
| medium | — | Streak counter ('Jours d'affilée') shows 0 every morning and caps at 7 | `js/app.js:130` |
| medium | — | 'Programme de révision' is a hardcoded one-off personal schedule that silently vanishes Wednesday–Saturday | `js/app.js:756` |
| low | — | Streak counter capped at 7 and resets to 0 until first answer of the day | `js/app.js:130` |
| low | — | Undefined CSS variables --card and --grey1 break sign-gallery styling | `css/style.css:728` |
| low | — | Latent XSS: question/answer/sign data rendered via innerHTML without escaping | `js/app.js:324` |
| low | — | Unvalidated JSON.parse of localStorage bricks the app if a key is corrupted | `js/app.js:16` |
| low | — | GitHub Pages production deploy triggered by pushes to a non-default feature branch | `.github/workflows/deploy.yml:5` |
| low | — | Quitting on the last question skips the 'Quitter le quiz ?' confirmation | `js/app.js:695` |
| low | — | Planning tasks never auto-complete: launchPlanningTask ignores its taskId parameter | `js/app.js:845` |
| low | — | Dead CSS: exam banner, tag-new, sr-badge warm/cool, reveal-correct are never rendered | `css/style.css:417` |
| low | — | Service worker caches error responses and has no offline navigation fallback | `sw.js:26` |
| low | — | Inconsistent French: half the hardcoded UI strings are missing accents | `js/app.js:265` |
| low | — | Quiz progress bar never reaches 100% | `js/app.js:279` |
| low | — | No README and an unverifiable 'Questions 2026 officielles' claim | `index.html:42` |
### nous-deux

| Sév. | Vérifié | Finding | Fichier |
|------|---------|---------|---------|
| high | ✅ confirmé (re-gradé medium) | GitHub Pages deploy is broken: Vite base path not set for project site | `vite.config.ts:6` |
| high | ✅ confirmé | Thoughts chat permanently freezes after 100 messages (fetches oldest 100, not newest) | `src/pages/Thoughts.tsx:40` |
| high | ✅ confirmé (re-gradé medium) | Global daily_questions table is writable by any authenticated user (cross-tenant content injection) | `src/components/Dashboard/QuestionWidget.tsx:38` |
| high | ✅ confirmé | GitHub Pages deployment is broken: no Vite base path and no SPA fallback for BrowserRouter | `vite.config.ts:6` |
| high | ✅ confirmé | Activities page is unreachable on mobile — bottom nav drops it entirely | `src/components/Layout/AppLayout.tsx:103` |
| high | ✅ confirmé | All Supabase writes are fire-and-forget: failed sends silently discard user input (data loss) and show success | `src/pages/Thoughts.tsx:64` |
| high | ✅ confirmé (re-gradé medium) | README-advertised Countdown feature has no create/edit UI — its only editor is dead, unmounted code | `src/pages/Dashboard.tsx:132` |
| medium | — | Sign-up race leaves profile null and renders a blank dashboard | `src/stores/authStore.ts:87` |
| medium | — | Activities page unreachable on mobile: bottom nav omits /activities | `src/components/Layout/AppLayout.tsx:103` |
| medium | — | Daily-question creation race produces duplicate rows and partners answering different questions | `src/pages/Dashboard.tsx:165` |
| medium | — | Question of the day never rotates: question_bank picked with limit(1), not randomly | `src/pages/Dashboard.tsx:163` |
| medium | — | GratitudeWidget delete-then-insert can permanently lose the day's gratitude entries | `src/components/Dashboard/GratitudeWidget.tsx:58` |
| medium | — | Time-capsule content is delivered to the client before the reveal date | `src/pages/Memories.tsx:41` |
| medium | — | Countdown feature has no reachable creation UI (CountdownWidget is never mounted) | `src/components/Dashboard/CountdownWidget.tsx:21` |
| medium | — | No SPA fallback for BrowserRouter on GitHub Pages: deep links and refresh 404 | `.github/workflows/deploy.yml:31` |
| medium | — | Streak and 'today' calculations use UTC day boundaries and undercount with a 60-row cap | `src/pages/Dashboard.tsx:121` |
| medium | — | Time-capsule content is sent to the client before the reveal date; secrecy is enforced only in the UI | `src/pages/Memories.tsx:41` |
| medium | — | Question answers fetched without couple scoping and filtered client-side; partner's answer delivered before user answers | `src/components/Dashboard/QuestionWidget.tsx:50` |
| medium | — | Tenant isolation rests entirely on unverifiable RLS: unscoped whole-table reads and client-chosen sender_id/created_by on writes | `src/pages/Thoughts.tsx:37` |
| medium | — | 'Question du jour' never rotates — the same first question_bank row is picked every day, with a duplicate-insert race | `src/pages/Dashboard.tsx:163` |
| medium | — | No loading states anywhere — every page flashes its empty-state copy while data is still fetching | `src/pages/Memories.tsx:161` |
| medium | — | Half the UI is written in accent-stripped French while the other half is correctly accented | `src/pages/SettingsPage.tsx:91` |
| medium | — | Six unmounted Dashboard widget components (~1,270 lines) duplicate live Dashboard logic — dead code hiding the only countdown editor | `src/components/Dashboard/CountdownWidget.tsx:21` |
| medium | — | Accessibility gaps: hover-only invisible delete buttons, unlabeled icon buttons, modals without dialog semantics, lang="en" on a French app | `src/pages/Memories.tsx:196` |
| medium | — | Thoughts composer silently does nothing when no partner is linked | `src/pages/Thoughts.tsx:61` |
| low | — | sendThought discards the message on failed insert and never confirms success | `src/pages/Thoughts.tsx:70` |
| low | — | Settings form can silently save an empty display name and initializes from a possibly-null profile | `src/pages/SettingsPage.tsx:40` |
| low | — | getTimeDiff rounds away fractional timezone offsets | `src/pages/Dashboard.tsx:32` |
| low | — | Dev notes indicate Supabase keys were previously exposed and rotation is still a pending manual action | `README.DEV_NOTES.md:12` |
| low | — | @tanstack/react-query is a dependency but never imported anywhere | `package.json:18` |
| low | — | Countdown display goes stale — remaining time is computed once at load and never ticks | `src/pages/Dashboard.tsx:137` |
| low | — | Calendar event form accepts end time before start time | `src/pages/CalendarPage.tsx:83` |
| low | — | Todo list progress counts only load on desktop mouse-hover — always missing on touch devices | `src/pages/Todos.tsx:291` |
| low | — | Login surfaces raw English Supabase error messages in an all-French UI | `src/pages/Login.tsx:26` |
| low | — | Gratitude widget has no realtime subscription — partner's entries only appear after a full reload | `src/components/Dashboard/GratitudeWidget.tsx:19` |
### streamflix

| Sév. | Vérifié | Finding | Fichier |
|------|---------|---------|---------|
| high | ✅ confirmé | Static export build fails: dynamic routes /film/[id] and /series/[id] lack generateStaticParams() | `src/app/film/[id]/page.tsx:6` |
| high | ✅ confirmé | Search page can never work and breaks the build: server component awaits searchParams under output:"export" | `src/app/search/page.tsx:6` |
| high | ✅ confirmé | Deploy workflow fails immediately: npm ci and setup-node cache require a package-lock.json that is not in the repo | `.github/workflows/deploy.yml:26` |
| high | ✅ confirmé (re-gradé medium) | Deploy workflow never provides NEXT_PUBLIC_TMDB_API_KEY, so the build-time TMDB fetches 401 and the export fails | `.github/workflows/deploy.yml:27` |
| high | ✅ confirmé | Build is broken: static export config is incompatible with the app's dynamic routes, so the GitHub Pages deploy can never succeed | `next.config.ts:4` |
| high | ✅ confirmé (re-gradé low) | README setup instructions do not work: wrong env var name and wrong local URL | `README.md:29` |
| high | ✅ confirmé (re-gradé low) | No error handling on any page except home: bad ID or TMDB failure yields a raw Next.js 500 screen | `src/app/film/[id]/page.tsx:9` |
| medium | — | README setup instructions use the wrong env var name (TMDB_API_KEY instead of NEXT_PUBLIC_TMDB_API_KEY) | `README.md:29` |
| medium | — | Image fallback points to /placeholder.jpg which does not exist and ignores the /streamflix basePath | `src/lib/tmdb.ts:6` |
| medium | — | Hero can render a trending person and link to a nonexistent /series/<personId> page | `src/app/page.tsx:40` |
| medium | — | TMDB API key is exposed in the public client bundle via NEXT_PUBLIC_ prefix | `src/lib/tmdb.ts:2` |
| medium | — | No .gitignore — developers are instructed to create .env.local with their API key, which git will happily commit | `README.md:29` |
| medium | — | README advertises cast on detail pages, but cast is not implemented anywhere | `README.md:8` |
| medium | — | Footer legal links are dead (href="#"): Mentions legales, Politique de confidentialite, CGU go nowhere | `src/components/Footer.tsx:25` |
| medium | — | Image fallback points to /placeholder.jpg which does not exist (and ignores basePath) | `src/lib/tmdb.ts:6` |
| medium | — | No .gitignore: node_modules, .next, and the .env.local containing the TMDB API key are all unignored | `README.md:28` |
| medium | — | Accessibility: unlabeled icon-only buttons, and carousel arrows that are keyboard-focusable while invisible | `src/components/Carousel.tsx:23` |
| low | — | Detail pages have no error/not-found handling: bad or unknown ids crash to the default error page | `src/app/film/[id]/page.tsx:9` |
| low | — | WatchProviders renders an empty 'Où regarder ?' box for provider payloads without flatrate/rent/buy, and provider chips lose their href when link is missing | `src/components/WatchProviders.tsx:56` |
| low | — | No .gitignore: node_modules, build output, and the user's .env.local API key file are all trackable | `package.json:1` |
| low | — | Language hardcoded to fr-FR and providers hardcoded to France, while README is entirely in English and never mentions it | `src/lib/tmdb.ts:13` |
| low | — | Dead code and template leftovers: unused Link import (lint fails out of the box) and five unused default Next.js SVGs | `src/app/page.tsx:5` |
| low | — | WatchProviders renders anchor tags without href and an empty-looking box when FR data is partial | `src/components/WatchProviders.tsx:22` |