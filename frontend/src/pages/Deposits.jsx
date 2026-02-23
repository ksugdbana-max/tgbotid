import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CheckCircle2, XCircle, Clock } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://welldecked-deflected-daniella.ngrok-free.dev';
const PER_PAGE = 10;

export default function Deposits() {
    const [deposits, setDeposits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('PENDING');
    const [currentPage, setCurrentPage] = useState(1);

    useEffect(() => {
        fetchDeposits();
    }, []);

    const fetchDeposits = async () => {
        try {
            const token = localStorage.getItem('adminToken');
            const { data } = await axios.get(`${API_BASE}/admin/deposits/enhanced`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setDeposits(data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setLoading(false);
        }
    };

    // Filter and paginate
    const filteredDeposits = deposits.filter(d => d.status === activeTab);
    const totalPages = Math.ceil(filteredDeposits.length / PER_PAGE);
    const paginatedDeposits = filteredDeposits.slice(
        (currentPage - 1) * PER_PAGE,
        currentPage * PER_PAGE
    );

    // Reset to page 1 when changing tabs
    useEffect(() => {
        setCurrentPage(1);
    }, [activeTab]);

    const getStatusIcon = (status) => {
        switch (status) {
            case 'APPROVED':
                return <CheckCircle2 className="w-5 h-5 text-green-400" />;
            case 'REJECTED':
                return <XCircle className="w-5 h-5 text-red-400" />;
            default:
                return <Clock className="w-5 h-5 text-orange-400" />;
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-4 p-4">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">Payment Verifications</h2>

            {/* Tab Navigation */}
            <div className="flex gap-2 mb-6 overflow-x-auto">
                {['PENDING', 'APPROVED', 'REJECTED'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap ${activeTab === tab
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                            }`}
                    >
                        {tab.charAt(0) + tab.slice(1).toLowerCase()}
                    </button>
                ))}
            </div>

            {/* Deposits List - Click to View Details */}
            <div className="space-y-3">
                {paginatedDeposits.length === 0 ? (
                    <p className="text-gray-400 text-center py-8">No {activeTab.toLowerCase()} deposits</p>
                ) : (
                    paginatedDeposits.map(deposit => (
                        <div
                            key={deposit.id}
                            onClick={() => window.location.href = `/deposit/${deposit.id}`}
                            className="bg-gray-800/50 rounded-lg p-4 hover:bg-gray-800/70 transition-colors cursor-pointer"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3 flex-1">
                                    {getStatusIcon(deposit.status)}
                                    <div className="flex-1">
                                        <p className="text-white font-semibold">
                                            ₹{deposit.amount}
                                            {deposit.payment_method === 'OXAPAY' && (
                                                <span className="ml-2 px-2 py-0.5 bg-purple-600/20 text-purple-400 text-xs rounded-full">OxaPay</span>
                                            )}
                                        </p>
                                        <p className="text-gray-400 text-sm">
                                            @{deposit.user.username || deposit.user.full_name}
                                        </p>
                                        <p className="text-blue-400 text-xs font-mono mt-0.5">
                                            {deposit.payment_method === 'OXAPAY' ? `Track ID: ${deposit.oxapay_order_id || 'N/A'}` : `UTR: ${deposit.upi_ref_id || 'N/A'}`}
                                        </p>
                                        <p className="text-gray-500 text-xs mt-1">
                                            {new Date(deposit.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-gray-400 text-sm">
                                    Click to view →
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex justify-center items-center gap-2 mt-6">
                    <button
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
                    >
                        Previous
                    </button>
                    <span className="text-gray-400">
                        Page {currentPage} of {totalPages}
                    </span>
                    <button
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className="px-4 py-2 bg-gray-800 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
                    >
                        Next
                    </button>
                </div>
            )}
        </div>
    );
}
