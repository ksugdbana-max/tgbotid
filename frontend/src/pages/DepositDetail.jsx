import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, CheckCircle, XCircle } from 'lucide-react';

import { API_BASE } from '../api_config';

export default function DepositDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [deposit, setDeposit] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDeposit();
    }, [id]);

    const fetchDeposit = async () => {
        try {
            const token = localStorage.getItem('admin_token');
            const { data } = await axios.get(`${API_BASE}/admin/deposits/enhanced`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const foundDeposit = data.find(d => d.id === parseInt(id));
            setDeposit(foundDeposit);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async () => {
        try {
            const token = localStorage.getItem('admin_token');
            await axios.patch(
                `${API_BASE}/admin/deposits/${id}`,
                { status: 'APPROVED' },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            navigate('/deposits');
        } catch (err) {
            console.error(err);
        }
    };

    const handleReject = async () => {
        try {
            const token = localStorage.getItem('admin_token');
            await axios.patch(
                `${API_BASE}/admin/deposits/${id}`,
                { status: 'REJECTED' },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            navigate('/deposits');
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!deposit) {
        return (
            <div className="p-4 text-center">
                <p className="text-gray-400">Deposit not found</p>
                <button
                    onClick={() => navigate('/deposits')}
                    className="mt-4 text-blue-400 hover:text-blue-300"
                >
                    Back to Deposits
                </button>
            </div>
        );
    }

    return (
        <div className="p-4 space-y-4">
            {/* Header */}
            <div className="flex items-center gap-3">
                <button
                    onClick={() => navigate('/deposits')}
                    className="text-gray-400 hover:text-white transition-colors"
                >
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <h2 className="text-2xl font-bold text-white">Deposit Details</h2>
            </div>

            {/* Deposit Info Card */}
            <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <h3 className="text-xl font-semibold text-white">₹{deposit.amount}</h3>
                        {deposit.payment_method === 'OXAPAY' && (
                            <span className="px-3 py-1 bg-purple-600/20 text-purple-400 text-sm font-medium rounded-full">
                                OxaPay (Crypto)
                            </span>
                        )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${deposit.status === 'APPROVED' ? 'bg-green-600/20 text-green-400' :
                        deposit.status === 'REJECTED' ? 'bg-red-600/20 text-red-400' :
                            'bg-orange-600/20 text-orange-400'
                        }`}>
                        {deposit.status === 'APPROVED' && deposit.payment_method === 'OXAPAY' ? 'Auto-Approved' : deposit.status}
                    </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                        <p className="text-gray-400">User</p>
                        <p className="text-white font-medium">{deposit.user.full_name}</p>
                    </div>
                    <div>
                        <p className="text-gray-400">Username</p>
                        <p className="text-white font-medium">@{deposit.user.username || 'N/A'}</p>
                    </div>
                    <div>
                        <p className="text-gray-400">Telegram ID</p>
                        <p className="text-white font-medium">{deposit.user.telegram_id}</p>
                    </div>
                    <div>
                        <p className="text-gray-400">Date</p>
                        <p className="text-white font-medium">
                            {new Date(deposit.created_at).toLocaleString()}
                        </p>
                    </div>
                </div>

                <div>
                    <p className="text-gray-400 mb-2">
                        {deposit.payment_method === 'OXAPAY' ? 'OxaPay Track ID' : 'UTR / Transaction Ref ID'}
                    </p>
                    <p className="text-white font-mono bg-gray-700 p-3 rounded-lg break-all">
                        {deposit.payment_method === 'OXAPAY' ? deposit.oxapay_order_id : deposit.upi_ref_id}
                    </p>
                </div>
            </div>

            {/* Screenshot */}
            {deposit.screenshot_path && (
                <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <p className="text-gray-400 mb-4">Payment Screenshot</p>
                    <img
                        src={deposit.screenshot_path.startsWith('tg_file_id:')
                            ? `${API_BASE}/admin/deposits/photo/${deposit.screenshot_path.split(':')[1]}`
                            : (deposit.screenshot_path.startsWith('http') ? deposit.screenshot_path : `${API_BASE}/${deposit.screenshot_path}`)}
                        alt="Payment proof"
                        className="rounded-lg w-full max-w-2xl mx-auto"
                    />
                </div>
            )}

            {/* Action Buttons */}
            {deposit.status === 'PENDING' && deposit.payment_method !== 'OXAPAY' && (
                <div className="flex gap-3">
                    <button
                        onClick={handleApprove}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                        <CheckCircle className="w-5 h-5" />
                        Approve Deposit
                    </button>
                    <button
                        onClick={handleReject}
                        className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
                    >
                        <XCircle className="w-5 h-5" />
                        Reject Deposit
                    </button>
                </div>
            )}
            {deposit.status === 'PENDING' && deposit.payment_method === 'OXAPAY' && (
                <div className="bg-purple-900/30 border border-purple-500/30 p-4 rounded-xl text-center">
                    <p className="text-purple-300">
                        ⏳ Waiting for automatic confirmation from OxaPay. No manual action required.
                    </p>
                </div>
            )}
        </div>
    );
}
