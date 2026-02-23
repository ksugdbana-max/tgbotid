import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Filter, CheckCircle, XCircle, Package } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'https://welldecked-deflected-daniella.ngrok-free.dev';

const Stock = () => {
    const [accounts, setAccounts] = useState([]);
    const [countries, setCountries] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterCountry, setFilterCountry] = useState('');
    const [filterStatus, setFilterStatus] = useState('all');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const [accountsRes, countriesRes] = await Promise.all([
            axios.get(`${API_BASE}/admin/accounts`),
            axios.get(`${API_BASE}/admin/countries`)
        ]);
        setAccounts(accountsRes.data);
        setCountries(countriesRes.data);
    };

    const getCountryById = (id) => countries.find(c => c.id === id);

    const filteredAccounts = accounts.filter(acc => {
        const country = getCountryById(acc.country_id);
        const matchesCountry = !filterCountry || acc.country_id === parseInt(filterCountry);
        const matchesStatus = filterStatus === 'all' ||
            (filterStatus === 'available' && acc.is_sold === false) ||
            (filterStatus === 'sold' && acc.is_sold === true);
        const matchesSearch = !searchTerm ||
            acc.phone_number.includes(searchTerm) ||
            country?.name.toLowerCase().includes(searchTerm.toLowerCase());
        return matchesCountry && matchesStatus && matchesSearch;
    });

    const groupedByCountry = filteredAccounts.reduce((acc, account) => {
        const countryId = account.country_id;
        if (!acc[countryId]) acc[countryId] = [];
        acc[countryId].push(account);
        return acc;
    }, {});

    const stats = {
        total: accounts.length,
        available: accounts.filter(a => a.is_sold === false).length,
        sold: accounts.filter(a => a.is_sold === true).length
    };

    return (
        <div className="space-y-4 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h2 className="text-2xl md:text-3xl font-bold text-white flex items-center gap-2">
                        <Package size={28} className="text-blue-400" />
                        Inventory Stock
                    </h2>
                    <p className="text-gray-400 text-sm mt-1">
                        {stats.total} total • {stats.available} available • {stats.sold} sold
                    </p>
                </div>
            </div>

            {/* Compact Filters Row */}
            <div className="bg-gray-800/50 p-3 rounded-xl border border-gray-700/50 backdrop-blur-sm">
                <div className="flex items-center gap-2 flex-wrap">
                    {/* Search */}
                    <div className="flex-1 min-w-[200px] relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            placeholder="Search phone or country..."
                            className="w-full bg-gray-700/50 border-none rounded-lg py-2 pl-9 pr-3 text-sm ring-1 ring-gray-600/50 focus:ring-2 focus:ring-blue-500/50 outline-none transition-all text-white placeholder:text-gray-500"
                        />
                    </div>

                    {/* Country Filter */}
                    <div className="relative">
                        <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                        <select
                            value={filterCountry}
                            onChange={e => setFilterCountry(e.target.value)}
                            className="bg-gray-700/50 border-none rounded-lg py-2 pl-9 pr-8 text-sm ring-1 ring-gray-600/50 focus:ring-2 focus:ring-blue-500/50 outline-none transition-all text-white appearance-none cursor-pointer"
                        >
                            <option value="">All Countries</option>
                            {countries.map(c => <option key={c.id} value={c.id}>{c.emoji} {c.name}</option>)}
                        </select>
                    </div>

                    {/* Status Icons */}
                    <div className="flex items-center gap-1 bg-gray-700/30 rounded-lg p-1">
                        <button
                            onClick={() => setFilterStatus('all')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${filterStatus === 'all'
                                ? 'bg-blue-600 text-white'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                                }`}
                            title="All"
                        >
                            <Package size={14} />
                            All
                        </button>
                        <button
                            onClick={() => setFilterStatus('available')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${filterStatus === 'available'
                                ? 'bg-green-600 text-white'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                                }`}
                            title="Available"
                        >
                            <CheckCircle size={14} />
                            Available
                        </button>
                        <button
                            onClick={() => setFilterStatus('sold')}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${filterStatus === 'sold'
                                ? 'bg-red-600 text-white'
                                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                                }`}
                            title="Sold"
                        >
                            <XCircle size={14} />
                            Sold
                        </button>
                    </div>
                </div>
            </div>

            {/* Inventory List - Compact Cards */}
            <div className="space-y-3">
                {Object.keys(groupedByCountry).length === 0 ? (
                    <div className="bg-gray-800/30 p-8 rounded-xl border border-gray-700/50 text-center">
                        <Package size={48} className="mx-auto text-gray-600 mb-3" />
                        <p className="text-gray-400">No accounts found</p>
                    </div>
                ) : (
                    Object.entries(groupedByCountry).map(([countryId, countryAccounts]) => {
                        const country = getCountryById(parseInt(countryId));
                        const availableCount = countryAccounts.filter(a => a.is_sold === false).length;
                        const soldCount = countryAccounts.filter(a => a.is_sold === true).length;

                        return (
                            <div key={countryId} className="bg-gray-800/50 rounded-xl border border-gray-700/50 overflow-hidden backdrop-blur-sm">
                                {/* Country Header - Compact */}
                                <div className="bg-gray-700/30 px-4 py-2.5 flex items-center justify-between border-b border-gray-700/50">
                                    <div className="flex items-center gap-2">
                                        <span className="text-2xl">{country?.emoji}</span>
                                        <span className="font-semibold text-white text-sm">{country?.name}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-xs">
                                        <span className="text-green-400 flex items-center gap-1">
                                            <CheckCircle size={14} />
                                            {availableCount}
                                        </span>
                                        <span className="text-red-400 flex items-center gap-1">
                                            <XCircle size={14} />
                                            {soldCount}
                                        </span>
                                    </div>
                                </div>

                                {/* Accounts Grid - Compact */}
                                <div className="p-3 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                    {countryAccounts.map(acc => (
                                        <div
                                            key={acc.id}
                                            className="bg-gray-700/30 hover:bg-gray-700/50 p-2.5 rounded-lg transition-all border border-gray-600/30"
                                        >
                                            <div className="flex items-center justify-between gap-2">
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-white font-mono text-sm font-medium truncate">
                                                        {acc.phone_number}
                                                    </p>
                                                    {acc.twofa_password && (
                                                        <p className="text-blue-400 text-xs font-mono mt-0.5 truncate" title={acc.twofa_password}>
                                                            🔐 {acc.twofa_password}
                                                        </p>
                                                    )}
                                                </div>
                                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold whitespace-nowrap ${acc.is_sold === false
                                                    ? 'bg-green-600/20 text-green-400 ring-1 ring-green-600/30'
                                                    : 'bg-red-600/20 text-red-400 ring-1 ring-red-600/30'
                                                    }`}>
                                                    {acc.is_sold === false ? 'Available' : 'Sold'}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};

export default Stock;
