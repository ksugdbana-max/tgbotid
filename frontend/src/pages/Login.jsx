import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE } from '../api_config';

const Login = ({ onLogin }) => {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [autoLogging, setAutoLogging] = useState(false);

    // Auto-login when opened inside Telegram Mini App
    useEffect(() => {
        const tg = window.Telegram?.WebApp;
        if (tg && tg.initData && tg.initData.length > 0) {
            setAutoLogging(true);
            axios.post(`${API_BASE}/admin/telegram-login`, { init_data: tg.initData })
                .then(res => {
                    if (res.data.token) {
                        localStorage.setItem('admin_token', res.data.token);
                        tg.ready?.();
                        onLogin();
                    }
                })
                .catch(err => {
                    setAutoLogging(false);
                    if (err.response?.status === 403) {
                        setError('Access denied. Only the admin can log in.');
                    } else {
                        // Fall back to password login
                        setError('');
                    }
                });
        }
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await axios.post(`${API_BASE}/admin/login`, { password });
            if (res.data.token) {
                localStorage.setItem('admin_token', res.data.token);
                onLogin();
            }
        } catch (err) {
            console.error("Login Error Details:", err);
            if (err.response && err.response.status === 401) {
                setError('Invalid Password. Please check.');
            } else {
                setError('Login Failed. Check console/network logs.');
            }
        }
    };

    if (autoLogging) {
        return (
            <div className="flex items-center justify-center min-h-[100dvh] bg-black p-4">
                <div className="bg-gray-800 p-10 rounded-3xl border border-gray-700 shadow-2xl text-center">
                    <div className="text-4xl mb-4">🔐</div>
                    <p className="text-white text-lg font-bold">Verifying Telegram identity...</p>
                    <p className="text-gray-400 text-sm mt-2">Auto-logging you in</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-[100dvh] bg-black p-4">
            <form onSubmit={handleSubmit} className="bg-gray-800 p-6 md:p-10 rounded-3xl border border-gray-700 shadow-2xl w-full max-w-sm md:max-w-md animate-in fade-in zoom-in duration-300">
                <h1 className="text-2xl md:text-3xl font-bold mb-6 md:mb-8 text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                    Admin Access
                </h1>
                {error && <p className="text-red-500 mb-4 text-sm text-center bg-red-900/20 p-2 rounded-lg border border-red-900/50">{error}</p>}
                <div className="mb-6">
                    <label className="block text-gray-400 mb-2 text-sm md:text-base">Enter Admin Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        className="w-full bg-gray-700 border-none rounded-xl p-3 md:p-4 ring-1 ring-gray-600 focus:ring-2 focus:ring-purple-500 outline-none text-center text-xl md:text-2xl tracking-widest"
                        placeholder="••••••••"
                        autoFocus
                    />
                </div>
                <button type="submit" className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-3 md:py-4 rounded-xl transition-all active:scale-95 text-base md:text-lg shadow-lg shadow-purple-900/20">
                    Unlock Dashboard
                </button>
            </form>
        </div>
    );
};

export default Login;
