# SenPrinTech

Site e-commerce Django pour SenPrinTech, service d'impression digitale (flyers, cartes de visite, textile, objets personnalises, impression entreprise).

## Fonctionnalites

- Catalogue produits avec options configurables (format, papier, quantite, fichiers client...)
- Panier et tunnel de commande avec paiement assiste Wave / Orange Money via WhatsApp
- Comptes clients avec verification email et suivi de commandes/devis
- Demande de devis entreprise et formulaire de contact, avec notifications email automatiques
- Panneau d'administration personnalise pour gerer produits, commandes, devis et demandes de contact

## Stack technique

- Django 5.1
- SQLite en developpement, PostgreSQL en production
- WhiteNoise pour les fichiers statiques
- Gunicorn pour le serveur de production

## Deploiement

Voir [DEPLOY_RENDER.md](DEPLOY_RENDER.md) pour la procedure complete de deploiement sur Render.
