import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, X } from 'lucide-react';

import { API_BASE } from '../api_config';

// Common country flags for quick selection
const COMMON_FLAGS = [
    { emoji: '🇮🇳', name: 'India' },
    { emoji: '🇺🇸', name: 'United States' },
    { emoji: '🇬🇧', name: 'United Kingdom' },
    { emoji: '🇨🇦', name: 'Canada' },
    { emoji: '🇦🇺', name: 'Australia' },
    { emoji: '🇩🇪', name: 'Germany' },
    { emoji: '🇫🇷', name: 'France' },
    { emoji: '🇯🇵', name: 'Japan' },
    { emoji: '🇰🇷', name: 'South Korea' },
    { emoji: '🇧🇷', name: 'Brazil' },
    { emoji: '🇲🇽', name: 'Mexico' },
    { emoji: '🇪🇸', name: 'Spain' },
    { emoji: '🇮🇹', name: 'Italy' },
    { emoji: '🇷🇺', name: 'Russia' },
    { emoji: '🇨🇳', name: 'China' },
    { emoji: '🇦🇪', name: 'UAE' },
    { emoji: '🇸🇦', name: 'Saudi Arabia' },
    { emoji: '🇿🇦', name: 'South Africa' },
    { emoji: '🇳🇬', name: 'Nigeria' },
    { emoji: '🇪🇬', name: 'Egypt' },
    { emoji: '🇸🇬', name: 'Singapore' },
    { emoji: '🇹🇭', name: 'Thailand' },
    { emoji: '🇵🇭', name: 'Philippines' },
    { emoji: '🇻🇳', name: 'Vietnam' },
    { emoji: '🇮🇩', name: 'Indonesia' },
    { emoji: '🇲🇾', name: 'Malaysia' },
    { emoji: '🇵🇰', name: 'Pakistan' },
    { emoji: '🇧🇩', name: 'Bangladesh' },
    { emoji: '🇱🇰', name: 'Sri Lanka' },
    { emoji: '🇳🇵', name: 'Nepal' }
];

const EmojiPicker = ({ onSelect, onClose }) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredFlags = COMMON_FLAGS.filter(flag =>
        flag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        flag.emoji.includes(searchTerm)
    );

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-2xl border border-gray-700 max-w-lg w-full max-h-[80vh] overflow-hidden flex flex-col">
                <div className="p-4 border-b border-gray-700 flex items-center justify-between">
                    <h3 className="text-white font-semibold text-lg">Select Country Flag</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="p-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            placeholder="Search country..."
                            className="w-full bg-gray-700 border-none rounded-xl p-3 pl-10 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white placeholder:text-gray-500"
                            autoFocus
                        />
                    </div>
                </div>

                <div className="overflow-y-auto p-4 grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {filteredFlags.map(flag => (
                        <button
                            key={flag.emoji}
                            onClick={() => {
                                onSelect({ emoji: flag.emoji, name: flag.name });
                                onClose();
                            }}
                            className="bg-gray-700/50 hover:bg-gray-700 p-3 rounded-lg transition-colors flex flex-col items-center gap-2 group"
                        >
                            <span className="text-3xl">{flag.emoji}</span>
                            <span className="text-gray-300 text-sm text-center group-hover:text-white transition-colors">
                                {flag.name}
                            </span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

const Countries = () => {
    const [countries, setCountries] = useState([]);
    const [newCountry, setNewCountry] = useState({ name: '', emoji: '', price: '', price_usd: '' });
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [editPrice, setEditPrice] = useState('');
    const [editPriceUsd, setEditPriceUsd] = useState('');

    useEffect(() => {
        fetchCountries();
    }, []);

    const fetchCountries = async () => {
        const res = await axios.get(`${API_BASE}/admin/countries`);
        setCountries(res.data);
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        await axios.post(`${API_BASE}/admin/countries`, {
            ...newCountry,
            price: parseFloat(newCountry.price) || 0,
            price_usd: parseFloat(newCountry.price_usd) || 0
        });
        setNewCountry({ name: '', emoji: '', price: '', price_usd: '' });
        fetchCountries();
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this country?')) {
            await axios.delete(`${API_BASE}/admin/countries/${id}`);
            fetchCountries();
        }
    };

    const handleUpdatePrice = async (id) => {
        try {
            await axios.put(`${API_BASE}/admin/countries/${id}`, {
                update_data: {
                    price: parseFloat(editPrice) || 0,
                    price_usd: parseFloat(editPriceUsd) || 0
                }
            });
            setEditingId(null);
            fetchCountries();
        } catch (error) {
            console.error('Error updating price:', error);
            alert('Failed to update price');
        }
    };

    const handleEmojiSelect = ({ emoji, name }) => {
        setNewCountry(prev => ({ ...prev, emoji, name }));
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
            <h2 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                Country Management
            </h2>

            {/* Add Country Form */}
            <form onSubmit={handleAdd} className="bg-gray-800 p-4 md:p-6 rounded-2xl border border-gray-700 shadow-lg space-y-4">
                <h3 className="text-lg font-semibold text-white mb-2">Add New Country</h3>
                <p className="text-sm text-gray-400 mb-4">
                    💡 Tip: Click the flag button to browse emojis, or paste an emoji directly into the small box
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-gray-400 mb-1 text-sm font-medium">Country Flag & Emoji</label>
                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={() => setShowEmojiPicker(true)}
                                className="flex-1 bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 hover:ring-blue-500 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white text-left flex items-center justify-center gap-2 min-h-[50px]"
                            >
                                {newCountry.emoji ? (
                                    <span className="text-4xl">{newCountry.emoji}</span>
                                ) : (
                                    <span className="text-gray-400">Select Flag...</span>
                                )}
                            </button>
                            <input
                                type="text"
                                value={newCountry.emoji}
                                onChange={e => setNewCountry({ ...newCountry, emoji: e.target.value })}
                                className="w-20 bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white text-center text-2xl"
                                placeholder="🏴"
                                maxLength="4"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-gray-400 mb-1 text-sm font-medium">Country Name</label>
                        <input
                            type="text"
                            value={newCountry.name}
                            onChange={e => setNewCountry({ ...newCountry, name: e.target.value })}
                            className="w-full bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white"
                            placeholder="e.g., India"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-gray-400 mb-1 text-sm font-medium">Price (₹ INR)</label>
                        <input
                            type="number"
                            step="0.01"
                            value={newCountry.price}
                            onChange={e => setNewCountry({ ...newCountry, price: e.target.value })}
                            className="w-full bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white"
                            placeholder="e.g., 99.00"
                        />
                    </div>
                    <div>
                        <label className="block text-gray-400 mb-1 text-sm font-medium">Price ($ USD)</label>
                        <input
                            type="number"
                            step="0.01"
                            value={newCountry.price_usd}
                            onChange={e => setNewCountry({ ...newCountry, price_usd: e.target.value })}
                            className="w-full bg-gray-700 border-none rounded-xl p-3 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none transition-all text-white"
                            placeholder="e.g., 1.20"
                        />
                    </div>
                </div>
                <button
                    type="submit"
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors"
                >
                    Add Country
                </button>
            </form>

            {/* Countries List */}
            <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">All Countries ({countries.length})</h3>
                <div className="space-y-2">
                    {countries.length === 0 ? (
                        <p className="text-gray-400 text-center py-8">No countries added yet</p>
                    ) : (
                        countries.map(country => (
                            <div key={country.id} className="bg-gray-700/50 p-4 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="text-3xl">{country.emoji}</span>
                                    <div>
                                        <p className="text-white font-medium">{country.name}</p>
                                        {editingId === country.id ? (
                                            <div className="flex flex-col gap-2 mt-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-gray-500 text-xs">INR:</span>
                                                    <input
                                                        type="number"
                                                        step="0.01"
                                                        value={editPrice}
                                                        onChange={e => setEditPrice(e.target.value)}
                                                        className="w-24 bg-gray-600 border-none rounded-lg px-2 py-1 text-white text-sm ring-1 ring-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
                                                        placeholder="INR"
                                                    />
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-gray-500 text-xs">USD:</span>
                                                    <input
                                                        type="number"
                                                        step="0.01"
                                                        value={editPriceUsd}
                                                        onChange={e => setEditPriceUsd(e.target.value)}
                                                        className="w-24 bg-gray-600 border-none rounded-lg px-2 py-1 text-white text-sm ring-1 ring-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
                                                        placeholder="USD"
                                                    />
                                                </div>
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleUpdatePrice(country.id)}
                                                        className="text-green-500 hover:text-green-400 text-sm font-medium"
                                                    >
                                                        Save
                                                    </button>
                                                    <button
                                                        onClick={() => setEditingId(null)}
                                                        className="text-gray-400 hover:text-white text-sm font-medium"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <p className="text-gray-400 text-sm">
                                                ₹{country.price} / ${country.price_usd}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    {editingId !== country.id && (
                                        <button
                                            onClick={() => {
                                                setEditingId(country.id);
                                                setEditPrice(country.price);
                                                setEditPriceUsd(country.price_usd);
                                            }}
                                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                                        >
                                            Edit
                                        </button>
                                    )}
                                    <button
                                        onClick={() => handleDelete(country.id)}
                                        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {showEmojiPicker && (
                <EmojiPicker
                    onSelect={handleEmojiSelect}
                    onClose={() => setShowEmojiPicker(false)}
                />
            )}
        </div>
    );
};

export default Countries;
