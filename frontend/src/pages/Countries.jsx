import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, X, Plus } from 'lucide-react';
import { API_BASE } from '../api_config';

// Complete list of all world countries with flag emojis and dial codes
const ALL_WORLD_COUNTRIES = [
    { emoji: '🇦🇫', name: 'Afghanistan', dial: '+93' },
    { emoji: '🇦🇱', name: 'Albania', dial: '+355' },
    { emoji: '🇩🇿', name: 'Algeria', dial: '+213' },
    { emoji: '🇦🇩', name: 'Andorra', dial: '+376' },
    { emoji: '🇦🇴', name: 'Angola', dial: '+244' },
    { emoji: '🇦🇬', name: 'Antigua and Barbuda', dial: '+1268' },
    { emoji: '🇦🇷', name: 'Argentina', dial: '+54' },
    { emoji: '🇦🇲', name: 'Armenia', dial: '+374' },
    { emoji: '🇦🇺', name: 'Australia', dial: '+61' },
    { emoji: '🇦🇹', name: 'Austria', dial: '+43' },
    { emoji: '🇦🇿', name: 'Azerbaijan', dial: '+994' },
    { emoji: '🇧🇸', name: 'Bahamas', dial: '+1242' },
    { emoji: '🇧🇭', name: 'Bahrain', dial: '+973' },
    { emoji: '🇧🇩', name: 'Bangladesh', dial: '+880' },
    { emoji: '🇧🇧', name: 'Barbados', dial: '+1246' },
    { emoji: '🇧🇾', name: 'Belarus', dial: '+375' },
    { emoji: '🇧🇪', name: 'Belgium', dial: '+32' },
    { emoji: '🇧🇿', name: 'Belize', dial: '+501' },
    { emoji: '🇧🇯', name: 'Benin', dial: '+229' },
    { emoji: '🇧🇹', name: 'Bhutan', dial: '+975' },
    { emoji: '🇧🇴', name: 'Bolivia', dial: '+591' },
    { emoji: '🇧🇦', name: 'Bosnia and Herzegovina', dial: '+387' },
    { emoji: '🇧🇼', name: 'Botswana', dial: '+267' },
    { emoji: '🇧🇷', name: 'Brazil', dial: '+55' },
    { emoji: '🇧🇳', name: 'Brunei', dial: '+673' },
    { emoji: '🇧🇬', name: 'Bulgaria', dial: '+359' },
    { emoji: '🇧🇫', name: 'Burkina Faso', dial: '+226' },
    { emoji: '🇧🇮', name: 'Burundi', dial: '+257' },
    { emoji: '🇨🇻', name: 'Cabo Verde', dial: '+238' },
    { emoji: '🇰🇭', name: 'Cambodia', dial: '+855' },
    { emoji: '🇨🇲', name: 'Cameroon', dial: '+237' },
    { emoji: '🇨🇦', name: 'Canada', dial: '+1' },
    { emoji: '🇨🇫', name: 'Central African Republic', dial: '+236' },
    { emoji: '🇹🇩', name: 'Chad', dial: '+235' },
    { emoji: '🇨🇱', name: 'Chile', dial: '+56' },
    { emoji: '🇨🇳', name: 'China', dial: '+86' },
    { emoji: '🇨🇴', name: 'Colombia', dial: '+57' },
    { emoji: '🇰🇲', name: 'Comoros', dial: '+269' },
    { emoji: '🇨🇬', name: 'Congo', dial: '+242' },
    { emoji: '🇨🇩', name: 'Congo (DRC)', dial: '+243' },
    { emoji: '🇨🇷', name: 'Costa Rica', dial: '+506' },
    { emoji: '🇨🇮', name: "Côte d'Ivoire", dial: '+225' },
    { emoji: '🇭🇷', name: 'Croatia', dial: '+385' },
    { emoji: '🇨🇺', name: 'Cuba', dial: '+53' },
    { emoji: '🇨🇾', name: 'Cyprus', dial: '+357' },
    { emoji: '🇨🇿', name: 'Czech Republic', dial: '+420' },
    { emoji: '🇩🇰', name: 'Denmark', dial: '+45' },
    { emoji: '🇩🇯', name: 'Djibouti', dial: '+253' },
    { emoji: '🇩🇲', name: 'Dominica', dial: '+1767' },
    { emoji: '🇩🇴', name: 'Dominican Republic', dial: '+1809' },
    { emoji: '🇪🇨', name: 'Ecuador', dial: '+593' },
    { emoji: '🇪🇬', name: 'Egypt', dial: '+20' },
    { emoji: '🇸🇻', name: 'El Salvador', dial: '+503' },
    { emoji: '🇬🇶', name: 'Equatorial Guinea', dial: '+240' },
    { emoji: '🇪🇷', name: 'Eritrea', dial: '+291' },
    { emoji: '🇪🇪', name: 'Estonia', dial: '+372' },
    { emoji: '🇸🇿', name: 'Eswatini', dial: '+268' },
    { emoji: '🇪🇹', name: 'Ethiopia', dial: '+251' },
    { emoji: '🇫🇯', name: 'Fiji', dial: '+679' },
    { emoji: '🇫🇮', name: 'Finland', dial: '+358' },
    { emoji: '🇫🇷', name: 'France', dial: '+33' },
    { emoji: '🇬🇦', name: 'Gabon', dial: '+241' },
    { emoji: '🇬🇲', name: 'Gambia', dial: '+220' },
    { emoji: '🇬🇪', name: 'Georgia', dial: '+995' },
    { emoji: '🇩🇪', name: 'Germany', dial: '+49' },
    { emoji: '🇬🇭', name: 'Ghana', dial: '+233' },
    { emoji: '🇬🇷', name: 'Greece', dial: '+30' },
    { emoji: '🇬🇩', name: 'Grenada', dial: '+1473' },
    { emoji: '🇬🇹', name: 'Guatemala', dial: '+502' },
    { emoji: '🇬🇳', name: 'Guinea', dial: '+224' },
    { emoji: '🇬🇼', name: 'Guinea-Bissau', dial: '+245' },
    { emoji: '🇬🇾', name: 'Guyana', dial: '+592' },
    { emoji: '🇭🇹', name: 'Haiti', dial: '+509' },
    { emoji: '🇭🇳', name: 'Honduras', dial: '+504' },
    { emoji: '🇭🇺', name: 'Hungary', dial: '+36' },
    { emoji: '🇮🇸', name: 'Iceland', dial: '+354' },
    { emoji: '🇮🇳', name: 'India', dial: '+91' },
    { emoji: '🇮🇩', name: 'Indonesia', dial: '+62' },
    { emoji: '🇮🇷', name: 'Iran', dial: '+98' },
    { emoji: '🇮🇶', name: 'Iraq', dial: '+964' },
    { emoji: '🇮🇪', name: 'Ireland', dial: '+353' },
    { emoji: '🇮🇱', name: 'Israel', dial: '+972' },
    { emoji: '🇮🇹', name: 'Italy', dial: '+39' },
    { emoji: '🇯🇲', name: 'Jamaica', dial: '+1876' },
    { emoji: '🇯🇵', name: 'Japan', dial: '+81' },
    { emoji: '🇯🇴', name: 'Jordan', dial: '+962' },
    { emoji: '🇰🇿', name: 'Kazakhstan', dial: '+7' },
    { emoji: '🇰🇪', name: 'Kenya', dial: '+254' },
    { emoji: '🇰🇮', name: 'Kiribati', dial: '+686' },
    { emoji: '🇰🇼', name: 'Kuwait', dial: '+965' },
    { emoji: '🇰🇬', name: 'Kyrgyzstan', dial: '+996' },
    { emoji: '🇱🇦', name: 'Laos', dial: '+856' },
    { emoji: '🇱🇻', name: 'Latvia', dial: '+371' },
    { emoji: '🇱🇧', name: 'Lebanon', dial: '+961' },
    { emoji: '🇱🇸', name: 'Lesotho', dial: '+266' },
    { emoji: '🇱🇷', name: 'Liberia', dial: '+231' },
    { emoji: '🇱🇾', name: 'Libya', dial: '+218' },
    { emoji: '🇱🇮', name: 'Liechtenstein', dial: '+423' },
    { emoji: '🇱🇹', name: 'Lithuania', dial: '+370' },
    { emoji: '🇱🇺', name: 'Luxembourg', dial: '+352' },
    { emoji: '🇲🇬', name: 'Madagascar', dial: '+261' },
    { emoji: '🇲🇼', name: 'Malawi', dial: '+265' },
    { emoji: '🇲🇾', name: 'Malaysia', dial: '+60' },
    { emoji: '🇲🇻', name: 'Maldives', dial: '+960' },
    { emoji: '🇲🇱', name: 'Mali', dial: '+223' },
    { emoji: '🇲🇹', name: 'Malta', dial: '+356' },
    { emoji: '🇲🇭', name: 'Marshall Islands', dial: '+692' },
    { emoji: '🇲🇷', name: 'Mauritania', dial: '+222' },
    { emoji: '🇲🇺', name: 'Mauritius', dial: '+230' },
    { emoji: '🇲🇽', name: 'Mexico', dial: '+52' },
    { emoji: '🇫🇲', name: 'Micronesia', dial: '+691' },
    { emoji: '🇲🇩', name: 'Moldova', dial: '+373' },
    { emoji: '🇲🇨', name: 'Monaco', dial: '+377' },
    { emoji: '🇲🇳', name: 'Mongolia', dial: '+976' },
    { emoji: '🇲🇪', name: 'Montenegro', dial: '+382' },
    { emoji: '🇲🇦', name: 'Morocco', dial: '+212' },
    { emoji: '🇲🇿', name: 'Mozambique', dial: '+258' },
    { emoji: '🇲🇲', name: 'Myanmar (Burma)', dial: '+95' },
    { emoji: '🇳🇦', name: 'Namibia', dial: '+264' },
    { emoji: '🇳🇷', name: 'Nauru', dial: '+674' },
    { emoji: '🇳🇵', name: 'Nepal', dial: '+977' },
    { emoji: '🇳🇱', name: 'Netherlands', dial: '+31' },
    { emoji: '🇳🇿', name: 'New Zealand', dial: '+64' },
    { emoji: '🇳🇮', name: 'Nicaragua', dial: '+505' },
    { emoji: '🇳🇪', name: 'Niger', dial: '+227' },
    { emoji: '🇳🇬', name: 'Nigeria', dial: '+234' },
    { emoji: '🇰🇵', name: 'North Korea', dial: '+850' },
    { emoji: '🇲🇰', name: 'North Macedonia', dial: '+389' },
    { emoji: '🇳🇴', name: 'Norway', dial: '+47' },
    { emoji: '🇴🇲', name: 'Oman', dial: '+968' },
    { emoji: '🇵🇰', name: 'Pakistan', dial: '+92' },
    { emoji: '🇵🇼', name: 'Palau', dial: '+680' },
    { emoji: '🇵🇦', name: 'Panama', dial: '+507' },
    { emoji: '🇵🇬', name: 'Papua New Guinea', dial: '+675' },
    { emoji: '🇵🇾', name: 'Paraguay', dial: '+595' },
    { emoji: '🇵🇪', name: 'Peru', dial: '+51' },
    { emoji: '🇵🇭', name: 'Philippines', dial: '+63' },
    { emoji: '🇵🇱', name: 'Poland', dial: '+48' },
    { emoji: '🇵🇹', name: 'Portugal', dial: '+351' },
    { emoji: '🇶🇦', name: 'Qatar', dial: '+974' },
    { emoji: '🇷🇴', name: 'Romania', dial: '+40' },
    { emoji: '🇷🇺', name: 'Russia', dial: '+7' },
    { emoji: '🇷🇼', name: 'Rwanda', dial: '+250' },
    { emoji: '🇰🇳', name: 'Saint Kitts and Nevis', dial: '+1869' },
    { emoji: '🇱🇨', name: 'Saint Lucia', dial: '+1758' },
    { emoji: '🇻🇨', name: 'Saint Vincent and the Grenadines', dial: '+1784' },
    { emoji: '🇼🇸', name: 'Samoa', dial: '+685' },
    { emoji: '🇸🇲', name: 'San Marino', dial: '+378' },
    { emoji: '🇸🇹', name: 'Sao Tome and Principe', dial: '+239' },
    { emoji: '🇸🇦', name: 'Saudi Arabia', dial: '+966' },
    { emoji: '🇸🇳', name: 'Senegal', dial: '+221' },
    { emoji: '🇷🇸', name: 'Serbia', dial: '+381' },
    { emoji: '🇸🇨', name: 'Seychelles', dial: '+248' },
    { emoji: '🇸🇱', name: 'Sierra Leone', dial: '+232' },
    { emoji: '🇸🇬', name: 'Singapore', dial: '+65' },
    { emoji: '🇸🇰', name: 'Slovakia', dial: '+421' },
    { emoji: '🇸🇮', name: 'Slovenia', dial: '+386' },
    { emoji: '🇸🇧', name: 'Solomon Islands', dial: '+677' },
    { emoji: '🇸🇴', name: 'Somalia', dial: '+252' },
    { emoji: '🇿🇦', name: 'South Africa', dial: '+27' },
    { emoji: '🇰🇷', name: 'South Korea', dial: '+82' },
    { emoji: '🇸🇸', name: 'South Sudan', dial: '+211' },
    { emoji: '🇪🇸', name: 'Spain', dial: '+34' },
    { emoji: '🇱🇰', name: 'Sri Lanka', dial: '+94' },
    { emoji: '🇸🇩', name: 'Sudan', dial: '+249' },
    { emoji: '🇸🇷', name: 'Suriname', dial: '+597' },
    { emoji: '🇸🇪', name: 'Sweden', dial: '+46' },
    { emoji: '🇨🇭', name: 'Switzerland', dial: '+41' },
    { emoji: '🇸🇾', name: 'Syria', dial: '+963' },
    { emoji: '🇹🇼', name: 'Taiwan', dial: '+886' },
    { emoji: '🇹🇯', name: 'Tajikistan', dial: '+992' },
    { emoji: '🇹🇿', name: 'Tanzania', dial: '+255' },
    { emoji: '🇹🇭', name: 'Thailand', dial: '+66' },
    { emoji: '🇹🇱', name: 'Timor-Leste', dial: '+670' },
    { emoji: '🇹🇬', name: 'Togo', dial: '+228' },
    { emoji: '🇹🇴', name: 'Tonga', dial: '+676' },
    { emoji: '🇹🇹', name: 'Trinidad and Tobago', dial: '+1868' },
    { emoji: '🇹🇳', name: 'Tunisia', dial: '+216' },
    { emoji: '🇹🇷', name: 'Turkey', dial: '+90' },
    { emoji: '🇹🇲', name: 'Turkmenistan', dial: '+993' },
    { emoji: '🇹🇻', name: 'Tuvalu', dial: '+688' },
    { emoji: '🇺🇬', name: 'Uganda', dial: '+256' },
    { emoji: '🇺🇦', name: 'Ukraine', dial: '+380' },
    { emoji: '🇦🇪', name: 'UAE', dial: '+971' },
    { emoji: '🇬🇧', name: 'United Kingdom', dial: '+44' },
    { emoji: '🇺🇸', name: 'United States', dial: '+1' },
    { emoji: '🇺🇾', name: 'Uruguay', dial: '+598' },
    { emoji: '🇺🇿', name: 'Uzbekistan', dial: '+998' },
    { emoji: '🇻🇺', name: 'Vanuatu', dial: '+678' },
    { emoji: '🇻🇦', name: 'Vatican City', dial: '+379' },
    { emoji: '🇻🇪', name: 'Venezuela', dial: '+58' },
    { emoji: '🇻🇳', name: 'Vietnam', dial: '+84' },
    { emoji: '🇾🇪', name: 'Yemen', dial: '+967' },
    { emoji: '🇿🇲', name: 'Zambia', dial: '+260' },
    { emoji: '🇿🇼', name: 'Zimbabwe', dial: '+263' },
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
        (c.name.toLowerCase().includes(search.toLowerCase()) ||
            c.dial.includes(search))
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
                                    <span className="text-white flex-1">{c.name}</span>
                                    <span className="text-gray-400 text-sm font-mono">{c.dial}</span>
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
