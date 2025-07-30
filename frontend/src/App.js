import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AdminDashboard from "./AdminDashboard";
import History from "./History";
import WebsiteEditor from "./WebsiteEditor";
import ConciergeModal from "./ConciergeModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function WebsiteGenerator() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    description: "",
    site_type: "vitrine",
    business_name: "",
    primary_color: "#3B82F6"
  });
  const [generatedWebsite, setGeneratedWebsite] = useState(null);
  const [loading, setLoading] = useState(false);
  const [referralCode, setReferralCode] = useState("");
  const [paymentUrl, setPaymentUrl] = useState(null);
  const [paymentId, setPaymentId] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewHtml, setPreviewHtml] = useState("");
  const [showConciergeModal, setShowConciergeModal] = useState(false);

  // Check for referral code in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const ref = urlParams.get('ref');
    if (ref) {
      setReferralCode(ref);
    }
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const generateWebsite = async () => {
    if (!formData.description || !formData.business_name) {
      alert("Veuillez remplir tous les champs obligatoires");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/generate-website`, {
        ...formData,
        referral_code: referralCode
      });

      setGeneratedWebsite(response.data);
      setStep(2);
    } catch (error) {
      console.error("Erreur lors de la génération:", error);
      alert("Erreur lors de la génération du site web");
    } finally {
      setLoading(false);
    }
  };

  const showWebsitePreview = async () => {
    if (!generatedWebsite) return;

    try {
      const response = await axios.get(`${API}/preview/${generatedWebsite.id}`);
      setPreviewHtml(response.data.html);
      setShowPreview(true);
    } catch (error) {
      console.error("Erreur lors du chargement de la prévisualisation:", error);
      alert("Erreur lors du chargement de la prévisualisation");
    }
  };

  const createPaymentUrl = async () => {
    if (!generatedWebsite) return;

    try {
      const response = await axios.post(`${API}/paypal/create-payment-url`, {
        website_id: generatedWebsite.id,
        referral_code: referralCode
      });

      setPaymentUrl(response.data.payment_url);
      setPaymentId(generatedWebsite.id); // Using website_id as payment reference
      setStep(3);
    } catch (error) {
      console.error("Erreur lors de la création du paiement:", error);
      alert("Erreur lors de la création du paiement");
    }
  };

  const confirmPayment = async () => {
    if (!paymentId) return;

    try {
      await axios.post(`${API}/confirm-payment/${paymentId}`);
      setStep(4);
      alert("Paiement confirmé avec succès ! 🎉");
    } catch (error) {
      console.error("Erreur lors de la confirmation du paiement:", error);
      alert("Erreur lors de la confirmation du paiement");
    }
  };

  const createReferralLink = async () => {
    try {
      const response = await axios.post(`${API}/create-referral`, {});
      const referralLink = response.data.referral_link;
      
      // Always show the link first
      const message = `🎉 Votre lien de parrainage a été créé !\n\n📋 ${referralLink}\n\n💡 Partagez ce lien pour faire économiser 5€ à vos amis !`;
      
      // Try to copy to clipboard (but don't fail if it doesn't work)
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(referralLink);
          alert(message + "\n\n✅ Le lien a été copié dans votre presse-papier !");
        } else {
          // Fallback method
          const textArea = document.createElement("textarea");
          textArea.value = referralLink;
          textArea.style.position = 'fixed';
          textArea.style.left = '-999999px';
          textArea.style.top = '-999999px';
          document.body.appendChild(textArea);
          textArea.focus();
          textArea.select();
          
          try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (successful) {
              alert(message + "\n\n✅ Le lien a été copié dans votre presse-papier !");
            } else {
              alert(message + "\n\n📝 Copiez ce lien manuellement pour le partager !");
            }
          } catch (err) {
            document.body.removeChild(textArea);
            alert(message + "\n\n📝 Copiez ce lien manuellement pour le partager !");
          }
        }
      } catch (clipboardError) {
        // Even if clipboard fails, still show the link
        console.log("Clipboard failed, but that's OK:", clipboardError);
        alert(message + "\n\n📝 Copiez ce lien manuellement pour le partager !");
      }
      
    } catch (error) {
      console.error("Erreur lors de la création du lien de parrainage:", error);
      
      if (error.response?.status === 500) {
        alert("❌ Erreur du serveur. Veuillez réessayer dans quelques instants.");
      } else if (error.request) {
        alert("❌ Impossible de contacter le serveur. Vérifiez votre connexion internet.");
      } else {
        alert("❌ Une erreur inattendue s'est produite lors de la création du lien. Veuillez réessayer.");
      }
    }
  };

  const downloadWebsite = async () => {
    if (!generatedWebsite) return;

    try {
      const response = await axios.get(`${API}/download/${generatedWebsite.id}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${formData.business_name}_website.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error("Erreur lors du téléchargement:", error);
      alert("Erreur lors du téléchargement");
    }
  };

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="bg-gray-900 shadow-sm border-b border-green-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="text-2xl font-bold text-green-400">🤖 AI WebGen</div>
              <div className="ml-4 text-sm text-gray-300">
                <div className="font-medium">Créateur de sites web par Intelligence Artificielle</div>
                <div className="text-xs text-green-400 italic mt-1">
                  ✨ NOUVEAU : Éditeur intégré après achat - Modifiez votre site librement !
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {referralCode && (
                <div className="bg-green-900 text-green-300 px-3 py-1 rounded-full text-sm border border-green-500">
                  🎉 Réduction de 5€ appliquée !
                </div>
              )}
              <button
                onClick={createReferralLink}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                📤 Partager pour économiser
              </button>
              <a
                href="/history"
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                📜 Historique
              </a>
              <div className="text-xs text-orange-400 bg-orange-900 px-2 py-1 rounded animate-pulse">
                🔥 Service concierge : 78% de nos clients
              </div>
              <a
                href="/admin"
                className="bg-gray-800 text-green-400 px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors text-sm border border-green-500"
              >
                👑 Admin
              </a>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center">
            {[1, 2, 3, 4].map((stepNumber) => (
              <div key={stepNumber} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  step >= stepNumber ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-400'
                }`}>
                  {stepNumber}
                </div>
                {stepNumber < 4 && (
                  <div className={`w-12 h-0.5 ${
                    step > stepNumber ? 'bg-green-600' : 'bg-gray-700'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-center mt-2 text-sm text-gray-400">
            <div className="text-center">
              Création • Prévisualisation • Paiement • Téléchargement
            </div>
          </div>
        </div>

        {/* Step 1: Website Creation */}
        {step === 1 && (
          <div className="bg-gray-900 border border-green-500 rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-white mb-2">
              Créez votre site web parfait
            </h2>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <div className="flex items-center">
                  <div className="text-yellow-600 mr-3">💡</div>
                  <div>
                    <p className="text-yellow-800 text-sm">
                      <strong>Astuce :</strong> Vous pourrez éditer votre site après achat, mais 
                      <span className="text-yellow-700"> pensez-vous à l'hébergement ?</span> 
                      <span className="text-xs text-yellow-600"> (Nous avons une solution simple...)</span>
                    </p>
                  </div>
                </div>
              </div>

              <p className="text-gray-300 mb-8">
                Décrivez votre projet et notre IA créera un site web professionnel pour vous
              </p>

            {/* NEW - Editing Info Banner on Homepage */}
            <div className="bg-gradient-to-r from-green-900 to-blue-900 border border-green-400 rounded-lg p-6 mb-8">
              <div className="flex items-center justify-center space-x-3 mb-4">
                <span className="text-3xl">🎨</span>
                <h3 className="text-xl font-bold text-green-200">
                  ✨ NOUVEAU : Éditeur Intégré Après Achat !
                </h3>
                <span className="text-3xl">✨</span>
              </div>
              <div className="text-center mb-4">
                <p className="text-green-100 text-lg mb-3">
                  Une fois votre site acheté, <strong className="text-green-200">modifiez-le librement</strong> avec notre éditeur intégré !
                </p>
                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div className="bg-green-800 bg-opacity-50 p-3 rounded-lg">
                    <div className="text-2xl mb-2">🎨</div>
                    <div className="font-semibold text-green-200">Couleurs & Design</div>
                    <div className="text-green-100">Changez couleurs, polices, mise en page</div>
                  </div>
                  <div className="bg-blue-800 bg-opacity-50 p-3 rounded-lg">
                    <div className="text-2xl mb-2">📝</div>
                    <div className="font-semibold text-blue-200">Contenu & Textes</div>
                    <div className="text-blue-100">Modifiez textes, ajoutez sections</div>
                  </div>
                  <div className="bg-purple-800 bg-opacity-50 p-3 rounded-lg">
                    <div className="text-2xl mb-2">📞</div>
                    <div className="font-semibold text-purple-200">Contact & Galerie</div>
                    <div className="text-purple-100">Ajoutez contact, témoignages, photos</div>
                  </div>
                </div>
              </div>
              <div className="flex justify-center">
                <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-2 rounded-full font-medium">
                  🚀 Personnalisez votre site autant que vous voulez !
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nom de votre entreprise *
                </label>
                <input
                  type="text"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleInputChange}
                  placeholder="Ex: Ma Super Entreprise"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type de site web
                </label>
                <select
                  name="site_type"
                  value={formData.site_type}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value="vitrine">🏪 Site vitrine d'entreprise</option>
                  <option value="ecommerce">🛒 E-commerce simple</option>
                  <option value="blog">📝 Blog</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Couleur principale
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    type="color"
                    name="primary_color"
                    value={formData.primary_color}
                    onChange={handleInputChange}
                    className="w-16 h-12 border border-gray-300 rounded-lg cursor-pointer"
                  />
                  <input
                    type="text"
                    name="primary_color"
                    value={formData.primary_color}
                    onChange={handleInputChange}
                    placeholder="#3B82F6"
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description détaillée de votre site *
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows={4}
                  placeholder="Décrivez votre entreprise, vos services, votre style souhaité, vos couleurs préférées, etc."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="text-blue-600 mr-3">💡</div>
                  <div>
                    <p className="font-medium text-blue-900">Prix transparent</p>
                    <p className="text-blue-700 text-sm">
                      {referralCode ? (
                        <span className="text-green-600 font-medium">
                          10€ au lieu de 15€ grâce au code de parrainage ! 🎉
                        </span>
                      ) : (
                        "15€ pour un site web complet et professionnel"
                      )}
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={generateWebsite}
                disabled={loading}
                className={`w-full py-4 px-6 rounded-lg font-medium text-white transition-colors ${
                  loading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {loading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Génération en cours...
                  </div>
                ) : (
                  "🚀 Générer mon site web"
                )}
              </button>
              
              <div className="text-center mt-3">
                <p className="text-xs text-gray-500">
                  💡 Génération en moins de 30 secondes • Sans engagement
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Preview */}
        {step === 2 && generatedWebsite && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Votre site web est prêt !
            </h2>
            <p className="text-gray-600 mb-8">
              Découvrez la prévisualisation de votre site web généré par IA
            </p>

            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Détails du site</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-600">Nom de l'entreprise:</span>
                    <p className="font-medium">{formData.business_name}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Type de site:</span>
                    <p className="font-medium">
                      {formData.site_type === 'vitrine' && '🏪 Site vitrine'}
                      {formData.site_type === 'ecommerce' && '🛒 E-commerce'}
                      {formData.site_type === 'blog' && '📝 Blog'}
                    </p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Prix:</span>
                    <p className="font-medium text-indigo-600">{generatedWebsite.price}€</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Couleur principale:</span>
                    <div className="flex items-center">
                      <div 
                        className="w-4 h-4 rounded mr-2 border" 
                        style={{ backgroundColor: formData.primary_color }}
                      ></div>
                      <p className="font-medium">{formData.primary_color}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={showWebsitePreview}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  👁️ Voir la prévisualisation
                </button>
                <button
                  onClick={createPaymentUrl}
                  className="flex-1 bg-indigo-600 text-white py-3 px-6 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  💳 Procéder au paiement
                </button>
              </div>

              {showPreview && (
                <div className="mt-6">
                  <h3 className="font-semibold text-gray-900 mb-4">Prévisualisation</h3>
                  <div className="border rounded-lg overflow-hidden">
                    <div className="bg-gray-100 px-4 py-2 text-sm text-gray-600">
                      Aperçu de votre site web
                    </div>
                    <iframe
                      srcDoc={previewHtml}
                      className="w-full h-96"
                      title="Prévisualisation du site web"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === 3 && generatedWebsite && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Finaliser votre achat
            </h2>
            <p className="text-gray-600 mb-8">
              Procédez au paiement sécurisé avec PayPal
            </p>

            <div className="space-y-6">
              {/* NEW - Editing Feature Info */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="text-3xl">🎨</div>
                  <h3 className="font-semibold text-blue-900">
                    ✨ Édition Illimitée Incluse Après Achat !
                  </h3>
                </div>
                <p className="text-blue-800 mb-3">
                  Une fois votre site acheté, vous pourrez le <strong>modifier librement</strong> grâce à notre éditeur intégré :
                </p>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm">Changer les couleurs et le nom</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm">Ajouter sections et témoignages</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm">Éditer le contenu facilement</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm">Ajouter galerie et contact</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm">Prévisualisation temps réel</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm">Guide d'aide intégré</span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 flex justify-center">
                  <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium">
                    🎯 Personnalisez votre site autant que vous voulez !
                  </span>
                </div>
              </div>

              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-6">
                <h3 className="font-semibold text-indigo-900 mb-4">Récapitulatif</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Site web pour {formData.business_name}</span>
                    <span className="font-medium">{generatedWebsite.price}€</span>
                  </div>
                  {referralCode && (
                    <div className="flex justify-between text-green-600">
                      <span>Réduction parrainage</span>
                      <span className="font-medium">-5€</span>
                    </div>
                  )}
                  <div className="border-t pt-2 flex justify-between text-lg font-bold">
                    <span>Total</span>
                    <span className="text-indigo-600">{generatedWebsite.price}€</span>
                  </div>
                </div>
              </div>

              <div className="text-center space-y-4">
                <p className="text-gray-600">
                  Cliquez sur le bouton ci-dessous pour payer avec PayPal
                </p>
                
                {paymentUrl && (
                  <a
                    href={paymentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block bg-yellow-400 text-black py-3 px-8 rounded-lg font-medium hover:bg-yellow-500 transition-colors text-lg"
                  >
                    💳 Payer {generatedWebsite.price}€ avec PayPal
                  </a>
                )}

                <div className="bg-gray-50 rounded-lg p-4 mt-6">
                  <p className="text-sm text-gray-600 mb-3">
                    Après avoir effectué le paiement PayPal, cliquez sur le bouton ci-dessous pour confirmer :
                  </p>
                  <button
                    onClick={confirmPayment}
                    className="w-full bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    ✅ J'ai payé - Confirmer le paiement
                  </button>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="text-blue-600 mr-3">🔒</div>
                  <div>
                    <p className="font-medium text-blue-900">Paiement 100% sécurisé</p>
                    <p className="text-blue-700 text-sm">
                      Via PayPal - Vos informations bancaires sont protégées
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Download */}
        {step === 4 && (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="text-green-600 text-2xl">✅</div>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Félicitations !
              </h2>
              <p className="text-gray-600">
                Votre paiement a été confirmé et votre site web est prêt à être téléchargé
              </p>
              
              {/* Subtle concern creation */}
              <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mt-4">
                <p className="text-blue-700 text-sm">
                  🤔 <strong>Et maintenant ?</strong> La plupart de nos clients se demandent comment mettre leur site en ligne... 
                  <span className="text-blue-600 text-xs">(On a pensé à ça aussi !)</span>
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <button
                onClick={downloadWebsite}
                className="w-full bg-indigo-600 text-white py-4 px-6 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                📥 Télécharger mon site web (ZIP)
              </button>

              {/* NEW - Edit Button */}
              <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-center space-x-2 mb-3">
                  <span className="text-2xl">🎨</span>
                  <h3 className="font-semibold text-green-800">Personnalisez maintenant votre site !</h3>
                </div>
                <p className="text-green-700 text-sm mb-3">
                  Utilisez notre éditeur intégré pour modifier : couleurs, textes, sections, contact, galerie...
                </p>
                <button
                  onClick={() => window.location.href = `/edit/${generatedWebsite.id}`}
                  className="w-full bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  ✏️ Éditer mon site maintenant
                </button>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-900 font-medium mb-2">Que contient votre téléchargement ?</p>
                <ul className="text-blue-700 text-sm space-y-1">
                  <li>• index.html - Page principale de votre site</li>
                  <li>• styles.css - Toutes les styles CSS</li>
                  <li>• script.js - Fonctionnalités JavaScript</li>
                  <li>• README.md - Instructions d'utilisation</li>
                </ul>
              </div>

              {/* NEW - Hosting & Domain Options */}
              <div className="bg-gradient-to-r from-gray-50 to-blue-50 border border-gray-200 rounded-lg p-6">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    🎯 Une dernière étape... Comment rendre votre site accessible ?
                  </h3>
                  <p className="text-gray-600 text-sm">
                    Vous avez maintenant un site professionnel. Nos clients choisissent généralement l'une de ces options :
                  </p>
                </div>
                
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="bg-white p-4 rounded-lg border border-orange-200 relative">
                    <div className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs px-2 py-1 rounded-full">
                      78% choisissent
                    </div>
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="text-2xl">🤝</span>
                      <h4 className="font-bold text-gray-800">Nous faisons tout</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">
                      Comme la plupart, <strong>laissez-nous vous éviter le stress</strong>. 
                      Domaine + hébergement + site en ligne.
                    </p>
                    <div className="text-xs text-gray-500 mb-3">
                      Fini les complications techniques.<br/>
                      Votre site sera en ligne demain.
                    </div>
                    <div className="text-center">
                      <div className="text-gray-800 font-bold mb-1">49€ <span className="text-sm text-gray-500">tout compris</span></div>
                      <div className="text-xs text-green-600 mb-2">💡 Support inclus 3 mois</div>
                      <button 
                        onClick={() => setShowConciergeModal(true)}
                        className="w-full bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 text-sm font-medium"
                      >
                        🚀 Oui, faites-le pour moi
                      </button>
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border border-blue-200">
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="text-2xl">📚</span>
                      <h4 className="font-bold text-gray-800">Je me débrouille</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">
                      Vous êtes technique ? Voici notre guide pas-à-pas avec 6 solutions d'hébergement.
                    </p>
                    <div className="text-xs text-gray-500 mb-3">
                      Netlify, GitHub, Hostinger, OVH...<br/>
                      Instructions détaillées incluses.
                    </div>
                    <div className="text-center">
                      <div className="text-gray-800 font-bold mb-2">Gratuit</div>
                      <button 
                        onClick={() => window.open(`${API}/download-hosting-guide`, '_blank')}
                        className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 text-sm"
                      >
                        📚 Télécharger le guide
                      </button>
                    </div>
                  </div>
                  
                  <div className="bg-white p-4 rounded-lg border border-gray-200 opacity-75">
                    <div className="flex items-center space-x-2 mb-3">
                      <span className="text-2xl">⚡</span>
                      <h4 className="font-bold text-gray-800">Solution automatique</h4>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">
                      Un clic et c'est en ligne ! Notre solution automatique arrive bientôt.
                    </p>
                    <div className="text-xs text-gray-500 mb-3">
                      Interface simple, déploiement instant.<br/>
                      <strong>50 premiers clients : -50%</strong>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-600 mb-2">~8€/mois</div>
                      <button disabled className="w-full bg-gray-300 text-gray-500 py-2 px-4 rounded-lg text-sm cursor-not-allowed">
                        🔜 Bientôt (inscrivez-vous)
                      </button>  
                    </div>
                  </div>
                </div>
                
                <div className="text-center mt-4">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
                    <p className="text-sm text-green-800">
                      💬 <em>"J'ai pris le service concierge et 24h après mon site était en ligne. 
                      Zéro stress, je recommande !"</em> - <strong>Marie L.</strong>, coiffeuse
                    </p>
                  </div>
                  <p className="text-xs text-gray-500">
                    💡 <strong>Conseil :</strong> La majorité de nos clients prennent le service complet pour éviter les complications.
                    <br/>Vous pouvez toujours éditer votre site après la mise en ligne !
                  </p>
                </div>
              </div>

              <button
                onClick={createReferralLink}
                className="w-full bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 transition-colors"
              >
                📤 Partager pour économiser sur le prochain achat
              </button>

              <button
                onClick={() => {
                  setStep(1);
                  setFormData({
                    description: "",
                    site_type: "vitrine",
                    business_name: "",
                    primary_color: "#3B82F6"
                  });
                  setGeneratedWebsite(null);
                  setPaymentUrl(null);
                  setPaymentId(null);
                  setShowPreview(false);
                }}
                className="w-full bg-gray-200 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-300 transition-colors"
              >
                🔄 Créer un nouveau site
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Concierge Modal */}
      <ConciergeModal 
        isOpen={showConciergeModal}
        onClose={() => setShowConciergeModal(false)}
        websiteId={generatedWebsite?.id}
        websiteName={generatedWebsite?.business_name || formData.business_name}
      />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WebsiteGenerator />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/history" element={<History />} />
        <Route path="/edit/:websiteId" element={<WebsiteEditor />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;