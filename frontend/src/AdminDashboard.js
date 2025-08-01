import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [websites, setWebsites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load stats
      const statsResponse = await axios.get(`${API}/admin/stats`);
      setStats(statsResponse.data);
      
      // Load websites
      const websitesResponse = await axios.get(`${API}/admin/websites`);
      setWebsites(websitesResponse.data.websites);
      
    } catch (error) {
      console.error("Error loading dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mr-3"></div>
          <span className="text-white">Chargement du tableau de bord...</span>
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
              <h1 className="text-2xl font-bold text-white">📊 Dashboard Admin</h1>
              <p className="text-gray-400">AI WebGen - Tableau de bord administrateur</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.location.href = "/history"}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
              >
                📜 Historique
              </button>
              <button
                onClick={() => window.location.href = "/"}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors shadow-lg"
              >
                🏠 Retour à l'app
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center">
                <div className="text-3xl mr-4">🌐</div>
                <div>
                  <p className="text-sm text-gray-400">Sites Créés</p>
                  <p className="text-2xl font-bold text-white">{stats.total_websites}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center">
                <div className="text-3xl mr-4">💰</div>
                <div>
                  <p className="text-sm text-gray-400">Revenus</p>
                  <p className="text-2xl font-bold text-green-500">{stats.total_revenue}€</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center">
                <div className="text-3xl mr-4">✅</div>
                <div>
                  <p className="text-sm text-gray-400">Taux de Conversion</p>
                  <p className="text-2xl font-bold text-green-400">{stats.conversion_rate}%</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <div className="flex items-center">
                <div className="text-3xl mr-4">📈</div>
                <div>
                  <p className="text-sm text-gray-400">Aujourd'hui</p>
                  <p className="text-2xl font-bold text-green-300">{stats.today_websites}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Additional Stats */}
        {stats && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-green-400 mb-4">📊 Statistiques Détaillées</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Sites payés:</span>
                  <span className="font-medium text-white">{stats.paid_websites} / {stats.total_websites}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Codes de parrainage créés:</span>
                  <span className="font-medium text-white">{stats.total_referrals}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Parrainages utilisés:</span>
                  <span className="font-medium text-white">{stats.used_referrals}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Revenus moyens par site:</span>
                  <span className="font-medium text-green-400">
                    {stats.paid_websites > 0 ? (stats.total_revenue / stats.paid_websites).toFixed(2) : 0}€
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-semibold text-green-400 mb-4">🎯 Sites Récents</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {stats.recent_websites.map((website) => (
                  <div key={website.id} className="flex items-center justify-between p-3 bg-gray-800 rounded border border-green-900">
                    <div>
                      <p className="font-medium text-sm text-white">{website.business_name}</p>
                      <p className="text-xs text-gray-400">
                        {website.site_type} • {formatDate(website.created_at)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-green-400">{website.price}€</p>
                      <div className="flex items-center space-x-1">
                        {website.paid ? (
                          <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded border border-green-700">Payé</span>
                        ) : (
                          <span className="text-xs bg-yellow-900 text-yellow-300 px-2 py-1 rounded border border-yellow-700">En attente</span>
                        )}
                        {website.referral_used && (
                          <span className="text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded border border-blue-700">Parrainage</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* All Websites Table */}
        <div className="bg-gray-900 border border-green-500 rounded-lg shadow-lg">
          <div className="px-6 py-4 border-b border-green-500">
            <h3 className="text-lg font-semibold text-green-400">🌐 Tous les Sites Web</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-green-900">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-green-400 uppercase tracking-wider">
                    Entreprise
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-green-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-green-400 uppercase tracking-wider">
                    Prix
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-green-400 uppercase tracking-wider">
                    État
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-green-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-green-400 uppercase tracking-wider">
                    Couleur
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-900 divide-y divide-green-900">
                {websites.map((website) => (
                  <tr key={website.id} className="hover:bg-gray-800 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">
                          {website.business_name}
                        </div>
                        <div className="text-sm text-gray-400 truncate max-w-xs">
                          {website.description}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-green-300">
                        {website.site_type === 'vitrine' && '🏪 Vitrine'}
                        {website.site_type === 'ecommerce' && '🛒 E-commerce'}
                        {website.site_type === 'blog' && '📝 Blog'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-green-400">{website.price}€</span>
                      {website.referral_code && (
                        <span className="ml-2 text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded border border-blue-700">
                          Parrainage
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {website.paid ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-900 text-green-300 border border-green-700">
                          Payé
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-900 text-yellow-300 border border-yellow-700">
                          En attente
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {formatDate(website.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div
                          className="w-4 h-4 rounded border mr-2 border-gray-600"
                          style={{ backgroundColor: website.primary_color }}
                        ></div>
                        <span className="text-sm text-gray-400">{website.primary_color}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;