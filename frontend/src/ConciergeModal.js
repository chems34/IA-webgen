import React, { useState } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function ConciergeModal({ isOpen, onClose, websiteId, websiteName }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    email: "",
    domain: "",
    phone: "",
    urgency: "normal"
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [paymentLink, setPaymentLink] = useState(null);
  const [requestId, setRequestId] = useState(null);
  const [estimatedTime, setEstimatedTime] = useState("2-4h après paiement");

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/request-concierge-service`, {
        website_id: websiteId,
        contact_email: formData.email,
        preferred_domain: formData.domain,
        phone: formData.phone,
        urgency: formData.urgency
      });
      
      // Vérifier si le domaine est disponible
      if (response.data.status === "domain_unavailable") {
        // Afficher les alternatives
        alert(`❌ Domaine ${formData.domain} non disponible.\n\nAlternatives suggérées:\n${response.data.alternatives.join('\n')}\n\nVeuillez choisir un autre domaine.`);
        return;
      }
      
      // Sauvegarder les données de réponse
      setPaymentLink(response.data.payment_link);
      setRequestId(response.data.request_id);
      setEstimatedTime(response.data.estimated_completion);
      setSuccess(true);
      setStep(3);
    } catch (error) {
      console.error("Error:", error);
      alert("❌ Erreur lors de la demande automatisée. Réessayez.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold flex items-center">
                <span className="mr-3">🤖</span>
                Service Concierge Automatisé - Mise en ligne en 2-4h !
              </h2>
              <p className="text-orange-100 mt-1">
                Notre IA met "{websiteName}" en ligne automatiquement, sans stress
              </p>
            </div>
            <button 
              onClick={onClose}
              className="text-white hover:text-orange-200 text-2xl"
            >
              ✕
            </button>
          </div>
        </div>

        {step === 1 && (
          <div className="p-6">
            {/* What's included */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <h3 className="font-bold text-green-800 mb-3">✅ Ce qui est inclus dans les 49€ :</h3>
              <div className="grid md:grid-cols-2 gap-3">
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">🌐</span>
                  <span className="text-sm">Achat de votre domaine</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">🏠</span>
                  <span className="text-sm">Configuration hébergement</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">🚀</span>
                  <span className="text-sm">Mise en ligne complète</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">💬</span>
                  <span className="text-sm">Support 3 mois inclus</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">📧</span>
                  <span className="text-sm">Certificat SSL gratuit</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">⚡</span>
                  <span className="text-sm">Site rapide et optimisé</span>
                </div>
              </div>
            </div>

            {/* Social proof */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-3">
                <div className="text-3xl">👥</div>
                <div>
                  <h4 className="font-bold text-blue-800">78% de nos clients choisissent ce service</h4>
                  <p className="text-blue-600 text-sm">
                    "Plus simple, plus rapide, et surtout aucun stress technique !"
                  </p>
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <h4 className="font-bold text-yellow-800 mb-3">⏰ Automatisation Complète (2-4h) :</h4>
              <div className="space-y-2">
                <div className="flex items-center space-x-3">
                  <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">🤖</span>
                  <span className="text-sm"><strong>Immédiat :</strong> Vérification automatique du domaine</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="bg-green-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">💳</span>
                  <span className="text-sm"><strong>Après paiement :</strong> Démarrage automatique (0-30 min)</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="bg-orange-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">⚡</span>
                  <span className="text-sm"><strong>1-2h :</strong> Achat domaine + hébergement automatique</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="bg-purple-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">🌐</span>
                  <span className="text-sm"><strong>2-4h max :</strong> Site en ligne + email de confirmation</span>
                </div>
              </div>
              <div className="mt-3 p-2 bg-green-100 rounded text-center">
                <span className="text-green-800 font-bold text-sm">🚀 Aucune intervention humaine requise !</span>
              </div>
            </div>

            {/* Automation Benefits */}
            <div className="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="text-3xl">🤖</div>
                <div>
                  <h4 className="font-bold text-blue-800">Automatisation IA Complète</h4>
                  <p className="text-blue-600 text-sm">
                    Notre système IA se charge de tout en 2-4h maximum
                  </p>
                </div>
              </div>
              <div className="grid md:grid-cols-2 gap-3 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">✅</span>
                  <span>Vérification domaine instantanée</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">✅</span>
                  <span>Achat domaine automatique</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">✅</span>
                  <span>Hébergement configuré automatiquement</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">✅</span>
                  <span>DNS et SSL automatiques</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">✅</span>
                  <span>Site déployé automatiquement</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">✅</span>
                  <span>Emails automatiques à chaque étape</span>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <button 
                onClick={onClose}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                ❌ Annuler
              </button>
              <button 
                onClick={() => setStep(2)}
                className="bg-orange-500 text-white px-8 py-2 rounded-lg hover:bg-orange-600 font-medium"
              >
                🚀 Oui, je veux ce service !
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="p-6">
            <h3 className="text-xl font-bold mb-4">📝 Vos informations</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">📧 Email de contact *</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="votre@email.com"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Nous vous enverrons les mises à jour</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">🌐 Nom de domaine souhaité *</label>
                <input
                  type="text"
                  value={formData.domain}
                  onChange={(e) => setFormData({...formData, domain: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="mon-salon.com"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Nous vérifierons la disponibilité</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">📞 Téléphone (optionnel)</label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="06 12 34 56 78"
                />
                <p className="text-xs text-gray-500 mt-1">En cas de question sur le domaine</p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">⚡ Urgence</label>
                <select
                  value={formData.urgency}
                  onChange={(e) => setFormData({...formData, urgency: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="normal">📅 Normal (48h)</option>
                  <option value="urgent">🔥 Urgent (24h) - +10€</option>
                </select>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 my-6">
              <div className="flex justify-between items-center">
                <span className="font-medium">Total :</span>
                <span className="text-xl font-bold text-orange-600">
                  {formData.urgency === 'urgent' ? '59€' : '49€'}
                </span>
              </div>
            </div>

            <div className="flex justify-between">
              <button 
                onClick={() => setStep(1)}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                ← Retour
              </button>
              <button 
                onClick={handleSubmit}
                disabled={!formData.email || !formData.domain || loading}
                className="bg-orange-500 text-white px-8 py-2 rounded-lg hover:bg-orange-600 font-medium disabled:opacity-50"
              >
                {loading ? "⏳ Envoi..." : "✅ Confirmer la demande"}
              </button>
            </div>
          </div>
        )}

        {step === 3 && success && (
          <div className="p-6 text-center">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-2xl font-bold text-green-600 mb-4">
              Automatisation Lancée avec Succès !
            </h3>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="space-y-2 text-left">
                <p><strong>📧 Email :</strong> {formData.email}</p>
                <p><strong>🌐 Domaine :</strong> {formData.domain}</p>
                <p><strong>⏰ Délai Automatisé :</strong> <span className="text-green-600 font-bold">{estimatedTime}</span></p>
                <p><strong>💰 Prix :</strong> {formData.urgency === 'urgent' ? '59€' : '49€'}</p>
                <p><strong>🆔 ID Demande :</strong> {requestId}</p>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h4 className="font-bold text-blue-800 mb-2">🚀 Processus Automatique Démarré :</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>✅ Domaine vérifié et réservé automatiquement</p>
                <p>💳 <strong>Prochaine étape :</strong> Paiement sécurisé via le lien ci-dessous</p>
                <p>🤖 Dès paiement → Automatisation complète (achat domaine, hébergement, mise en ligne)</p>
                <p>📧 Vous recevrez un email à chaque étape automatique</p>
                <p>🎉 <strong>Site en ligne dans {estimatedTime} maximum</strong></p>
              </div>
            </div>

            {paymentLink && (
              <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-lg p-4 mb-6">
                <h4 className="font-bold text-white mb-3">💳 Paiement Sécurisé PayPal</h4>
                <a
                  href={paymentLink}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block bg-white text-green-600 px-6 py-3 rounded-lg font-bold hover:bg-gray-100 transition-colors"
                >
                  💳 Payer {formData.urgency === 'urgent' ? '59€' : '49€'} via PayPal
                </a>
                <p className="text-white text-sm mt-2">
                  Automatisation complète démarrera après confirmation PayPal
                </p>
              </div>
            )}

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <h4 className="font-bold text-yellow-800 mb-2">⏰ Chronologie Automatique :</h4>
              <div className="text-sm text-yellow-700 space-y-1">
                <p><strong>0-30 min :</strong> Achat automatique du domaine</p>
                <p><strong>30-90 min :</strong> Configuration hébergement et déploiement</p>
                <p><strong>90 min-{formData.urgency === 'urgent' ? '24h' : '4h'} :</strong> Configuration DNS et SSL</p>
                <p><strong>Final :</strong> Email avec votre site en ligne !</p>
              </div>
            </div>

            <button 
              onClick={onClose}
              className="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600 font-medium"
            >
              🏠 Retour à l'accueil
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ConciergeModal;