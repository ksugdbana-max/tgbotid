import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../api_config';

const PaymentSettings = () => {
    const [upiId, setUpiId] = useState('');
    const [qrImage, setQrImage] = useState(null); // File object
    const [qrPreview, setQrPreview] = useState(''); // URL for preview
    const [channelLink, setChannelLink] = useState('');
    const [ownerUsername, setOwnerUsername] = useState('');
    const [exchangeRate, setExchangeRate] = useState(84.0);
    const [settings, setSettings] = useState({ bot_channel_link: '', bot_owner_username: '' });
    const [apiId, setApiId] = useState('');
    const [apiHash, setApiHash] = useState('');
    const [apiSaving, setApiSaving] = useState(false);
    const [apiMessage, setApiMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [showRedeployModal, setShowRedeployModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');
    const [webhookFixing, setWebhookFixing] = useState(false);
    const [webhookMessage, setWebhookMessage] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const token = localStorage.getItem('admin_token');
            if (!token) {
                navigate('/login');
                return;
            }
            // Fetch payment settings
            const response = await axios.get(`${API_BASE}/admin/settings/payment`);
            setUpiId(response.data.upi_id || '');
            setQrPreview(response.data.qr_image || '');
            setChannelLink(response.data.channel_link || '');
            setOwnerUsername(response.data.owner_username || '');

            // Fetch exchange rate
            try {
                const rateRes = await axios.get(`${API_BASE}/admin/settings/exchange-rate`);
                if (rateRes.data && rateRes.data.rate) {
                    setExchangeRate(rateRes.data.rate);
                }
            } catch (err) {
                console.error("Error fetching exchange rate:", err);
            }

            // Fetch Telegram API credentials
            try {
                const apiRes = await axios.get(`${API_BASE}/admin/settings/telegram-api`);
                setApiId(apiRes.data.api_id || '');
                setApiHash(apiRes.data.api_hash || '');
            } catch (err) {
                console.error("Error fetching API credentials:", err);
            }

            setLoading(false);
        } catch (error) {
            console.error("Error fetching settings:", error);
            setMessage("Failed to load settings.");
            setLoading(false);
        }
    };

    const handleSaveApiCredentials = async () => {
        if (!apiId || !apiHash) {
            setApiMessage('❌ Both API ID and API Hash are required.');
            return;
        }
        setApiSaving(true);
        setApiMessage('');
        try {
            await axios.post(`${API_BASE}/admin/settings/telegram-api`, {
                api_id: apiId.trim(),
                api_hash: apiHash.trim()
            });
            setApiMessage('✅ Telegram API credentials saved! Session generation will now work.');
        } catch (error) {
            setApiMessage(`❌ ${error.response?.data?.detail || 'Failed to save credentials.'}`);
        } finally {
            setApiSaving(false);
        }
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setQrImage(file);
            // Create local preview
            const reader = new FileReader();
            reader.onloadend = () => {
                setQrPreview(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setMessage('');

        // Validate channel link
        if (channelLink && channelLink.trim()) {
            const channelLower = channelLink.toLowerCase();
            if (channelLower.includes('yourchannel') || channelLower.includes('your_channel')) {
                setMessage('❌ Please enter YOUR actual channel link, not the placeholder "yourchannel"!');
                setSaving(false);
                return;
            }
            if (!channelLink.startsWith('http')) {
                setMessage('❌ Channel link must start with https://');
                setSaving(false);
                return;
            }
        }

        // Validate owner username
        if (ownerUsername && ownerUsername.trim()) {
            const ownerLower = ownerUsername.toLowerCase();
            if (ownerLower.includes('yourusername') || ownerLower.includes('your_username')) {
                setMessage('❌ Please enter YOUR actual username, not "@yourusername"!');
                setSaving(false);
                return;
            }
            if (!ownerUsername.startsWith('@')) {
                setMessage('❌ Owner username must start with @');
                setSaving(false);
                return;
            }
        }

        const formData = new FormData();
        formData.append('upi_id', upiId);
        if (channelLink && channelLink.trim()) {
            formData.append('channel_link', channelLink.trim());
        }
        if (ownerUsername && ownerUsername.trim()) {
            formData.append('owner_username', ownerUsername.trim());
        }
        if (qrImage) {
            formData.append('qr_image', qrImage);
        }

        try {
            // Save Payment Settings
            await axios.post(`${API_BASE}/admin/settings/payment`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            // Save Exchange Rate
            await axios.post(`${API_BASE}/admin/settings/exchange-rate`, {
                rate: parseFloat(exchangeRate)
            });

            setMessage('✅ Settings updated successfully!');
            fetchSettings(); // Refresh to get server URLs
        } catch (error) {
            console.error("Error saving settings:", error);
            const errorMsg = error.response?.data?.detail || 'Failed to save settings.';
            setMessage(`❌ ${errorMsg}`);
        } finally {
            setSaving(false);
        }
    };

    const handleFixWebhook = async () => {
        setWebhookFixing(true);
        setWebhookMessage('');

        try {
            const response = await axios.post(`${API_BASE}/api/fix-webhook`);

            if (response.data.success) {
                setWebhookMessage(`✅ ${response.data.message}`);
                if (response.data.webhook_info) {
                    console.log('Webhook Info:', response.data.webhook_info);
                }
            } else {
                setWebhookMessage(`❌ ${response.data.message}`);
            }
        } catch (error) {
            console.error("Error fixing webhook:", error);
            setWebhookMessage('❌ Failed to fix webhook. Check backend logs.');
        } finally {
            setWebhookFixing(false);
        }
    };

    if (loading) return <div className="p-8 text-white">Loading settings...</div>;

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold text-white mb-8">💳 Payment Settings</h1>

            <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 shadow-lg">
                <form onSubmit={handleSubmit} className="space-y-8">

                    {/* UPI ID Section */}
                    <div>
                        <label className="block text-slate-400 text-sm font-medium mb-2">
                            UPI ID (VPA)
                        </label>
                        <input
                            type="text"
                            value={upiId}
                            onChange={(e) => setUpiId(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                            placeholder="e.g. business@upi"
                            required
                        />
                        <p className="text-xs text-slate-500 mt-2">
                            This UPI ID will be shown to users for manual deposits.
                        </p>
                    </div>

                    {/* QR Code Section */}
                    <div>
                        <label className="block text-slate-400 text-sm font-medium mb-4">
                            QR Code Image
                        </label>

                        <div className="flex flex-col md:flex-row gap-8 items-start">

                            {/* Preview Area */}
                            <div className="w-48 h-48 bg-slate-900 rounded-lg border-2 border-dashed border-slate-700 flex items-center justify-center overflow-hidden relative">
                                {qrPreview ? (
                                    <img
                                        src={qrPreview}
                                        alt="QR Code"
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <span className="text-slate-600 text-sm">No QR Uploaded</span>
                                )}
                            </div>

                            {/* Upload Controls */}
                            <div className="flex-1">
                                <label className="cursor-pointer bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium transition-colors inline-block mb-3">
                                    <span>Upload New QR Code</span>
                                    <input
                                        type="file"
                                        accept="image/*"
                                        onChange={handleImageChange}
                                        className="hidden"
                                    />
                                </label>
                                <p className="text-sm text-slate-400">
                                    Supports JPG, PNG, WEBP. <br />
                                    Max file size: 5MB.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Bot Configuration Section */}
                    <div className="border-t border-slate-700 pt-8 mt-8">
                        <h3 className="text-xl font-bold text-white mb-6">📢 Bot Configuration</h3>

                        <div className="space-y-6">
                            {/* Channel Link */}
                            <div>
                                <label className="block text-slate-400 text-sm font-medium mb-2">
                                    Channel Link
                                </label>
                                <input
                                    type="url"
                                    value={channelLink}
                                    onChange={(e) => setChannelLink(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                                    placeholder="https://t.me/yourchannel"
                                />
                                <p className="text-xs text-slate-500 mt-2">
                                    ⚠️ <strong>IMPORTANT:</strong> Enter YOUR actual Telegram channel URL, not the placeholder text!
                                </p>
                            </div>

                            {/* Owner Username */}
                            <div>
                                <label className="block text-slate-400 text-sm font-medium mb-2">
                                    Owner Username
                                </label>
                                <input
                                    type="text"
                                    value={ownerUsername}
                                    onChange={(e) => setOwnerUsername(e.target.value)}
                                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                                    placeholder="@yourusername"
                                />
                                <p className="text-xs text-slate-500 mt-2">
                                    ⚠️ <strong>IMPORTANT:</strong> Enter YOUR actual Telegram username (must start with @), not "@yourusername"!
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Exchange Rate Section */}
                    <div className="border-t border-slate-700 pt-8 mt-8">
                        <h3 className="text-xl font-bold text-white mb-6">💱 Exchange Rate (OxaPay)</h3>
                        <div>
                            <label className="block text-slate-400 text-sm font-medium mb-2">
                                USD to INR Rate
                            </label>
                            <div className="flex items-center gap-3">
                                <span className="text-slate-400 font-medium">1 USD = ₹</span>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={exchangeRate}
                                    onChange={(e) => setExchangeRate(e.target.value)}
                                    className="w-48 bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                                    placeholder="84.0"
                                    required
                                />
                                <span className="text-slate-400 font-medium">INR</span>
                            </div>
                            <p className="text-xs text-slate-500 mt-2">
                                Used to convert OxaPay USD deposits into bot INR balance.
                            </p>
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="pt-4 border-t border-slate-700">
                        <button
                            type="submit"
                            disabled={saving}
                            className={`w-full py-3 rounded-lg font-bold text-lg transition-all ${saving
                                ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg shadow-purple-900/50'
                                }`}
                        >
                            {saving ? 'Saving...' : '💾 Save Payment Settings'}
                        </button>
                    </div>

                    {/* Feedback Message */}
                    {message && (
                        <div className={`p-4 rounded-lg text-center font-medium ${message.includes('✅')
                            ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                            : 'bg-red-500/10 text-red-400 border border-red-500/20'
                            }`}>
                            {message}
                        </div>
                    )}

                </form>
            </div>

            {/* Telegram API Credentials Section */}
            <div className="mt-8 bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-2">🔑 Telegram API Credentials</h3>
                <p className="text-slate-400 text-sm mb-6">
                    Required for session generation (auto-login accounts). Get these from{' '}
                    <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" className="text-purple-400 underline hover:text-purple-300">my.telegram.org</a>
                    {' '}→ API development tools.
                </p>

                <div className="space-y-4">
                    <div>
                        <label className="block text-slate-400 text-sm font-medium mb-2">API ID</label>
                        <input
                            type="text"
                            value={apiId}
                            onChange={(e) => setApiId(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                            placeholder="e.g. 12345678"
                        />
                    </div>
                    <div>
                        <label className="block text-slate-400 text-sm font-medium mb-2">API Hash</label>
                        <input
                            type="password"
                            value={apiHash}
                            onChange={(e) => setApiHash(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-purple-500 outline-none transition-all"
                            placeholder="32-character hash string"
                        />
                    </div>
                </div>

                <button
                    onClick={handleSaveApiCredentials}
                    disabled={apiSaving}
                    className={`mt-4 w-full py-3 rounded-lg font-bold text-lg transition-all ${apiSaving
                        ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg shadow-purple-900/50'
                        }`}
                >
                    {apiSaving ? 'Saving...' : '💾 Save API Credentials'}
                </button>

                {apiMessage && (
                    <div className={`mt-4 p-4 rounded-lg text-center font-medium ${apiMessage.includes('✅')
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'
                        }`}>
                        {apiMessage}
                    </div>
                )}
            </div>

            {/* Webhook Fix Section */}
            <div className="mt-8 bg-slate-800 rounded-xl p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">🔗 Webhook Management</h3>
                <p className="text-slate-400 text-sm mb-6">
                    Use this button after every deployment to refresh the webhook connection.
                    This ensures the bot always responds to messages.
                </p>

                <button
                    onClick={handleFixWebhook}
                    disabled={webhookFixing}
                    className={`w-full py-3 rounded-lg font-bold text-lg transition-all ${webhookFixing
                        ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white shadow-lg shadow-blue-900/50'
                        }`}
                >
                    {webhookFixing ? '🔄 Fixing Webhook...' : '🔧 Fix Webhook Now'}
                </button>

                <button onClick={() => setShowRedeployModal(true)}
                    className="mt-4 w-full py-3 rounded-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl transition-all">
                    🚀 Redeploy Bot
                </button>

                {webhookMessage && (
                    <div className={`mt-4 p-4 rounded-lg text-center font-medium ${webhookMessage.includes('✅')
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                        : 'bg-red-500/10 text-red-400 border border-red-500/20'
                        }`}>
                        {webhookMessage}
                    </div>
                )}
            </div>

            <div className="mt-8 bg-blue-500/10 border border-blue-500/20 p-6 rounded-xl">
                <h3 className="text-blue-400 font-bold mb-2">ℹ️ How this works</h3>
                <p className="text-slate-300 text-sm">
                    Changes made here are <b>updated instantly</b> on the Telegram Bot.
                    When a user clicks "Determine Payment", the bot fetches the latest UPI ID and QR Code from here directly.
                    No need to restart the bot!
                </p>
            </div>

            {/* Redeploy Modal */}
            {showRedeployModal && (
                <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-2xl border border-gray-700 max-w-2xl w-full p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-2xl font-bold text-white">🚀 Redeploy Bot on Koyeb</h3>
                            <button onClick={() => setShowRedeployModal(false)} className="text-gray-400 hover:text-white text-2xl">
                                ✕
                            </button>
                        </div>

                        <div className="space-y-4 text-gray-300">
                            <p className="text-lg">Follow these steps to redeploy your bot:</p>

                            <div className="bg-gray-900/50 rounded-lg p-4 space-y-3">
                                <div className="flex items-start space-x-3">
                                    <span className="text-2xl">1️⃣</span>
                                    <div>
                                        <p className="font-semibold text-white">Go to Koyeb Dashboard</p>
                                        <a href="https://app.koyeb.com" target="_blank" rel="noopener noreferrer"
                                            className="text-blue-400 hover:text-blue-300 underline">
                                            https://app.koyeb.com
                                        </a>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-3">
                                    <span className="text-2xl">2️⃣</span>
                                    <div>
                                        <p className="font-semibold text-white">Find Your Bot Service</p>
                                        <p className="text-sm">Click on your bot service in the list</p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-3">
                                    <span className="text-2xl">3️⃣</span>
                                    <div>
                                        <p className="font-semibold text-white">Click "Redeploy"</p>
                                        <p className="text-sm">Or click the three dots (⋮) → "Redeploy"</p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-3">
                                    <span className="text-2xl">4️⃣</span>
                                    <div>
                                        <p className="font-semibold text-white">Wait for Deployment</p>
                                        <p className="text-sm">Usually takes 2-3 minutes</p>
                                    </div>
                                </div>
                            </div>

                            <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                                <p className="text-blue-300">
                                    💡 <strong>Tip:</strong> After redeploying, your bot will restart with all the latest changes!
                                </p>
                            </div>
                        </div>

                        <div className="mt-6 flex justify-end">
                            <button onClick={() => setShowRedeployModal(false)}
                                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PaymentSettings;
