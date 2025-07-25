import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function History() {
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [selectedFilter, setSelectedFilter] = useState("all");

  const ITEMS_PER_PAGE = 20;

  useEffect(() => {
    loadHistoryData();
    loadHistoryStats();
  }, [currentPage, selectedFilter]);

  const loadHistoryData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/history`, {
        params: {
          limit: ITEMS_PER_PAGE,
          skip: currentPage * ITEMS_PER_PAGE
        }
      });
      
      let filteredHistory = response.data.history;
      
      // Apply filter
      if (selectedFilter !== "all") {
        filteredHistory = response.data.history.filter(
          entry => entry.action_type === selectedFilter
        );
      }
      
      setHistory(filteredHistory);
      setTotalPages(Math.ceil(response.data.total / ITEMS_PER_PAGE));
    } catch (error) {
      console.error("Error loading history:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoryStats = async () => {
    try {
      const response = await axios.get(`${API}/history-stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error loading history stats:", error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  };

  const getActionIcon = (actionType) => {
    const icons = {
      website_generated: "🌐",
      ai_generation: "🤖",
      template_used: "📋",
      website_previewed: "👁️",
      payment_created: "💳",
      payment_confirmed: "✅",
      website_downloaded: "📥",
      referral_created: "🎁"
    };
    return icons[actionType] || "📝";
  };

  const getActionText = (actionType) => {
    const texts = {
      website_generated: "Site web généré",
      ai_generation: "Génération IA",
      template_used: "Template utilisé",
      website_previewed: "Site prévisualisé",
      payment_created: "Paiement créé",
      payment_confirmed: "Paiement confirmé",
      website_downloaded: "Site téléchargé",
      referral_created: "Code de parrainage créé"
    };
    return texts[actionType] || actionType;
  };

  const cleanupOldHistory = async () => {
    try {
      const response = await axios.delete(`${API}/history/cleanup?days_old=30`);
      alert(`${response.data.deleted_count} entrées d'historique supprimées`);
      loadHistoryData();
      loadHistoryStats();
    } catch (error) {
      console.error("Error cleaning up history:", error);
      alert("Erreur lors du nettoyage de l'historique");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mr-3"></div>
          <span className="text-white">Chargement de l'historique...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="bg-gray-900 shadow-sm border-b border-green-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">📜 Historique des Actions</h1>
              <p className="text-gray-400">Suivi complet de toutes les activités AI WebGen</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={cleanupOldHistory}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                🗑️ Nettoyer (30j+)
              </button>
              <button
                onClick={() => window.location.href = "/admin"}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => window.location.href = "/"}
                className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
              >
                🏠 Accueil
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-900 border border-green-500 rounded-lg p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">📊</div>
                <div>
                  <p className="text-sm text-gray-400">Total Activités</p>
                  <p className="text-2xl font-bold text-white">{stats.total_activities}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">📈</div>
                <div>
                  <p className="text-sm text-gray-400">Aujourd'hui</p>
                  <p className="text-2xl font-bold text-green-400">{stats.today_activities}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">🤖</div>
                <div>
                  <p className="text-sm text-gray-400">Générations IA</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {stats.action_counts.ai_generation || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">💳</div>
                <div>
                  <p className="text-sm text-gray-400">Paiements</p>
                  <p className="text-2xl font-bold text-yellow-400">
                    {(stats.action_counts.payment_created || 0) + (stats.action_counts.payment_confirmed || 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-gray-900 border border-green-500 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-green-400 mb-4">🔍 Filtres</h3>
          <div className="flex flex-wrap gap-2">
            {["all", "ai_generation", "template_used", "website_previewed", "payment_created", "payment_confirmed", "website_downloaded", "referral_created"].map((filter) => (
              <button
                key={filter}
                onClick={() => {
                  setSelectedFilter(filter);
                  setCurrentPage(0);
                }}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  selectedFilter === filter
                    ? "bg-green-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                {getActionIcon(filter)} {filter === "all" ? "Tout" : getActionText(filter)}
              </button>
            ))}
          </div>
        </div>

        {/* History Timeline */}
        <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg">
          <div className="px-6 py-4 border-b border-green-500">
            <h3 className="text-lg font-semibold text-green-400">📜 Timeline des Actions</h3>
          </div>
          
          <div className="p-6">
            {history.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📭</div>
                <p className="text-gray-400 text-lg">Aucune activité trouvée</p>
              </div>
            ) : (
              <div className="space-y-4">
                {history.map((entry) => (
                  <div key={entry.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-green-500 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="text-2xl">{getActionIcon(entry.action_type)}</div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h4 className="text-white font-medium">{getActionText(entry.action_type)}</h4>
                            {entry.business_name && (
                              <span className="text-green-400 text-sm">• {entry.business_name}</span>
                            )}
                          </div>
                          <p className="text-gray-400 text-sm mb-2">
                            {formatDate(entry.timestamp)}
                            {entry.website_id && (
                              <span className="ml-2 text-blue-400">
                                ID: {entry.website_id.slice(0, 8)}...
                              </span>
                            )}
                          </p>
                          
                          {/* Details */}
                          {entry.details && Object.keys(entry.details).length > 0 && (
                            <div className="bg-gray-900 rounded p-3 mt-2">
                              <p className="text-xs text-gray-500 mb-2">Détails:</p>
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {Object.entries(entry.details).map(([key, value]) => (
                                  <div key={key} className="text-sm">
                                    <span className="text-gray-400">{key}:</span>
                                    <span className="text-white ml-1">
                                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center mt-8">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                    disabled={currentPage === 0}
                    className="px-4 py-2 bg-gray-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
                  >
                    ← Précédent
                  </button>
                  
                  <span className="text-white px-4">
                    Page {currentPage + 1} sur {totalPages}
                  </span>
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                    disabled={currentPage === totalPages - 1}
                    className="px-4 py-2 bg-gray-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
                  >
                    Suivant →
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default History;