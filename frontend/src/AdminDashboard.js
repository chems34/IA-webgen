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
            <button
              onClick={() => window.location.href = "/"}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors shadow-lg"
            >
              🏠 Retour à l'app
            </button>
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
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Statistiques Détaillées</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Sites payés:</span>
                  <span className="font-medium">{stats.paid_websites} / {stats.total_websites}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Codes de parrainage créés:</span>
                  <span className="font-medium">{stats.total_referrals}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Parrainages utilisés:</span>
                  <span className="font-medium">{stats.used_referrals}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Revenus moyens par site:</span>
                  <span className="font-medium">
                    {stats.paid_websites > 0 ? (stats.total_revenue / stats.paid_websites).toFixed(2) : 0}€
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🎯 Sites Récents</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {stats.recent_websites.map((website) => (
                  <div key={website.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div>
                      <p className="font-medium text-sm">{website.business_name}</p>
                      <p className="text-xs text-gray-500">
                        {website.site_type} • {formatDate(website.created_at)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{website.price}€</p>
                      <div className="flex items-center space-x-1">
                        {website.paid ? (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Payé</span>
                        ) : (
                          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">En attente</span>
                        )}
                        {website.referral_used && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Parrainage</span>
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
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">🌐 Tous les Sites Web</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entreprise
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Prix
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    État
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Couleur
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {websites.map((website) => (
                  <tr key={website.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {website.business_name}
                        </div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {website.description}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">
                        {website.site_type === 'vitrine' && '🏪 Vitrine'}
                        {website.site_type === 'ecommerce' && '🛒 E-commerce'}
                        {website.site_type === 'blog' && '📝 Blog'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">{website.price}€</span>
                      {website.referral_code && (
                        <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          Parrainage
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {website.paid ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          Payé
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          En attente
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(website.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div
                          className="w-4 h-4 rounded border mr-2"
                          style={{ backgroundColor: website.primary_color }}
                        ></div>
                        <span className="text-sm text-gray-500">{website.primary_color}</span>
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