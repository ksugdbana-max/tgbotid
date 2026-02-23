import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, User, CreditCard, ShoppingBag, Clock } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://welldecked-deflected-daniella.ngrok-free.dev';

const UserDetails = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            try {
                const res = await axios.get(`${API_BASE}/admin/users/${id}`);
                setData(res.data);
            } catch (err) {
                console.error("Error fetching user details:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchDetails();
    }, [id]);

    if (loading) return <div className="text-center text-gray-400 py-10">Loading profile...</div>;
    if (!data) return <div className="text-center text-red-400 py-10">User not found.</div>;

    const { user, purchases, deposits } = data;

    return (
        <div className="space-y-6 animate-in pb-10">
            <button
                onClick={() => navigate('/users')}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
            >
                <ArrowLeft size={20} />
                <span>Back to Users</span>
            </button>

            {/* Profile Header */}
            <div className="bg-gray-800/50 p-6 rounded-3xl border border-gray-700">
                <div className="flex flex-col md:flex-row items-center gap-6">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                        <User className="text-white" size={48} />
                    </div>
                    <div className="text-center md:text-left flex-1">
                        <h2 className="text-3xl font-bold">{user.full_name}</h2>
                        <p className="text-gray-400">@{user.username || 'N/A'} • Telegram ID: {user.telegram_id}</p>
                        <div className="mt-4 flex flex-wrap justify-center md:justify-start gap-4">
                            <div className="bg-blue-500/10 px-4 py-2 rounded-xl border border-blue-500/20">
                                <p className="text-xs text-blue-400 uppercase tracking-widest font-bold">Balance</p>
                                <p className="text-xl font-bold">₹{user.balance.toFixed(2)}</p>
                            </div>
                            <div className="bg-purple-500/10 px-4 py-2 rounded-xl border border-purple-500/20">
                                <p className="text-xs text-purple-400 uppercase tracking-widest font-bold">Joined</p>
                                <p className="text-xl font-bold">{new Date(user.created_at).toLocaleDateString()}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Purchase History */}
                <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                        <ShoppingBag className="text-blue-400" size={20} />
                        <h3 className="text-xl font-bold">Purchase History</h3>
                    </div>
                    <div className="bg-gray-800/30 rounded-2xl overflow-hidden border border-gray-700">
                        {purchases.length > 0 ? (
                            <div className="divide-y divide-gray-700">
                                {purchases.map(p => (
                                    <div key={p.id} className="p-4 flex justify-between items-center bg-gray-900/10">
                                        <div>
                                            <p className="font-medium text-sm">Account Purchase</p>
                                            <p className="text-xs text-gray-500">{new Date(p.created_at).toLocaleString()}</p>
                                        </div>
                                        <p className="font-bold text-red-400">-₹{p.amount?.toFixed(2) || '0.00'}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-10 text-center text-gray-500">No purchases found.</div>
                        )}
                    </div>
                </div>

                {/* Deposit History */}
                <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                        <CreditCard className="text-green-400" size={20} />
                        <h3 className="text-xl font-bold">Deposit History</h3>
                    </div>
                    <div className="bg-gray-800/30 rounded-2xl overflow-hidden border border-gray-700">
                        {deposits.length > 0 ? (
                            <div className="divide-y divide-gray-700">
                                {deposits.map(d => (
                                    <div key={d.id} className="p-4 flex justify-between items-center bg-gray-900/10">
                                        <div>
                                            <p className="font-medium text-sm flex items-center space-x-2">
                                                <span>Deposit</span>
                                                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${d.status === 'APPROVED' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                    d.status === 'REJECTED' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                        'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
                                                    }`}>
                                                    {d.status}
                                                </span>
                                            </p>
                                            <p className="text-xs text-gray-500">{new Date(d.created_at).toLocaleString()}</p>
                                        </div>
                                        <p className="font-bold text-green-400">+₹{d.amount.toFixed(2)}</p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="p-10 text-center text-gray-500">No deposits found.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserDetails;
