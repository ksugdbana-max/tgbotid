import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Package, Loader2, Check, X, AlertCircle } from 'lucide-react';
import SessionGeneratorModal from '../components/SessionGeneratorModal';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://welldecked-deflected-daniella.ngrok-free.dev';

// Phone prefix to country mapping
const PHONE_COUNTRY_MAP = {
    '+1': 'United States',
    '+44': 'United Kingdom',
    '+91': 'India',
    '+86': 'China',
    '+81': 'Japan',
    '+33': 'France',
    '+49': 'Germany',
    '+7': 'Russia',
    '+61': 'Australia',
    '+55': 'Brazil',
    '+52': 'Mexico',
    '+34': 'Spain',
    '+39': 'Italy',
    '+82': 'South Korea',
    '+62': 'Indonesia',
    '+90': 'Turkey',
    '+966': 'Saudi Arabia',
    '+971': 'UAE',
    '+20': 'Egypt',
    '+27': 'South Africa'
};

const Accounts = () => {
    const [accounts, setAccounts] = useState([]);
    const [countries, setCountries] = useState([]);
    const [phoneNumber, setPhoneNumber] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [filterCountry, setFilterCountry] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    // Session Generator States
    const [showSessionGen, setShowSessionGen] = useState(false);
    const [sessionGenStep, setSessionGenStep] = useState(1);
    const [sessionGenLoading, setSessionGenLoading] = useState(false);
    const [sessionGenError, setSessionGenError] = useState('');
    const [sessionId, setSessionId] = useState('');
    const [otpCode, setOtpCode] = useState('');
    const [twoFAPass, setTwoFAPass] = useState('');
    const [generatedSession, setGeneratedSession] = useState('');
    const [detected2FA, setDetected2FA] = useState(false);

    useEffect(() => {
        fetchAccounts();
        fetchCountries();
    }, []);

    const fetchAccounts = async () => {
        const res = await axios.get(`${API_BASE}/admin/accounts`);
        setAccounts(res.data);
    };

    const fetchCountries = async () => {
        const res = await axios.get(`${API_BASE}/admin/countries`);
        setCountries(res.data);
    };

    const detectCountryFromPhone = (phone) => {
        for (const [prefix, countryName] of Object.entries(PHONE_COUNTRY_MAP)) {
            if (phone.startsWith(prefix)) {
                const country = countries.find(c => c.name.toLowerCase().includes(countryName.toLowerCase()));
                return country?.id || null;
            }
        }
        return null;
    };

    const handleGenerateSession = () => {
        if (!phoneNumber || phoneNumber.length < 10) {
            setMessage({ type: 'error', text: 'Please enter a valid phone number' });
            return;
        }
        setShowSessionGen(true);
        setSessionGenStep(1);
        setSessionGenError('');
        setMessage({ type: '', text: '' });
    };

    const handleSendOTP = async () => {
        setSessionGenLoading(true);
        setSessionGenError('');
        try {
            const res = await axios.post(`${API_BASE}/admin/session/start`, {
                phone_number: phoneNumber
            });
            if (res.data.success) {
                setSessionId(res.data.session_id);
                setSessionGenStep(2);
            } else {
                setSessionGenError(res.data.message || 'Failed to send OTP');
            }
        } catch (err) {
            setSessionGenError(err.response?.data?.message || 'Network error');
        } finally {
            setSessionGenLoading(false);
        }
    };

    const handleVerifyOTP = async () => {
        setSessionGenLoading(true);
        setSessionGenError('');
        try {
            const res = await axios.post(`${API_BASE}/admin/session/verify-otp`, {
                session_id: sessionId,
                phone_number: phoneNumber,
                otp_code: otpCode
            });
            if (res.data.success) {
                if (res.data.needs_2fa) {
                    setDetected2FA(true);
                    setSessionGenStep(3);
                } else {
                    // No 2FA - session generated!
                    await finalizeAccount(res.data.session_string, '');
                }
            } else {
                setSessionGenError(res.data.message || 'Invalid OTP');
            }
        } catch (err) {
            setSessionGenError(err.response?.data?.message || 'Verification failed');
        } finally {
            setSessionGenLoading(false);
        }
    };

    const handleVerify2FA = async () => {
        setSessionGenLoading(true);
        setSessionGenError('');
        try {
            const res = await axios.post(`${API_BASE}/admin/session/verify-2fa`, {
                session_id: sessionId,
                password: twoFAPass
            });
            if (res.data.success) {
                await finalizeAccount(res.data.session_string, twoFAPass);
            } else {
                setSessionGenError(res.data.message || 'Invalid 2FA password');
            }
        } catch (err) {
            setSessionGenError(err.response?.data?.message || '2FA verification failed');
        } finally {
            setSessionGenLoading(false);
        }
    };

    const finalizeAccount = async (sessionString, twofa) => {
        try {
            const countryId = detectCountryFromPhone(phoneNumber);
            if (!countryId) {
                setMessage({ type: 'error', text: 'Could not detect country. Please add country first.' });
                setShowSessionGen(false);
                return;
            }

            await axios.post(`${API_BASE}/admin/accounts`, {
                country_id: countryId,
                phone_number: phoneNumber,
                session_data: sessionString,
                type: 'ID',
                twofa_password: twofa
            });

            setMessage({ type: 'success', text: '✅ Account added successfully!' });
            setPhoneNumber('');
            setOtpCode('');
            setTwoFAPass('');
            setGeneratedSession('');
            setShowSessionGen(false);
            setSessionGenStep(1);
            fetchAccounts();
        } catch (err) {
            setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to add account' });
        }
    };

    const getCountryById = (id) => countries.find(c => c.id === id);

    const filteredAccounts = accounts.filter(acc => {
        const country = getCountryById(acc.country_id);
        const matchesCountry = !filterCountry || acc.country_id === parseInt(filterCountry);
        const matchesSearch = !searchTerm ||
            acc.phone_number.includes(searchTerm) ||
            country?.name.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesCountry && matchesSearch;
    });

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div>
                <h2 className="text-3xl font-bold text-white flex items-center gap-2">
                    📱 Accounts
                </h2>
                <p className="text-gray-400 mt-1">
                    Add and manage Telegram accounts
                </p>
            </div>

            {/* Message Alert */}
            {message.text && (
                <div className={`p-4 rounded-xl flex items-center gap-3 ${message.type === 'success' ? 'bg-green-500/20 border border-green-500/50 text-green-400' :
                    'bg-red-500/20 border border-red-500/50 text-red-400'
                    }`}>
                    {message.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
                    <span>{message.text}</span>
                    <button onClick={() => setMessage({ type: '', text: '' })} className="ml-auto">
                        <X size={18} />
                    </button>
                </div>
            )}

            {/* Simple Add Account Form */}
            <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                    ➕ Add New Account
                </h3>
                <div className="space-y-4">
                    <div>
                        <label className="block text-gray-400 mb-2 text-sm font-medium">
                            📞 Phone Number (with country code)
                        </label>
                        <input
                            type="text"
                            value={phoneNumber}
                            onChange={e => setPhoneNumber(e.target.value)}
                            placeholder="+91 9876543210"
                            className="w-full bg-gray-700 border-none rounded-xl p-4 text-lg ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white placeholder:text-gray-500 font-mono"
                        />
                        <p className="text-gray-500 text-xs mt-2">
                            💡 Enter phone with country code (e.g., +91 for India, +1 for USA)
                        </p>
                    </div>

                    <button
                        onClick={handleGenerateSession}
                        disabled={loading || !phoneNumber}
                        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold py-4 rounded-xl transition-all flex items-center justify-center gap-2 text-lg shadow-lg"
                    >
                        {loading ? (
                            <>
                                <Loader2 size={24} className="animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                🔐 Generate Session & Add Account
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            placeholder="Search accounts..."
                            className="w-full bg-gray-700 border-none rounded-xl p-3 pl-10 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white placeholder:text-gray-500"
                        />
                    </div>
                    <select
                        value={filterCountry}
                        onChange={e => setFilterCountry(e.target.value)}
                        className="w-full bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white"
                    >
                        <option value="">All Countries</option>
                        {countries.map(c => <option key={c.id} value={c.id}>{c.emoji} {c.name}</option>)}
                    </select>
                </div>
            </div>

            {/* Accounts List */}
            <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Package size={20} />
                    All Accounts ({filteredAccounts.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                    {filteredAccounts.length === 0 ? (
                        <p className="text-gray-400 text-center py-8">No accounts found</p>
                    ) : (
                        filteredAccounts.map(acc => {
                            const country = getCountryById(acc.country_id);
                            return (
                                <div key={acc.id} className="bg-gray-700/50 p-3 rounded-lg hover:bg-gray-700 transition-colors">
                                    <div className="flex items-center justify-between flex-wrap gap-2">
                                        <div className="flex items-center gap-3 flex-1">
                                            <span className="text-2xl">{country?.emoji}</span>
                                            <div className="flex-1">
                                                <p className="text-white font-medium font-mono">{acc.phone_number}</p>
                                                <p className="text-gray-400 text-sm">
                                                    {country?.name} • {acc.type}
                                                </p>
                                                {acc.twofa_password && (
                                                    <p className="text-blue-400 text-sm mt-1 font-mono">
                                                        🔐 2FA: {acc.twofa_password}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${acc.is_sold === false
                                            ? 'bg-green-600/20 text-green-400'
                                            : 'bg-red-600/20 text-red-400'
                                            }`}>
                                            {acc.is_sold === false ? 'Available' : 'Sold'}
                                        </span>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>

            {/* Session Generator Modal */}
            <SessionGeneratorModal
                show={showSessionGen}
                onClose={() => setShowSessionGen(false)}
                phoneNumber={phoneNumber}
                step={sessionGenStep}
                loading={sessionGenLoading}
                error={sessionGenError}
                onSendOTP={handleSendOTP}
                onVerifyOTP={handleVerifyOTP}
                onVerify2FA={handleVerify2FA}
                otpCode={otpCode}
                setOtpCode={setOtpCode}
                twoFAPass={twoFAPass}
                setTwoFAPass={setTwoFAPass}
            />
        </div>
    );
};

export default Accounts;
