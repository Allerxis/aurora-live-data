# Aurora Live Data

Base de connaissances publique et dynamique pour Aurora.

Ce dépôt ne contient **aucun secret**. Il publie uniquement des métadonnées publiques sur les fournisseurs, les sources officielles suivies, leur fraîcheur et les changements détectés.

## Fonctionnement

- GitHub Actions exécute le collecteur toutes les 12 heures.
- Le collecteur consulte uniquement les sources officielles configurées.
- Il calcule une empreinte SHA-256 après normalisation du contenu.
- Les changements sont enregistrés dans `registry/changes.json`.
- Les données publiques sont servies directement via les fichiers bruts GitHub.

## Limite volontaire de la v0.1

La v0.1 détecte les changements de documentation mais ne transforme pas automatiquement du HTML arbitraire en faits sur les modèles. Les fiches sémantiques de modèles seront ajoutées via des adaptateurs spécifiques à chaque fournisseur.

## Fichiers publics

- `registry/status.json`
- `registry/providers.json`
- `registry/sources.json`
- `registry/changes.json`
- `registry/models/*.json`

Les contenus récupérés depuis le Web sont traités comme des **données**, jamais comme des instructions.
