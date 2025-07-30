# ⚡ Configuration PayPal - 5 Minutes Chrono !

## 🎯 **ÉTAPE 1 : Créer votre PayPal.me**

1. **Allez sur** : https://www.paypal.com/paypalme/
2. **Cliquez** : "Créer votre lien PayPal.me"
3. **Choisissez** : `paypal.me/VOTRE-NOM`
   - Exemple : `paypal.me/cafe-delices` ou `paypal.me/marie-coiffure`

## 🔧 **ÉTAPE 2 : Personnaliser votre Code**

### **Fichier à modifier** : `/app/backend/server.py`

**Ligne ~880, remplacez :**
```python
# AVANT (ligne actuelle)
return f"https://paypal.me/aiwebgen/{price}EUR"

# APRÈS (votre PayPal)
return f"https://paypal.me/VOTRE-NOM/{price}EUR"
```

### **Exemple concret :**
```python
# Si votre PayPal.me est : paypal.me/salon-marie
return f"https://paypal.me/salon-marie/{price}EUR"
```

## 🚀 **ÉTAPE 3 : Redémarrer le Système**

```bash
sudo supervisorctl restart backend
```

## ✅ **ÉTAPE 4 : Tester**

```bash
curl -X POST https://votre-url.com/api/test/concierge/demo
```

**Résultat attendu :**
```json
{
  "payment_link": "https://paypal.me/VOTRE-NOM/49.0EUR"
}
```

---

## 💡 **Exemples de Noms PayPal**

| Type Business | PayPal.me Suggéré |
|---------------|-------------------|
| Coiffeur | `paypal.me/salon-marie` |
| Restaurant | `paypal.me/bistrot-paul` |
| Boulangerie | `paypal.me/boulangerie-martin` |
| Conseil | `paypal.me/conseil-julie` |
| E-commerce | `paypal.me/boutique-mode` |

---

## 🎉 **C'est Tout !**

**En 5 minutes**, votre système de conciergerie automatisée est opérationnel avec PayPal !

Les clients pourront payer directement via votre lien personnalisé et vous recevrez une notification instantanée.

---

## 📧 **Bonus : Notification Automatique**

PayPal vous enverra automatiquement un email à chaque paiement reçu. Vous pourrez alors déclencher l'automatisation manuellement ou configurer les webhooks PayPal pour une automatisation 100% complète.

**Votre conciergerie automatisée est maintenant prête ! 🚀**