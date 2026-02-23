import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://welldecked-deflected-daniella.ngrok-free.dev';

const Dashboard = () => {
    const [stats, setStats] = useState({
        total_sales: 0,
        total_users: 0,
        pending_deposits: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const token = localStorage.getItem('adminToken');
            const { data } = await axios.get(`${API_BASE}/admin/stats`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setStats(data);
        } catch (err) {
            console.error('Failed to fetch stats:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-2xl md:text-3xl font-bold mb-6 md:mb-8 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                Dashboard Overview
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                <StatCard label="Total Sales" value={loading ? "..." : `₹${stats.total_sales.toFixed(2)}`} />
                <StatCard label="Total Users" value={loading ? "..." : stats.total_users} />
                <StatCard label="Pending Deposits" value={loading ? "..." : stats.pending_deposits} highlight />
            </div>
        </div>
    );
};

const StatCard = ({ label, value, highlight }) => (
    <div className="bg-gray-800 p-5 md:p-6 rounded-2xl border border-gray-700 shadow-lg hover:border-blue-500/50 transition-all duration-300 group">
        <p className="text-gray-400 text-sm mb-1 group-hover:text-blue-400 transition-colors uppercase tracking-wider font-semibold">
            {label}
        </p>
        <h3 className={`text-3xl md:text-4xl font-bold ${highlight ? 'text-orange-400' : 'text-white'}`}>
            {value}
        </h3>
    </div>
);

export default Dashboard;
