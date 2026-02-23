import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Countries from './pages/Countries';
import Accounts from './pages/Accounts';
import Stock from './pages/Stock';
import Deposits from './pages/Deposits';
import DepositDetail from './pages/DepositDetail';
import UserDetails from './pages/UserDetails';
import PaymentSettings from './pages/PaymentSettings';
import { LayoutDashboard, Users as UsersIcon, Globe, CreditCard, LogOut, Package, Settings } from 'lucide-react';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('admin_token'));

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <Router>
      <div className="flex flex-col h-screen bg-gray-900 text-white font-sans overflow-hidden">
        {/* Sidebar - Desktop Only */}
        <aside className="hidden md:flex w-64 bg-gray-800 p-6 flex-col shadow-xl">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-10">
            Admin Panel
          </h1>
          <nav className="flex-1 space-y-4">
            <NavItem to="/" icon={<LayoutDashboard size={20} />} label="Dashboard" />
            <NavItem to="/countries" icon={<Globe size={20} />} label="Countries" />
            <NavItem to="/accounts" icon={<CreditCard size={20} />} label="Accounts" />
            <NavItem to="/stock" icon={<Package size={20} />} label="Stock" />
            <NavItem to="/users" icon={<UsersIcon size={20} />} label="Users" />
            <NavItem to="/deposits" icon={<CreditCard size={20} />} label="Deposits" />
            <NavItem to="/settings" icon={<Settings size={20} />} label="Payment Settings" />
          </nav>
          <button
            onClick={handleLogout}
            className="mt-auto flex items-center space-x-3 p-3 text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <LogOut size={20} />
            <span>Logout</span>
          </button>
        </aside>

        {/* Top Header - Mobile Only */}
        <header className="md:hidden bg-gray-800 p-4 flex items-center justify-between shadow-lg sticky top-0 z-10">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            Admin Panel
          </h1>
          <button
            onClick={handleLogout}
            className="p-2 text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <LogOut size={20} />
          </button>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-10 bg-gradient-to-br from-gray-900 via-gray-900 to-black pb-20 md:pb-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/countries" element={<Countries />} />
            <Route path="/accounts" element={<Accounts />} />
            <Route path="/stock" element={<Stock />} />
            <Route path="/deposits" element={<Deposits />} />
            <Route path="/users" element={<Users />} />
            <Route path="/users/:id" element={<UserDetails />} />
            <Route path="/deposit/:id" element={<DepositDetail />} />
            <Route path="/settings" element={<PaymentSettings />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </main>


        {/* Bottom Navigation - Mobile Only */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 flex justify-around items-center py-2 px-1 z-20">
          <MobileNavItem to="/" icon={<LayoutDashboard size={20} />} label="Home" />
          <MobileNavItem to="/countries" icon={<Globe size={20} />} label="Countries" />
          <MobileNavItem to="/accounts" icon={<CreditCard size={20} />} label="Accounts" />
          <MobileNavItem to="/stock" icon={<Package size={20} />} label="Stock" />
          <MobileNavItem to="/users" icon={<UsersIcon size={20} />} label="Users" />
          <MobileNavItem to="/deposits" icon={<CreditCard size={20} />} label="Deposits" />
        </nav>
      </div>
    </Router>
  );
};

const NavItem = ({ to, icon, label }) => (
  <Link to={to} className="flex items-center space-x-3 p-3 hover:bg-gray-700 rounded-lg transition-colors">
    {icon}
    <span>{label}</span>
  </Link>
);


const MobileNavItem = ({ to, icon, label }) => (
  <Link to={to} className="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-blue-400 transition-colors py-1 px-2 min-w-0">
    <div className="flex items-center justify-center">{icon}</div>
    <span className="text-[9px] font-medium truncate max-w-full text-center">{label}</span>
  </Link>
);

export default App;
