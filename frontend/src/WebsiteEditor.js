import React, { useState, useEffect } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function WebsiteEditor() {
  const { websiteId } = useParams();
  const navigate = useNavigate();
  
  const [website, setWebsite] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("visual");
  const [previewMode, setPreviewMode] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  useEffect(() => {
    loadWebsite();
  }, [websiteId]);

  const loadWebsite = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/edit/${websiteId}`);
      setWebsite(response.data);
    } catch (error) {
      console.error("Error loading website:", error);
      if (error.response?.status === 403) {
        alert("❌ Ce site n'est pas payé. L'édition n'est pas autorisée.");
        navigate("/");
      } else if (error.response?.status === 404) {
        alert("❌ Site web non trouvé.");
        navigate("/");
      }
    } finally {
      setLoading(false);
    }
  };

  const saveChanges = async () => {
    if (!website || !unsavedChanges) return;
    
    try {
      setSaving(true);
      const changes = {
        business_name: website.business_name,
        html_content: website.html_content,
        css_content: website.css_content,
        js_content: website.js_content,
        primary_color: website.primary_color
      };
      
      await axios.put(`${API}/edit/${websiteId}`, changes);
      setUnsavedChanges(false);
      alert("✅ Site web sauvegardé avec succès !");
    } catch (error) {
      console.error("Error saving changes:", error);
      alert("❌ Erreur lors de la sauvegarde.");
    } finally {
      setSaving(false);
    }
  };

  const updateWebsite = (field, value) => {
    setWebsite(prev => ({
      ...prev,
      [field]: value
    }));
    setUnsavedChanges(true);
  };

  const insertHtmlElement = (element) => {
    const newHtml = website.html_content + element;
    updateWebsite("html_content", newHtml);
  };

  const changeColor = (newColor) => {
    const newCss = website.css_content.replace(
      /color:\s*#[0-9a-fA-F]{6}/g,
      `color: ${newColor}`
    );
    updateWebsite("css_content", newCss);
    updateWebsite("primary_color", newColor);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-white">Chargement de l'éditeur...</p>
        </div>
      </div>
    );
  }

  if (!website) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <p className="text-white text-xl">Site web non trouvé</p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="bg-gray-900 border-b border-green-500 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-green-400">🎨 Éditeur de Site</h1>
            <span className="text-gray-400">•</span>
            <span className="text-white">{website.business_name}</span>
            {unsavedChanges && (
              <span className="bg-yellow-900 text-yellow-300 px-2 py-1 rounded text-sm">
                Non sauvegardé
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              {showHelp ? "❌ Fermer aide" : "❓ Aide"}
            </button>
            <button
              onClick={() => setPreviewMode(!previewMode)}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
            >
              {previewMode ? "✏️ Éditer" : "👁️ Prévisualiser"}
            </button>
            <button
              onClick={saveChanges}
              disabled={saving || !unsavedChanges}
              className={`px-6 py-2 rounded-lg font-semibold ${
                saving || !unsavedChanges
                  ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                  : "bg-green-600 text-white hover:bg-green-700"
              }`}
            >
              {saving ? "💾 Sauvegarde..." : "💾 Sauvegarder"}
            </button>
            <button
              onClick={() => navigate("/")}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
            >
              🏠 Accueil
            </button>
          </div>
        </div>
      </div>

      {/* Help Panel */}
      {showHelp && (
        <div className="bg-blue-900 border-b border-blue-500 p-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="bg-blue-800 p-4 rounded-lg">
              <h3 className="font-bold text-blue-200 mb-2">🎨 Modification Visuelle</h3>
              <p className="text-blue-100 text-sm">
                • Changez les couleurs avec le sélecteur<br/>
                • Ajoutez des éléments avec les boutons<br/>
                • Modifiez le nom de votre entreprise
              </p>
            </div>
            <div className="bg-blue-800 p-4 rounded-lg">
              <h3 className="font-bold text-blue-200 mb-2">⚡ Édition Rapide</h3>
              <p className="text-blue-100 text-sm">
                • Cliquez sur "Ajouter Section" pour plus de contenu<br/>
                • Utilisez les couleurs prédéfinies<br/>
                • Prévisualisez avant de sauvegarder
              </p>
            </div>
            <div className="bg-blue-800 p-4 rounded-lg">
              <h3 className="font-bold text-blue-200 mb-2">💡 Conseils</h3>
              <p className="text-blue-100 text-sm">
                • Sauvegardez régulièrement vos modifications<br/>
                • Testez sur mobile avec la prévisualisation<br/>
                • Gardez un design cohérent
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex h-screen">
        {/* Left Panel - Tools */}
        {!previewMode && (
          <div className="w-80 bg-gray-900 border-r border-green-500 p-4 overflow-y-auto">
            <div className="space-y-6">
              {/* Basic Settings */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-green-400 font-bold mb-4">⚙️ Paramètres de Base</h3>
                
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Nom de l'entreprise</label>
                  <input
                    type="text"
                    value={website.business_name}
                    onChange={(e) => updateWebsite("business_name", e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white"
                  />
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Couleur principale</label>
                  <div className="flex items-center space-x-2">
                    <input
                      type="color"
                      value={website.primary_color}
                      onChange={(e) => changeColor(e.target.value)}
                      className="w-12 h-8 rounded border border-gray-600"
                    />
                    <input
                      type="text"
                      value={website.primary_color}
                      onChange={(e) => changeColor(e.target.value)}
                      className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-2">
                  {["#4A90E2", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6", "#1ABC9C"].map(color => (
                    <button
                      key={color}
                      onClick={() => changeColor(color)}
                      className="w-8 h-8 rounded border-2 border-gray-600 hover:border-white"
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              </div>

              {/* Quick Elements */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-green-400 font-bold mb-4">➕ Ajouter des Éléments</h3>
                
                <div className="space-y-2">
                  <button
                    onClick={() => insertHtmlElement(`<div class="section"><h2>Nouvelle Section</h2><p>Votre contenu ici...</p></div>`)}
                    className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
                  >
                    📄 Ajouter Section
                  </button>
                  
                  <button
                    onClick={() => insertHtmlElement(`<div class="contact"><h3>Contactez-nous</h3><p>Email: contact@${website.business_name.toLowerCase().replace(/\s+/g, '')}.com</p><p>Téléphone: 01 23 45 67 89</p></div>`)}
                    className="w-full bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
                  >
                    📞 Ajouter Contact
                  </button>
                  
                  <button
                    onClick={() => insertHtmlElement(`<div class="testimonial"><h3>Témoignages</h3><blockquote>"Excellent service, je recommande vivement !" - Client satisfait</blockquote></div>`)}
                    className="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm"
                  >
                    💬 Ajouter Témoignage
                  </button>
                  
                  <button
                    onClick={() => insertHtmlElement(`<div class="gallery"><h3>Galerie</h3><div class="images-placeholder"><p>📸 Ajoutez vos images ici</p></div></div>`)}
                    className="w-full bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 text-sm"
                  >
                    🖼️ Ajouter Galerie
                  </button>
                </div>
              </div>

              {/* Advanced Tabs */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-green-400 font-bold mb-4">🔧 Édition Avancée</h3>
                
                <div className="flex space-x-1 mb-4">
                  <button
                    onClick={() => setActiveTab("html")}
                    className={`px-3 py-1 rounded text-sm ${
                      activeTab === "html" ? "bg-green-600 text-white" : "bg-gray-700 text-gray-300"
                    }`}
                  >
                    HTML
                  </button>
                  <button
                    onClick={() => setActiveTab("css")}
                    className={`px-3 py-1 rounded text-sm ${
                      activeTab === "css" ? "bg-green-600 text-white" : "bg-gray-700 text-gray-300"
                    }`}
                  >
                    CSS
                  </button>
                </div>

                {activeTab === "html" && (
                  <textarea
                    value={website.html_content}
                    onChange={(e) => updateWebsite("html_content", e.target.value)}
                    className="w-full h-32 bg-gray-700 border border-gray-600 rounded-lg p-2 text-white text-xs font-mono"
                    placeholder="Code HTML..."
                  />
                )}

                {activeTab === "css" && (
                  <textarea
                    value={website.css_content}
                    onChange={(e) => updateWebsite("css_content", e.target.value)}
                    className="w-full h-32 bg-gray-700 border border-gray-600 rounded-lg p-2 text-white text-xs font-mono"
                    placeholder="Code CSS..."
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {/* Right Panel - Preview */}
        <div className="flex-1 bg-white">
          <iframe
            srcDoc={`
              <!DOCTYPE html>
              <html lang="fr">
              <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${website.business_name}</title>
                <style>
                  ${website.css_content}
                  .section { margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }
                  .contact { background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0; }
                  .testimonial { background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0; font-style: italic; }
                  .gallery { margin: 20px 0; }
                  .images-placeholder { background: #e0e0e0; padding: 40px; text-align: center; border-radius: 8px; }
                  blockquote { border-left: 4px solid ${website.primary_color}; padding-left: 16px; margin: 10px 0; }
                </style>
              </head>
              <body>
                ${website.html_content}
              </body>
              </html>
            `}
            className="w-full h-full border-none"
            title="Prévisualisation"
          />
        </div>
      </div>
    </div>
  );
}

export default WebsiteEditor;