import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend } from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import './App.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend);

const API_BASE = 'http://localhost:5000/api';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [kpis, setKpis] = useState({});
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState({});

  useEffect(() => {
    fetchKpis();
    fetchChartData('sales_trend');
  }, []);

  const fetchKpis = async () => {
    try {
      const response = await axios.get(`${API_BASE}/kpis`);
      setKpis(response.data);
    } catch (error) {
      console.error('Error fetching KPIs:', error);
    }
  };

  const fetchChartData = async (chartType) => {
    try {
      const response = await axios.get(`${API_BASE}/chart/${chartType}`);
      setChartData({ type: chartType, data: response.data });
    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/query`, { query });
      setResults(response.data);
    } catch (error) {
      console.error('Error executing query:', error);
      setResults({ error: error.response?.data?.error || 'An error occurred' });
    } finally {
      setLoading(false);
    }
  };

  const renderChart = () => {
    if (!chartData.data) return null;

    const { type, data } = chartData;

    switch (type) {
      case 'sales_trend':
        return (
          <Line 
            data={{
              labels: data.map(item => item.month),
              datasets: [
                {
                  label: 'Monthly Revenue',
                  data: data.map(item => item.revenue),
                  borderColor: 'rgb(75, 192, 192)',
                  tension: 0.1
                }
              ]
            }}
          />
        );
      case 'product_performance':
        return (
          <Bar 
            data={{
              labels: data.map(item => item.category),
              datasets: [
                {
                  label: 'Revenue by Category',
                  data: data.map(item => item.revenue),
                  backgroundColor: 'rgba(153, 102, 255, 0.6)'
                }
              ]
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Business Intelligence Dashboard</h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
            <p className="text-2xl font-semibold">${(kpis.total_revenue || 0).toLocaleString()}</p>
            <p className={`text-sm ${(kpis.revenue_growth || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {kpis.revenue_growth > 0 ? '↑' : '↓'} {Math.abs(kpis.revenue_growth || 0).toFixed(1)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
            <p className="text-2xl font-semibold">{kpis.total_orders || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Total Customers</h3>
            <p className="text-2xl font-semibold">{kpis.total_customers || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-medium text-gray-500">Revenue Growth</h3>
            <p className={`text-2xl font-semibold ${(kpis.revenue_growth || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {kpis.revenue_growth > 0 ? '+' : ''}{kpis.revenue_growth?.toFixed(1) || 0}%
            </p>
          </div>
        </div>

        {/* Query Interface */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="query" className="block text-sm font-medium text-gray-700">
                Ask a Business Question
              </label>
              <input
                type="text"
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Show me top 5 customers by revenue"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-2 border"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Execute Query'}
            </button>
          </form>

          {results?.sql_query && (
            <div className="mt-4 p-4 bg-gray-50 rounded-md">
              <h4 className="font-medium text-gray-700">Generated SQL:</h4>
              <code className="text-sm bg-gray-800 text-green-400 p-2 rounded block mt-1">
                {results.sql_query}
              </code>
            </div>
          )}

          {results?.error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <h4 className="font-medium text-red-800">Error:</h4>
              <p className="text-red-600">{results.error}</p>
            </div>
          )}

          {results?.results && (
            <div className="mt-6">
              <h4 className="font-medium text-gray-700 mb-2">Results ({results.count} rows):</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(results.results[0] || {}).map(key => (
                        <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {results.results.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((value, cellIndex) => (
                          <td key={cellIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {value?.toString() || ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Charts */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex space-x-4 mb-4">
            <button
              onClick={() => fetchChartData('sales_trend')}
              className="bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm"
            >
              Sales Trend
            </button>
            <button
              onClick={() => fetchChartData('product_performance')}
              className="bg-green-100 text-green-700 px-3 py-1 rounded text-sm"
            >
              Product Performance
            </button>
            <button
              onClick={() => fetchChartData('customer_analytics')}
              className="bg-purple-100 text-purple-700 px-3 py-1 rounded text-sm"
            >
              Customer Analytics
            </button>
          </div>
          <div className="h-96">
            {renderChart()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;