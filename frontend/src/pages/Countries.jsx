import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, X, Plus } from 'lucide-react';
import { API_BASE } from '../api_config';

// Complete list of all world countries with flag emojis
const ALL_WORLD_COUNTRIES = [
    { emoji: '🇦🇫', name: 'Afghanistan' },
    { emoji: '🇦🇱', name: 'Albania' },
    { emoji: '🇩🇿', name: 'Algeria' },
    { emoji: '🇦🇩', name: 'Andorra' },
    { emoji: '🇦🇴', name: 'Angola' },
    { emoji: '🇦🇬', name: 'Antigua and Barbuda' },
    { emoji: '🇦🇷', name: 'Argentina' },
    { emoji: '🇦🇲', name: 'Armenia' },
    { emoji: '🇦🇺', name: 'Australia' },
    { emoji: '🇦🇹', name: 'Austria' },
    { emoji: '🇦🇿', name: 'Azerbaijan' },
    { emoji: '🇧🇸', name: 'Bahamas' },
    { emoji: '🇧🇭', name: 'Bahrain' },
    { emoji: '🇧🇩', name: 'Bangladesh' },
    { emoji: '🇧🇧', name: 'Barbados' },
    { emoji: '🇧🇾', name: 'Belarus' },
    { emoji: '🇧🇪', name: 'Belgium' },
    { emoji: '🇧🇿', name: 'Belize' },
    { emoji: '🇧🇯', name: 'Benin' },
    { emoji: '🇧🇹', name: 'Bhutan' },
    { emoji: '🇧🇴', name: 'Bolivia' },
    { emoji: '🇧🇦', name: 'Bosnia and Herzegovina' },
    { emoji: '🇧🇼', name: 'Botswana' },
    { emoji: '🇧🇷', name: 'Brazil' },
    { emoji: '🇧🇳', name: 'Brunei' },
    { emoji: '🇧🇬', name: 'Bulgaria' },
    { emoji: '🇧🇫', name: 'Burkina Faso' },
    { emoji: '🇧🇮', name: 'Burundi' },
    { emoji: '🇨🇻', name: 'Cabo Verde' },
    { emoji: '🇰🇭', name: 'Cambodia' },
    { emoji: '🇨🇲', name: 'Cameroon' },
    { emoji: '🇨🇦', name: 'Canada' },
    { emoji: '🇨🇫', name: 'Central African Republic' },
    { emoji: '🇹🇩', name: 'Chad' },
    { emoji: '🇨🇱', name: 'Chile' },
    { emoji: '🇨🇳', name: 'China' },
    { emoji: '🇨🇴', name: 'Colombia' },
    { emoji: '🇰🇲', name: 'Comoros' },
    { emoji: '🇨🇬', name: 'Congo' },
    { emoji: '🇨🇩', name: 'Congo (DRC)' },
    { emoji: '🇨🇷', name: 'Costa Rica' },
    { emoji: '🇨🇮', name: 'Côte d\'Ivoire' },
    { emoji: '🇭🇷', name: 'Croatia' },
    { emoji: '🇨🇺', name: 'Cuba' },
    { emoji: '🇨🇾', name: 'Cyprus' },
    { emoji: '🇨🇿', name: 'Czech Republic' },
    { emoji: '🇩🇰', name: 'Denmark' },
    { emoji: '🇩🇯', name: 'Djibouti' },
    { emoji: '🇩🇲', name: 'Dominica' },
    { emoji: '🇩🇴', name: 'Dominican Republic' },
    { emoji: '🇪🇨', name: 'Ecuador' },
    { emoji: '🇪🇬', name: 'Egypt' },
    { emoji: '🇸🇻', name: 'El Salvador' },
    { emoji: '🇬🇶', name: 'Equatorial Guinea' },
    { emoji: '🇪🇷', name: 'Eritrea' },
    { emoji: '🇪🇪', name: 'Estonia' },
    { emoji: '🇸🇿', name: 'Eswatini' },
    { emoji: '🇪🇹', name: 'Ethiopia' },
    { emoji: '🇫🇯', name: 'Fiji' },
    { emoji: '🇫🇮', name: 'Finland' },
    { emoji: '🇫🇷', name: 'France' },
    { emoji: '🇬🇦', name: 'Gabon' },
    { emoji: '🇬🇲', name: 'Gambia' },
    { emoji: '🇬🇪', name: 'Georgia' },
    { emoji: '🇩🇪', name: 'Germany' },
    { emoji: '🇬🇭', name: 'Ghana' },
    { emoji: '🇬🇷', name: 'Greece' },
    { emoji: '🇬🇩', name: 'Grenada' },
    { emoji: '🇬🇹', name: 'Guatemala' },
    { emoji: '🇬🇳', name: 'Guinea' },
    { emoji: '🇬🇼', name: 'Guinea-Bissau' },
    { emoji: '🇬🇾', name: 'Guyana' },
    { emoji: '🇭🇹', name: 'Haiti' },
    { emoji: '🇭🇳', name: 'Honduras' },
    { emoji: '🇭🇺', name: 'Hungary' },
    { emoji: '🇮🇸', name: 'Iceland' },
    { emoji: '🇮🇳', name: 'India' },
    { emoji: '🇮🇩', name: 'Indonesia' },
    { emoji: '🇮🇷', name: 'Iran' },
    { emoji: '🇮🇶', name: 'Iraq' },
    { emoji: '🇮🇪', name: 'Ireland' },
    { emoji: '🇮🇱', name: 'Israel' },
    { emoji: '🇮🇹', name: 'Italy' },
    { emoji: '🇯🇲', name: 'Jamaica' },
    { emoji: '🇯🇵', name: 'Japan' },
    { emoji: '🇯🇴', name: 'Jordan' },
    { emoji: '🇰🇿', name: 'Kazakhstan' },
    { emoji: '🇰🇪', name: 'Kenya' },
    { emoji: '🇰🇮', name: 'Kiribati' },
    { emoji: '🇰🇼', name: 'Kuwait' },
    { emoji: '🇰🇬', name: 'Kyrgyzstan' },
    { emoji: '🇱🇦', name: 'Laos' },
    { emoji: '🇱🇻', name: 'Latvia' },
    { emoji: '🇱🇧', name: 'Lebanon' },
    { emoji: '🇱🇸', name: 'Lesotho' },
    { emoji: '🇱🇷', name: 'Liberia' },
    { emoji: '🇱🇾', name: 'Libya' },
    { emoji: '🇱🇮', name: 'Liechtenstein' },
    { emoji: '🇱🇹', name: 'Lithuania' },
    { emoji: '🇱🇺', name: 'Luxembourg' },
    { emoji: '🇲🇬', name: 'Madagascar' },
    { emoji: '🇲🇼', name: 'Malawi' },
    { emoji: '🇲🇾', name: 'Malaysia' },
    { emoji: '🇲🇻', name: 'Maldives' },
    { emoji: '🇲🇱', name: 'Mali' },
    { emoji: '🇲🇹', name: 'Malta' },
    { emoji: '🇲🇭', name: 'Marshall Islands' },
    { emoji: '🇲🇷', name: 'Mauritania' },
    { emoji: '🇲🇺', name: 'Mauritius' },
    { emoji: '🇲🇽', name: 'Mexico' },
    { emoji: '🇫🇲', name: 'Micronesia' },
    { emoji: '🇲🇩', name: 'Moldova' },
    { emoji: '🇲🇨', name: 'Monaco' },
    { emoji: '🇲🇳', name: 'Mongolia' },
    { emoji: '🇲🇪', name: 'Montenegro' },
    { emoji: '🇲🇦', name: 'Morocco' },
    { emoji: '🇲🇿', name: 'Mozambique' },
    { emoji: '🇲🇲', name: 'Myanmar (Burma)' },
    { emoji: '🇳🇦', name: 'Namibia' },
    { emoji: '🇳🇷', name: 'Nauru' },
    { emoji: '🇳🇵', name: 'Nepal' },
    { emoji: '🇳🇱', name: 'Netherlands' },
    { emoji: '🇳🇿', name: 'New Zealand' },
    { emoji: '🇳🇮', name: 'Nicaragua' },
    { emoji: '🇳🇪', name: 'Niger' },
    { emoji: '🇳🇬', name: 'Nigeria' },
    { emoji: '🇰🇵', name: 'North Korea' },
    { emoji: '🇲🇰', name: 'North Macedonia' },
    { emoji: '🇳🇴', name: 'Norway' },
    { emoji: '🇴🇲', name: 'Oman' },
    { emoji: '🇵🇰', name: 'Pakistan' },
    { emoji: '🇵🇼', name: 'Palau' },
    { emoji: '🇵🇦', name: 'Panama' },
    { emoji: '🇵🇬', name: 'Papua New Guinea' },
    { emoji: '🇵🇾', name: 'Paraguay' },
    { emoji: '🇵🇪', name: 'Peru' },
    { emoji: '🇵🇭', name: 'Philippines' },
    { emoji: '🇵🇱', name: 'Poland' },
    { emoji: '🇵🇹', name: 'Portugal' },
    { emoji: '🇶🇦', name: 'Qatar' },
    { emoji: '🇷🇴', name: 'Romania' },
    { emoji: '🇷🇺', name: 'Russia' },
    { emoji: '🇷🇼', name: 'Rwanda' },
    { emoji: '🇰🇳', name: 'Saint Kitts and Nevis' },
    { emoji: '🇱🇨', name: 'Saint Lucia' },
    { emoji: '🇻🇨', name: 'Saint Vincent and the Grenadines' },
    { emoji: '🇼🇸', name: 'Samoa' },
    { emoji: '🇸🇲', name: 'San Marino' },
    { emoji: '🇸🇹', name: 'Sao Tome and Principe' },
    { emoji: '🇸🇦', name: 'Saudi Arabia' },
    { emoji: '🇸🇳', name: 'Senegal' },
    { emoji: '🇷🇸', name: 'Serbia' },
    { emoji: '🇸🇨', name: 'Seychelles' },
    { emoji: '🇸🇱', name: 'Sierra Leone' },
    { emoji: '🇸🇬', name: 'Singapore' },
    { emoji: '🇸🇰', name: 'Slovakia' },
    { emoji: '🇸🇮', name: 'Slovenia' },
    { emoji: '🇸🇧', name: 'Solomon Islands' },
    { emoji: '🇸🇴', name: 'Somalia' },
    { emoji: '🇿🇦', name: 'South Africa' },
    { emoji: '🇰🇷', name: 'South Korea' },
    { emoji: '🇸🇸', name: 'South Sudan' },
    { emoji: '🇪🇸', name: 'Spain' },
    { emoji: '🇱🇰', name: 'Sri Lanka' },
    { emoji: '🇸🇩', name: 'Sudan' },
    { emoji: '🇸🇷', name: 'Suriname' },
    { emoji: '🇸🇪', name: 'Sweden' },
    { emoji: '🇨🇭', name: 'Switzerland' },
    { emoji: '🇸🇾', name: 'Syria' },
    { emoji: '🇹🇼', name: 'Taiwan' },
    { emoji: '🇹🇯', name: 'Tajikistan' },
    { emoji: '🇹🇿', name: 'Tanzania' },
    { emoji: '🇹🇭', name: 'Thailand' },
    { emoji: '🇹🇱', name: 'Timor-Leste' },
    { emoji: '🇹🇬', name: 'Togo' },
    { emoji: '🇹🇴', name: 'Tonga' },
    { emoji: '🇹🇹', name: 'Trinidad and Tobago' },
    { emoji: '🇹🇳', name: 'Tunisia' },
    { emoji: '🇹🇷', name: 'Turkey' },
    { emoji: '🇹🇲', name: 'Turkmenistan' },
    { emoji: '🇹🇻', name: 'Tuvalu' },
    { emoji: '🇺🇬', name: 'Uganda' },
    { emoji: '🇺🇦', name: 'Ukraine' },
    { emoji: '🇦🇪', name: 'UAE' },
    { emoji: '🇬🇧', name: 'United Kingdom' },
    { emoji: '🇺🇸', name: 'United States' },
    { emoji: '🇺🇾', name: 'Uruguay' },
    { emoji: '🇺🇿', name: 'Uzbekistan' },
    { emoji: '🇻🇺', name: 'Vanuatu' },
    { emoji: '🇻🇦', name: 'Vatican City' },
    { emoji: '🇻🇪', name: 'Venezuela' },
    { emoji: '🇻🇳', name: 'Vietnam' },
    { emoji: '🇾🇪', name: 'Yemen' },
    { emoji: '🇿🇲', name: 'Zambia' },
    { emoji: '🇿🇼', name: 'Zimbabwe' },
];

const Countries = () => {
    const [countries, setCountries] = useState([]);
    const [search, setSearch] = useState('');
    const [showSearch, setShowSearch] = useState(false);
    const [selected, setSelected] = useState(null); // { emoji, name }
    const [price, setPrice] = useState('');
    const [priceUsd, setPriceUsd] = useState('');
    const [adding, setAdding] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [editPrice, setEditPrice] = useState('');
    const [editPriceUsd, setEditPriceUsd] = useState('');

    useEffect(() => { fetchCountries(); }, []);

    const fetchCountries = async () => {
        const res = await axios.get(`${API_BASE}/admin/countries`);
        setCountries(res.data);
    };

    // Countries from the world list that are NOT yet in DB
    const addedNames = new Set(countries.map(c => c.name.toLowerCase()));
    const filteredWorld = ALL_WORLD_COUNTRIES.filter(c =>
        !addedNames.has(c.name.toLowerCase()) &&
        c.name.toLowerCase().includes(search.toLowerCase())
    );

    const handleSelectCountry = (country) => {
        setSelected(country);
        setSearch('');
        setShowSearch(false);
    };

    const handleAdd = async (e) => {
        e.preventDefault();
        if (!selected) return;
        setAdding(true);
        try {
            await axios.post(`${API_BASE}/admin/countries`, {
                name: selected.name,
                emoji: selected.emoji,
                price: parseFloat(price) || 0,
                price_usd: parseFloat(priceUsd) || 0,
            });
            setSelected(null);
            setPrice('');
            setPriceUsd('');
            fetchCountries();
        } finally {
            setAdding(false);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('Delete this country?')) {
            await axios.delete(`${API_BASE}/admin/countries/${id}`);
            fetchCountries();
        }
    };

    const handleUpdatePrice = async (id) => {
        await axios.put(`${API_BASE}/admin/countries/${id}`, {
            update_data: {
                price: parseFloat(editPrice) || 0,
                price_usd: parseFloat(editPriceUsd) || 0,
            }
        });
        setEditingId(null);
        fetchCountries();
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
            <h2 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                🌍 Country Management
            </h2>

            {/* Search & Add Country */}
            <div className="bg-gray-800 p-4 md:p-6 rounded-2xl border border-gray-700 shadow-lg space-y-4">
                <h3 className="text-lg font-semibold text-white">Add Country</h3>

                {/* Country search box */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={search}
                        onChange={e => { setSearch(e.target.value); setShowSearch(true); setSelected(null); }}
                        onFocus={() => setShowSearch(true)}
                        placeholder="Search country (e.g. Argentina, Japan...)"
                        className="w-full bg-gray-700 border-none rounded-xl p-3 pl-10 ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none text-white placeholder:text-gray-500"
                    />
                    {search && (
                        <button onClick={() => { setSearch(''); setShowSearch(false); setSelected(null); }}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Dropdown results */}
                {showSearch && search && (
                    <div className="bg-gray-900 rounded-xl border border-gray-700 max-h-48 overflow-y-auto">
                        {filteredWorld.length === 0 ? (
                            <p className="text-gray-400 text-center py-4 text-sm">
                                {addedNames.has(search.toLowerCase()) ? '✅ Already added' : 'No matching countries'}
                            </p>
                        ) : (
                            filteredWorld.slice(0, 20).map(c => (
                                <button key={c.name} onClick={() => handleSelectCountry(c)}
                                    className="w-full flex items-center gap-3 p-3 hover:bg-gray-700 text-left transition-colors">
                                    <span className="text-2xl">{c.emoji}</span>
                                    <span className="text-white">{c.name}</span>
                                </button>
                            ))
                        )}
                    </div>
                )}

                {/* Selected country + price form */}
                {selected && (
                    <form onSubmit={handleAdd} className="bg-gray-700/50 rounded-xl p-4 space-y-3 border border-gray-600">
                        <div className="flex items-center gap-3">
                            <span className="text-4xl">{selected.emoji}</span>
                            <span className="text-white text-xl font-semibold">{selected.name}</span>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-gray-400 text-xs font-medium mb-1 block">Price (₹ INR)</label>
                                <input type="number" step="0.01" value={price} onChange={e => setPrice(e.target.value)}
                                    className="w-full bg-gray-700 rounded-lg p-2 text-white ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="e.g. 99.00" required />
                            </div>
                            <div>
                                <label className="text-gray-400 text-xs font-medium mb-1 block">Price ($ USD)</label>
                                <input type="number" step="0.01" value={priceUsd} onChange={e => setPriceUsd(e.target.value)}
                                    className="w-full bg-gray-700 rounded-lg p-2 text-white ring-1 ring-gray-600 focus:ring-2 focus:ring-blue-500 outline-none"
                                    placeholder="e.g. 1.20" />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button type="submit" disabled={adding}
                                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-2">
                                <Plus className="w-4 h-4" />
                                {adding ? 'Adding...' : 'Add Country'}
                            </button>
                            <button type="button" onClick={() => setSelected(null)}
                                className="px-4 bg-gray-600 hover:bg-gray-500 text-white py-2 rounded-lg transition-colors">
                                Cancel
                            </button>
                        </div>
                    </form>
                )}
            </div>

            {/* Countries List */}
            <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">
                    Active Countries ({countries.length})
                </h3>
                <div className="space-y-2">
                    {countries.length === 0 ? (
                        <p className="text-gray-400 text-center py-8">No countries added yet. Search above to add one!</p>
                    ) : (
                        countries.map(country => (
                            <div key={country.id} className="bg-gray-700/50 p-4 rounded-lg hover:bg-gray-700 transition-colors flex items-center justify-between">
                                <div className="flex items-center gap-3 flex-1">
                                    <span className="text-3xl">{country.emoji}</span>
                                    <div className="flex-1">
                                        <p className="text-white font-medium">{country.name}</p>
                                        {editingId === country.id ? (
                                            <div className="flex flex-wrap gap-2 mt-2">
                                                <input type="number" step="0.01" value={editPrice}
                                                    onChange={e => setEditPrice(e.target.value)}
                                                    className="w-24 bg-gray-600 rounded-lg px-2 py-1 text-white text-sm ring-1 ring-gray-500 outline-none"
                                                    placeholder="₹ INR" />
                                                <input type="number" step="0.01" value={editPriceUsd}
                                                    onChange={e => setEditPriceUsd(e.target.value)}
                                                    className="w-24 bg-gray-600 rounded-lg px-2 py-1 text-white text-sm ring-1 ring-gray-500 outline-none"
                                                    placeholder="$ USD" />
                                                <button onClick={() => handleUpdatePrice(country.id)}
                                                    className="text-green-400 hover:text-green-300 text-sm font-medium">Save</button>
                                                <button onClick={() => setEditingId(null)}
                                                    className="text-gray-400 hover:text-white text-sm">Cancel</button>
                                            </div>
                                        ) : (
                                            <p className="text-gray-400 text-sm">₹{country.price} / ${country.price_usd}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex gap-2 ml-2">
                                    {editingId !== country.id && (
                                        <button onClick={() => { setEditingId(country.id); setEditPrice(country.price); setEditPriceUsd(country.price_usd); }}
                                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
                                            Edit
                                        </button>
                                    )}
                                    <button onClick={() => handleDelete(country.id)}
                                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors">
                                        Del
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Countries;
