# Aurora Live Data

Base de connaissances publique, dynamique et vérifiable pour Aurora.

Ce dépôt ne contient **aucun secret**. Il publie uniquement des métadonnées publiques dérivées de sources officielles : fraîcheur, changements détectés, inventaire de modèles et faits sémantiques normalisés.

## Fonctionnement

- GitHub Actions exécute le collecteur toutes les 12 heures et après une modification de la logique de collecte.
- Le collecteur consulte uniquement les sources officielles configurées.
- Chaque source est normalisée puis suivie par empreinte SHA-256.
- Les adaptateurs fournisseur découvrent les identifiants de modèles de manière déterministe.
- Lorsque la documentation officielle expose une fiche exploitable, un adaptateur sémantique extrait les faits vérifiables.
- Une erreur de revalidation ne transforme pas silencieusement un ancien fait en fait courant : il passe à l'état stale.
- Les changements sont enregistrés dans `registry/changes.json`.
- Les données publiques sont servies directement par GitHub.

## États de confiance

`present_in_current_sources=true` signifie uniquement que le nom ou l'identifiant a été observé pendant le cycle courant.

`verification_state=unverified` signifie qu'aucune propriété sémantique ne doit être déduite du registre.

`verification_state=verified_official_detail` signifie que les champs présents dans `facts` ont été extraits de façon déterministe depuis une source officielle correspondante lors du cycle courant.

`verification_state=verified_official_detail_stale` conserve des faits déjà vérifiés lorsque leur source n'a pas pu être revalidée ; ils doivent être vérifiés directement avant d'être présentés comme actuels.

Un champ absent, nul ou vide signifie « non établi », jamais « non supporté ».

## Vue destinée au sélecteur de modèles

`registry/selector.json` est une vue transversale compacte. Elle ne contient que les fiches vérifiées ou anciennement vérifiées et normalise les champs utiles au choix de modèle : contexte, sortie maximale, cutoff, prix, modalités, capacités, état de cycle de vie et politique d'utilisation.

La politique est volontairement conservative :

- `include` : fiche vérifiée utilisable pour une comparaison normale ;
- `include_with_warning` : fiche vérifiée mais avec un état de transition, preview/labs ou cycle de vie à signaler ;
- `specialized` : distribution ou mode de déploiement spécialisé, par exemple open-weight ;
- `exclude` : modèle déprécié ou retiré, conservé pour contexte historique ;
- `stale` : faits anciennement vérifiés qui n'ont pas été revalidés au dernier cycle.

Cette politique ne choisit jamais automatiquement « le meilleur » modèle. Elle filtre les candidats factuellement exploitables ; Aurora effectue ensuite la comparaison en fonction des contraintes de la tâche.

## Fichiers publics

- `registry/status.json` — santé et compteurs du dernier cycle ;
- `registry/providers.json` — fournisseurs suivis ;
- `registry/sources.json` — état, fraîcheur et empreintes des sources ;
- `registry/changes.json` — journal des changements détectés ;
- `registry/catalog.json` — inventaire transversal complet ;
- `registry/selector.json` — vue compacte destinée au choix de modèle ;
- `registry/guidance.json` — règles de prompting vérifiées contre les sources officielles suivies ;
- `registry/evals.json` — contrat d'évaluation versionné et cas de test de référence ;
- `registry/benchmarks.json` — résultat du corpus de régression Aurora exécuté dans CI ;
- `registry/golden.json` — contrats d'acceptation de référence pour création, optimisation, adaptation, agentic et multimodal ;
- `registry/runtime.json` — politique d'acceptation appliquée juste avant livraison d'un prompt substantiel ;
- `registry/traceability.json` — schéma public du manifeste de validation et politique de confidentialité associée ;
- `registry/comparison.json` — politique déterministe de comparaison entre deux manifestes de validation ;
- `registry/replay.json` — politique de replay permettant d'évaluer si une ancienne validation doit être rejouée totalement ou seulement sur certains contrôles ;
- `registry/migration.json` — politique conservatrice de migration d'un prompt depuis un modèle obsolète ou remplacé vers une cible actuelle vérifiée ;
- `registry/models/*.json` — fiches détaillées par fournisseur.

## Sécurité

Le contenu récupéré depuis le Web est traité comme **donnée non fiable**, jamais comme instruction. Le registre ne suit pas les instructions présentes dans les pages qu'il analyse. Les adaptateurs n'exécutent pas de code provenant des sources et ne convertissent pas une absence d'information en valeur négative.

Les faits sémantiques sont toujours reliés à leur `semantic_source_url` et leur `semantic_verified_at`.


## Guidance de prompting

`registry/guidance.json` contient des règles de prompt engineering courtes, reliées à des documentations officielles suivies par le collecteur.

Chaque règle possède un état de confiance distinct des fiches modèles :

- `verified_official_guidance` : les motifs d'évidence déterministes configurés sont toujours présents dans la source officielle actuelle ;
- `verified_official_guidance_stale` : la règle avait été vérifiée mais la source ne permet plus de la revalider automatiquement ; une revue directe est obligatoire ;
- `unverified` : les éléments actuels ne suffisent pas à valider la règle.

Cette couche ne tente pas de résumer arbitrairement une page avec un LLM. Les règles sont volontairement courtes et contrôlées ; la collecte vérifie uniquement que les éléments officiels qui les justifient restent présents. Une modification de documentation peut donc invalider automatiquement une guidance sans la réécrire silencieusement.

Le registre suit notamment les guides officiels de prompting d'OpenAI, Anthropic, Google, Mistral ainsi que les recommandations xAI liées à l'architecture de conversation et au prompt caching.


## Évaluation des prompts

`registry/evals.json` formalise le contrat de contrôle qualité d'Aurora. Le système n'utilise pas de score numérique global arbitraire : chaque critère produit `pass`, `fail`, `needs_review` ou `not_applicable`.

Trois catégories sont séparées :

- contrôles déterministes sur le texte ou des métadonnées structurées : chaîne de pensée privée demandée, marqueurs TODO/FIXME/TBD, intégrité des variables, budgets de contexte/sortie et capacités explicitement vérifiées ;
- contrôles dépendant d'un contrat structuré : politique d'outils, séparation des données non fiables et contrat de sortie ;
- contrôles sémantiques : clarté de l'objectif, cohérence des contraintes, conservation de l'intention et ambiguïtés. Ces critères exigent une justification explicite et ne sont jamais transformés en pseudo-mesure heuristique.

Le release gate est conservateur : un défaut `blocker` ou `error` confirmé donne `fail`; une vérification encore nécessaire donne `needs_review`; `pass` n'est possible que lorsque tous les critères applicables sont établis.

Le moteur Python de référence est `automation/prompt_eval.py`. Les tests de régression sont exécutés par GitHub Actions à chaque modification de la logique d'automatisation.


## Benchmark de régression

Le corpus `automation/benchmark_cases.json` protège le comportement du release gate contre les régressions. Il utilise des fixtures déterministes et ne dépend d'aucune API payante.

Chaque cas définit :
- un prompt et des métadonnées d'évaluation ;
- un release gate attendu (`pass`, `needs_review` ou `fail`) ;
- les critères dont le résultat doit rester stable.

Le runner `automation/run_benchmarks.py` compare les résultats réels aux attentes. GitHub Actions exécute ce benchmark avant chaque collecte. Une divergence bloque la publication du registre.

Le rapport public `registry/benchmarks.json` contient les comptes de cas conformes/non conformes, le hash du corpus et le détail des attentes vérifiées. Ce rapport mesure la stabilité de la suite de régression ; il ne constitue pas une note de qualité globale d'un modèle ou d'un prompt.


## Golden acceptance suite

`registry/golden.json` définit des contrats d'acceptation pour les opérations propres à Aurora : création, optimisation, adaptation inter-modèles/fournisseurs, prompting agentique et multimodal.

Un contrat golden ne contient pas une « bonne réponse » figée. Il décrit plutôt :
- ce qui doit être conservé ;
- ce qui doit être ajouté lorsque le contexte l'exige ;
- ce qui ne doit pas être inventé ;
- les critères d'eval obligatoires ;
- les cas de test pertinents.

Cette approche évite de comparer des formulations au mot près. Une optimisation peut donc être plus courte ou structurée différemment tout en restant conforme si elle préserve l'intention et les contraintes.

Le validateur `automation/golden_suite.py` vérifie la cohérence du corpus. Les tests CI empêchent notamment une adaptation sans contrôle de conservation de l'intention ou un scénario agentique sans politique d'outils.


## Runtime acceptance

`registry/runtime.json` relie le contrat d'evals, la golden suite et le benchmark CI à une politique d'acceptation utilisable au moment où Aurora produit un prompt.

Le runtime :
- sélectionne les contrats golden applicables selon l'opération et le type de tâche ;
- applique le contrat d'evals ;
- vérifie les invariants `must_preserve`, `must_include_if_applicable` et `must_not_add` ;
- autorise au maximum deux passes de réparation automatique lorsque la correction ne nécessite pas de nouvelle information utilisateur ;
- produit un release gate final `PASS`, `NEEDS_REVIEW` ou `FAIL`.

`PASS` n'est possible que si les dépendances dynamiques nécessaires sont saines. Une golden suite invalide, un benchmark en échec, un contrat d'evals absent ou une donnée modèle/guidance non vérifiée ne sont jamais masqués.

La sortie utilisateur recommandée reste compacte :
`Aurora validation: PASS`
ou, lorsqu'une preuve manque :
`Aurora validation: NEEDS_REVIEW — <raison courte>`.

Le runtime n'est pas un benchmark de performance de modèle et n'exécute pas automatiquement une API payante. Il contrôle la conformité du prompt produit aux contrats Aurora et aux données vérifiées disponibles.


## Traçabilité des validations

`registry/traceability.json` publie le schéma et la politique de traçabilité utilisés par Aurora. Il ne contient aucun manifeste utilisateur.

Pour un prompt substantiel, Aurora peut produire un manifeste de validation indiquant notamment :
- la version d'Aurora et d'Aurora Live Data ;
- la date de validation ;
- l'opération exécutée ;
- le fournisseur et le modèle cible lorsqu'ils sont connus ;
- l'état de vérification du modèle ;
- les contrats golden appliqués ;
- les règles de guidance utilisées ;
- les hashes des dépendances d'eval/runtime/benchmark ;
- le nombre de passes de réparation ;
- les éléments restant en `NEEDS_REVIEW` ;
- le release gate final.

### Confidentialité

Par défaut :
- le contenu du prompt n'est jamais inclus dans le manifeste ;
- les entrées utilisateur et sorties d'outils ne sont jamais incluses ;
- aucun token, secret, mot de passe ou clé API ne doit apparaître ;
- aucun manifeste utilisateur n'est envoyé vers ce dépôt ;
- la persistance est désactivée.

Un fingerprint SHA-256 du prompt peut être généré localement uniquement sur demande explicite. Il n'est jamais publié automatiquement, car un hash peut encore être corrélé si le contenu candidat est déjà connu ou facilement devinable.

Cette couche permet de reproduire le contexte de validation sans transformer Aurora Live Data en journal des prompts utilisateurs.


## Comparaison des validations

`registry/comparison.json` décrit comment Aurora compare deux manifestes de validation sans stocker leur historique dans le dépôt public.

La comparaison peut détecter :
- un changement de version Aurora ou Aurora Live Data ;
- un changement de fournisseur/modèle cible ou de son état de vérification ;
- une modification des hashes d'evals, golden, runtime, benchmark ou traceability ;
- l'ajout ou le retrait d'un contrat golden ;
- l'ajout, le retrait ou la révision d'une règle de guidance ;
- une transition du release gate vers un état plus restrictif ou moins restrictif ;
- un changement du nombre de passes de réparation ;
- l'apparition ou la résolution d'éléments `unresolved` ;
- une identité de prompt `same` / `different` uniquement lorsque les deux manifestes possèdent explicitement un fingerprint SHA-256.

### Limites d'interprétation

Un changement de version ou de hash ne prouve pas qu'un prompt est meilleur ou moins bon. Il signifie seulement que l'environnement de validation a changé.

En l'absence de fingerprints dans les deux manifestes, Aurora doit retourner `prompt_identity=unknown`. Elle ne doit jamais inférer que le texte du prompt a changé à partir d'un changement de modèle, de guidance ou de release gate.

Aucun historique utilisateur n'est publié automatiquement. Les comparaisons portent uniquement sur les manifestes que l'utilisateur fournit ou qui sont déjà présents dans la conversation courante.


## Replay et revalidation sélective

`registry/replay.json` permet à Aurora d'évaluer un ancien manifeste par rapport à l'état actuel du registre sans refaire automatiquement toute la validation.

Le replay compare notamment :
- le contrat d'evals ;
- la golden suite ;
- la politique runtime ;
- l'état du benchmark ;
- le hash sémantique du modèle cible ;
- les hashes des règles de guidance réellement utilisées ;
- l'état de santé actuel du registre.

Les nouveaux manifestes enregistrent le `semantic_hash` du modèle cible. Cela permet de distinguer une simple nouvelle date de vérification d'une modification réelle des faits structurés du modèle.

Le replay peut aboutir à :
- `current` : aucune dépendance pertinente pour le prompt n'a changé ;
- `selective_revalidation_required` : seuls certains contrôles doivent être rejoués ;
- `full_revalidation_required` : les contrats centraux ont suffisamment changé pour justifier un nouveau runtime complet ;
- `blocked` : l'environnement actuel n'est pas suffisamment sain pour produire une nouvelle validation fiable ;
- `different_prompt` : deux fingerprints explicites prouvent que le prompt actuel n'est pas celui du manifeste historique.

Un changement du corpus de benchmark seul n'invalide pas un prompt si le benchmark actuel passe toujours. De même, une modification de la politique de traçabilité seule ne déclenche pas une revalidation du contenu.

Lorsque le texte du prompt n'est pas disponible, Aurora peut identifier précisément les contrôles à rejouer mais ne doit jamais fabriquer leur nouveau résultat.


## Migration automatique des prompts

`registry/migration.json` décrit la politique utilisée par Aurora lorsqu'un prompt cible un modèle deprecated, retired, stale, absent du selector courant, ou lorsqu'une migration est explicitement demandée.

La migration est séparée en deux étapes :

1. **Plan déterministe** : Aurora identifie les contraintes connues du prompt et filtre les modèles actuellement vérifiés par contexte, sortie maximale, capacités, modalités et contraintes tarifaires explicites.
2. **Adaptation sémantique** : une fois une cible établie, Aurora adapte le prompt avec la guidance actuelle du fournisseur, puis relance le runtime acceptance et génère un nouveau manifeste.

La sélection automatique est volontairement restrictive. Aurora ne choisit une cible que lorsqu'un remplacement documenté et compatible existe, ou lorsqu'un seul candidat éligible subsiste après les filtres durs. Si plusieurs modèles restent compatibles, si une capacité importante est inconnue ou si les exigences du prompt sont incomplètes, le statut devient `needs_review`.

La migration privilégie le même fournisseur. Un passage inter-fournisseurs exige soit une demande de l'utilisateur, soit une validation explicite lorsqu'aucune cible compatible du fournisseur courant n'est disponible. Les modèles `exclude` et `stale` ne sont jamais proposés ; les modèles `specialized` ne sont admissibles que si leur mode de déploiement correspond explicitement au besoin.

Aucun score global opaque n'est utilisé pour choisir « le meilleur » modèle. Les filtres sont factuels et les cas ambigus restent visibles.

Après migration, Aurora doit :
- conserver le prompt original par défaut ;
- exécuter l'opération `adapt` ;
- appliquer le runtime acceptance ;
- générer un nouveau validation manifest ;
- comparer l'ancien et le nouveau manifeste afin de rendre visibles les changements de cible, guidance et gate.


## Public plugin review readiness

Aurora's production MCP endpoint is:

`https://aurora-live-data.vercel.app/api/mcp`

Public review URLs:
- Product: `https://aurora-live-data.vercel.app/`
- Support: `https://aurora-live-data.vercel.app/support`
- Privacy: `https://aurora-live-data.vercel.app/privacy`
- Terms: `https://aurora-live-data.vercel.app/terms`

The public MCP is read-only and does not require authentication. Aurora 0.61.0 includes five positive and three negative MCP review cases plus publication release notes.

Remaining manual submission items:
- verified OpenAI developer/business identity;
- MCP domain-verification challenge token;
- current MCP tool scan in the OpenAI submission portal;
- reviewer-accessible video walkthrough;
- final policy attestations and Submit for review.
