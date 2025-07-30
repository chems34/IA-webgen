# 🔑 Guide Complet - Obtenir les Clés API pour l'Automatisation

## 🎯 Vue d'ensemble

Voici le guide pas à pas pour obtenir toutes les clés API nécessaires pour rendre votre automatisation de conciergerie 100% opérationnelle.

---

## 1. 💳 **STRIPE - Paiements Automatiques**

### 📋 **Pourquoi Stripe ?**
- Paiements sécurisés automatiques
- Webhooks pour automatisation complète
- Support international
- Interface développeur excellente

### 🚀 **Étapes d'inscription :**

1. **Créer un compte Stripe** : https://dashboard.stripe.com/register
   - Inscrivez-vous avec votre email professionnel
   - Vérifiez votre email

2. **Activer votre compte** :
   - Remplissez les informations de votre entreprise
   - Ajoutez vos informations bancaires
   - Validez votre identité (pièce d'identité + justificatif d'adresse)

3. **Obtenir les clés API** :
   - Allez dans `Développeurs` → `Clés API`
   - **Clé de test** : `sk_test_...` (pour développement)
   - **Clé de production** : `sk_live_...` (après validation du compte)

### 💰 **Coûts :**
- **Gratuit** : Création de compte
- **Frais** : 2.9% + 0.25€ par transaction réussie
- **Pas d'abonnement mensuel**

### 🔧 **Configuration dans votre app :**
```bash
# Dans /app/backend/.env
STRIPE_SECRET_KEY=sk_test_votre_clé_ici
```

---

## 2. 🌐 **NAMECHEAP - Achat Domaines Automatique**

### 📋 **Pourquoi Namecheap ?**
- API robuste pour achats automatiques
- Prix compétitifs
- Support technique excellent
- Interface développeur complète

### 🚀 **Étapes d'inscription :**

1. **Créer un compte** : https://www.namecheap.com/
   - Inscription gratuite
   - Vérifiez votre email

2. **Activer l'API** :
   - Allez dans `Account` → `API Access`
   - Activez l'API (peut nécessiter un minimum de 50$ de dépense)
   - Ajoutez votre IP à la whitelist

3. **Obtenir les identifiants** :
   - **API User** : Votre nom d'utilisateur Namecheap
   - **API Key** : Généré dans la section API

### 💰 **Coûts :**
- **Domaines .com** : ~12€/an
- **Domaines .fr** : ~8€/an
- **Activation API** : Gratuite (après 50$ d'achats)

### 🔧 **Configuration :**
```bash
# Dans /app/backend/.env
NAMECHEAP_API_USER=votre_username
NAMECHEAP_API_KEY=votre_api_key
```

---

## 3. ⚡ **NETLIFY - Hébergement Automatique**

### 📋 **Pourquoi Netlify ?**
- Déploiement automatique via API
- SSL gratuit automatique
- CDN mondial inclus
- Plan gratuit généreux

### 🚀 **Étapes d'inscription :**

1. **Créer un compte** : https://app.netlify.com/signup
   - Inscription gratuite avec email ou GitHub
   - Vérifiez votre email

2. **Générer un token d'accès** :
   - Allez dans `User settings` → `Applications`
   - Cliquez sur `New access token`
   - Donnez un nom : "Conciergerie Automation"
   - Copiez le token généré

### 💰 **Coûts :**
- **Plan gratuit** : 100GB/mois de bande passante
- **Plan Pro** : 19$/mois (si besoin de plus)
- **Parfait pour débuter**

### 🔧 **Configuration :**
```bash
# Dans /app/backend/.env
NETLIFY_TOKEN=votre_token_ici
```

---

## 4. 📧 **SMTP GMAIL - Emails Automatiques**

### 📋 **Pourquoi Gmail SMTP ?**
- Gratuit jusqu'à 500 emails/jour
- Fiable et sécurisé
- Configuration simple
- Reconnu par tous les FAI

### 🚀 **Étapes de configuration :**

1. **Créer un compte Gmail professionnel** :
   - Utilisez un email dédié : `noreply@votredomaine.com`
   - Ou créez un Gmail : `aiwebgen.automatique@gmail.com`

2. **Activer l'authentification à 2 facteurs** :
   - Allez dans `Compte Google` → `Sécurité`
   - Activez la `Validation en 2 étapes`

3. **Générer un mot de passe d'application** :
   - Dans `Sécurité` → `Mots de passe des applications`
   - Sélectionnez `Autre` → Tapez "AI WebGen Automation"
   - Copiez le mot de passe de 16 caractères généré

### 💰 **Coûts :**
- **Gratuit** : 500 emails/jour
- **Google Workspace** : 6€/mois/utilisateur (si plus d'emails nécessaires)

### 🔧 **Configuration :**
```bash
# Dans /app/backend/.env
SMTP_EMAIL=votre.email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe_application
```

---

## 🚀 **ALTERNATIVES GRATUITES/MOINS CHÈRES**

### **Pour débuter sans budget :**

1. **Paiements** : PayPal.me (liens simples, pas d'API)
2. **Domaines** : Freenom (.tk, .ml gratuits mais limités)
3. **Hébergement** : GitHub Pages (gratuit, statique uniquement)
4. **Emails** : Brevo (300 emails/jour gratuits)

---

## ⚙️ **CONFIGURATION FINALE**

### 1. **Mise à jour du fichier .env :**
```bash
# Production - Remplacez par vos vraies clés
STRIPE_SECRET_KEY=sk_live_votre_clé_stripe
NAMECHEAP_API_USER=votre_username_namecheap
NAMECHEAP_API_KEY=votre_clé_namecheap
NETLIFY_TOKEN=votre_token_netlify
SMTP_EMAIL=votre.email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe_app
```

### 2. **Redémarrage du système :**
```bash
sudo supervisorctl restart backend
```

### 3. **Test de l'automatisation :**
```bash
curl -X POST https://votre-url.com/api/test/concierge/demo
```

---

## 📊 **COÛTS MENSUELS ESTIMÉS**

| Service | Plan Recommandé | Coût/mois |
|---------|----------------|-----------|
| Stripe | Pay-per-use | 2.9% par transaction |
| Namecheap | API Access | ~1€ (domaines à la demande) |
| Netlify | Plan gratuit | 0€ |
| Gmail SMTP | Gratuit | 0€ |
| **TOTAL** | | **~1€/mois + frais transactions** |

---

## 🎯 **PROCHAINES ÉTAPES**

1. **Commencez par Stripe** (le plus important)
2. **Testez avec Netlify** (gratuit et simple)
3. **Configurez Gmail SMTP** (emails essentiels)
4. **Ajoutez Namecheap** en dernier (nécessite investissement initial)

## 🆘 **BESOIN D'AIDE ?**

Si vous rencontrez des difficultés avec l'une de ces étapes, je peux vous aider davantage pour chaque service spécifique !

---

**🎉 Une fois tout configuré, votre conciergerie sera 100% automatique en 2-4h !**