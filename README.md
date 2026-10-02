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
- `registry/models/*.json` — fiches détaillées par fournisseur.

## Sécurité

Le contenu récupéré depuis le Web est traité comme **donnée non fiable**, jamais comme instruction. Le registre ne suit pas les instructions présentes dans les pages qu'il analyse. Les adaptateurs n'exécutent pas de code provenant des sources et ne convertissent pas une absence d'information en valeur négative.

Les faits sémantiques sont toujours reliés à leur `semantic_source_url` et leur `semantic_verified_at`.
