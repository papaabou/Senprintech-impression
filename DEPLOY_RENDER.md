# Déploiement Render - SenPrinTech

Ce projet Django est préparé pour Render avec PostgreSQL, Gunicorn, WhiteNoise, variables d'environnement, fichiers statiques et médias uploadés.

## 1. Déploiement depuis GitHub

### Option recommandée : Blueprint

1. Pousser le projet sur GitHub.
2. Aller sur Render Dashboard.
3. Cliquer sur `New` puis `Blueprint`.
4. Sélectionner le dépôt GitHub.
5. Render détecte `render.yaml`.
6. Renseigner les variables secrètes demandées :
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`
7. Lancer le déploiement.

### Option manuelle : Web Service

Créer un `Web Service` Python avec :

```bash
Build Command:
bash build.sh

Start Command:
gunicorn ecommercesite.wsgi:application
```

Créer aussi une base PostgreSQL Render, puis copier son `External Database URL` ou `Internal Database URL` dans `DATABASE_URL`.

## 2. Variables d'environnement Render

```env
SECRET_KEY=une-longue-cle-secrete-generee
DEBUG=False
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
DATABASE_URL=postgresql://...

ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@senprintech.com
ADMIN_PASSWORD=mot-de-passe-admin-fort

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SERVE_MEDIA_FILES=True
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=True
MEDIA_ROOT=/var/data/mediafiles

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_HOST_USER=papeaboumbaye@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
DEFAULT_FROM_EMAIL=SenPrinTech <papeaboumbaye@gmail.com>
QUOTE_ADMIN_EMAIL=papeaboumbaye@gmail.com
```

Pour un domaine personnalisé, ajouter aussi :

```env
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com,.onrender.com
CSRF_TRUSTED_ORIGINS=https://votre-domaine.com,https://www.votre-domaine.com,https://*.onrender.com
```

## 3. Fichiers statiques

Render exécute :

```bash
python manage.py collectstatic --no-input
```

WhiteNoise sert les fichiers statiques depuis `STATIC_ROOT`.

## 4. Fichiers médias uploadés

Les fichiers clients sont stockés dans :

```bash
/var/data/mediafiles
```

Le `render.yaml` ajoute un disque persistant :

```yaml
disk:
  name: senprintech-media
  mountPath: /var/data
  sizeGB: 1
```

Sans disque persistant, les fichiers uploadés peuvent disparaître après redéploiement.

## 5. Migrations en production

Le script `build.sh` exécute déjà :

```bash
python manage.py migrate --no-input
```

Pour relancer manuellement depuis Render :

1. Ouvrir le service Render.
2. Aller dans `Shell`.
3. Lancer :

```bash
python manage.py migrate
```

## 6. Créer le superuser admin

Le build lance `python manage.py create_initial_superuser`.
Cette commande crée `admin` seulement si aucun superuser n'existe déjà.
Elle ne modifie pas le mot de passe à chaque déploiement.

Variables Render obligatoires pour l'admin initial :

```env
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@senprintech.com
ADMIN_PASSWORD=mot-de-passe-admin-fort
```

Depuis le Shell Render si disponible :

```bash
python manage.py createsuperuser
```

Puis ouvrir :

```text
https://votre-service.onrender.com/admin/
```

## 7. Seed du catalogue SenPrinTech

Après migrations, lancer si nécessaire :

```bash
python manage.py seed_senprintech
```

## 8. Erreurs fréquentes

### 400 Bad Request

Cause probable : `ALLOWED_HOSTS` incorrect.

Correction :

```env
ALLOWED_HOSTS=votre-service.onrender.com,.onrender.com
```

### CSRF verification failed

Cause probable : domaine absent de `CSRF_TRUSTED_ORIGINS`.

Correction :

```env
CSRF_TRUSTED_ORIGINS=https://votre-service.onrender.com
```

### Static files missing

Vérifier :

```bash
python manage.py collectstatic --no-input
```

et que `whitenoise.middleware.WhiteNoiseMiddleware` est juste après `SecurityMiddleware`.

### Uploads disparus après redéploiement

Cause : pas de disque persistant.

Correction : ajouter le disque Render et garder :

```env
MEDIA_ROOT=/var/data/mediafiles
SERVE_MEDIA_FILES=True
```

### Gmail n'envoie pas les emails

Utiliser un mot de passe d'application Gmail, pas le mot de passe normal.

Activer la validation en 2 étapes, puis créer le mot de passe ici :

```text
https://myaccount.google.com/apppasswords
```

### Base SQLite utilisée en production

Cause : `DATABASE_URL` absent.

Correction : créer une base PostgreSQL Render et ajouter `DATABASE_URL`.
Sans base persistante, les utilisateurs créés en production peuvent disparaître après redéploiement et les connexions échouent.

### Inscription créée mais connexion refusée

Cause probable : le compte est créé avec `is_active=False` en attendant le code email.
Si Gmail/SMTP n'est pas configuré avec un mot de passe d'application valide, le client ne reçoit pas le code et `authenticate()` refuse la connexion.

Correction :

```env
EMAIL_HOST_USER=papeaboumbaye@gmail.com
EMAIL_HOST_PASSWORD=mot-de-passe-application-gmail
```

Solution temporaire si Gmail bloque encore :

```env
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=False
```

Avec cette valeur, le client est activé et connecté directement après inscription.
